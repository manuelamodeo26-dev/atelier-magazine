import io
import json
import unittest
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError

import editorial_summary


class EditorialSummaryTests(unittest.TestCase):
    def setUp(self):
        editorial_summary.QUOTA_EXHAUSTED_FOR_RUN = False
        editorial_summary.AI_PROVIDER_UNAVAILABLE_FOR_RUN = False

    def _response(self, level="standard"):
        count = 4 if level == "approfondimento" else 3
        paragraphs = [" ".join(["moda"] * 90) for _ in range(count)]
        body = json.dumps({
            "choices": [{
                "finish_reason": "stop",
                "message": {"content": json.dumps({
                    "level": level,
                    "paragraphs": paragraphs,
                })},
            }]
        }).encode("utf-8")
        response = MagicMock()
        response.__enter__.return_value.read.return_value = body
        return response

    def _gemini_response(self, level="standard"):
        count = 4 if level == "approfondimento" else 3
        paragraphs = [" ".join(["moda"] * 90) for _ in range(count)]
        body = json.dumps({
            "candidates": [{
                "content": {"parts": [{"text": json.dumps({
                    "level": level,
                    "paragraphs": paragraphs,
                })}]}
            }]
        }).encode("utf-8")
        response = MagicMock()
        response.__enter__.return_value.read.return_value = body
        return response

    def _article(self):
        return {
            "title": "Una nuova collezione",
            "excerpt": "Contesto editoriale " * 40,
            "source": "Fonte di prova",
        }

    def test_summary_format_validator_accepts_only_complete_editorial_summaries(self):
        valid = "\n\n".join([" ".join(["moda"] * 70) for _ in range(4)])
        self.assertTrue(editorial_summary.is_valid_editorial_summary(valid, "standard"))
        short = "\n\n".join([" ".join(["moda"] * 50) for _ in range(3)])
        self.assertFalse(editorial_summary.is_valid_editorial_summary(short, "standard"))
        invalid = "\n\n".join([" ".join(["moda"] * 50) for _ in range(1)])
        self.assertFalse(editorial_summary.is_valid_editorial_summary(invalid, "standard"))
        self.assertFalse(editorial_summary.is_valid_editorial_summary(valid, "unknown"))
        self.assertFalse(editorial_summary.is_valid_editorial_summary(valid, "approfondimento"))
        too_long = "\n\n".join([" ".join(["moda"] * 80) for _ in range(4)])
        self.assertFalse(editorial_summary.is_valid_editorial_summary(too_long, "standard"))
        valid_deep = "\n\n".join([" ".join(["moda"] * 90) for _ in range(4)])
        self.assertTrue(editorial_summary.is_valid_editorial_summary(valid_deep, "approfondimento"))

    def test_uses_groq_chat_completions_and_json_mode(self):
        response = self._response()
        with (
            patch.object(editorial_summary, "API_KEY", "unit-test-key"),
            patch.object(editorial_summary, "MODEL", "openai/gpt-oss-120b"),
            patch.object(editorial_summary, "urlopen", return_value=response) as mocked,
        ):
            summary, level = editorial_summary.generate_editorial_summary(
                self._article(), "Testo della fonte " * 100
            )
        self.assertEqual(level, "standard")
        self.assertEqual(editorial_summary._word_count(summary), 270)
        request = mocked.call_args.args[0]
        self.assertEqual(request.full_url, "https://api.groq.com/openai/v1/chat/completions")
        self.assertEqual(request.get_header("Authorization"), "Bearer unit-test-key")
        payload = json.loads(request.data.decode("utf-8"))
        self.assertEqual(payload["model"], "openai/gpt-oss-120b")
        self.assertEqual(payload["response_format"], {"type": "json_object"})

    def test_respects_retry_after_for_rate_limits(self):
        response = self._response()
        rate_limit = HTTPError(
            "https://api.groq.com", 429, "Too Many Requests",
            {"Retry-After": "7"}, None,
        )
        with (
            patch.object(editorial_summary, "API_KEY", "unit-test-key"),
            patch.object(editorial_summary, "MODEL", "openai/gpt-oss-120b"),
            patch.object(editorial_summary, "urlopen", side_effect=[rate_limit, response]),
            patch.object(editorial_summary.time, "sleep") as sleep,
        ):
            summary, level = editorial_summary.generate_editorial_summary(
                self._article(), "Testo della fonte " * 100
            )
        self.assertEqual(level, "standard")
        self.assertEqual(editorial_summary._word_count(summary), 270)
        sleep.assert_called_once_with(7)

    def test_falls_back_to_smaller_model_on_quota_exhaustion(self):
        error_body = json.dumps({
            "error": {"message": "Rate limit reached for requests per day", "type": "requests"}
        }).encode("utf-8")
        quota_error = HTTPError(
            "https://api.groq.com", 429, "Too Many Requests", {}, io.BytesIO(error_body)
        )
        response = self._response()
        with (
            patch.object(editorial_summary, "API_KEY", "unit-test-key"),
            patch.object(editorial_summary, "MODEL", "openai/gpt-oss-120b"),
            patch.object(editorial_summary, "urlopen", side_effect=[quota_error, response]) as mocked,
            patch.object(editorial_summary.time, "sleep") as sleep,
        ):
            summary, level = editorial_summary.generate_editorial_summary(
                self._article(), "Testo della fonte " * 100
            )
        self.assertEqual(level, "standard")
        self.assertEqual(editorial_summary._word_count(summary), 270)
        self.assertEqual(mocked.call_count, 2)
        second_payload = json.loads(mocked.call_args_list[1].args[0].data.decode("utf-8"))
        self.assertEqual(second_payload["model"], "openai/gpt-oss-20b")
        sleep.assert_not_called()

    def test_keeps_short_in_depth_text_with_its_editorial_level(self):
        response = self._response(level="approfondimento")
        with (
            patch.object(editorial_summary, "API_KEY", "unit-test-key"),
            patch.object(editorial_summary, "MODEL", "openai/gpt-oss-120b"),
            patch.object(editorial_summary, "urlopen", return_value=response),
        ):
            summary, level = editorial_summary.generate_editorial_summary(
                self._article(), "Testo della fonte " * 100
            )
        self.assertEqual(level, "approfondimento")
        self.assertEqual(editorial_summary._word_count(summary), 360)

    def test_falls_back_to_gemini_when_both_groq_models_exhaust_quota(self):
        def quota_error():
            error_body = json.dumps({
                "error": {"message": "Rate limit reached for requests per day", "type": "requests"}
            }).encode("utf-8")
            return HTTPError(
                "https://api.groq.com", 429, "Too Many Requests", {}, io.BytesIO(error_body)
            )
        gemini_response = self._gemini_response()
        with (
            patch.object(editorial_summary, "API_KEY", "groq-unit-test-key"),
            patch.object(editorial_summary, "GEMINI_API_KEY", "gemini-unit-test-key"),
            patch.object(editorial_summary, "MODEL", "openai/gpt-oss-120b"),
            patch.object(editorial_summary, "QUOTA_EXHAUSTED_FOR_RUN", False),
            patch.object(editorial_summary, "urlopen", side_effect=[
                quota_error(), quota_error(), gemini_response
            ]) as mocked,
        ):
            summary, level = editorial_summary.generate_editorial_summary(
                self._article(), "Testo della fonte " * 100
            )
        self.assertEqual(level, "standard")
        self.assertEqual(editorial_summary._word_count(summary), 270)
        self.assertEqual(mocked.call_count, 3)
        gemini_request = mocked.call_args_list[2].args[0]
        self.assertIn("gemini-3.8-flash:generateContent", gemini_request.full_url)
        self.assertEqual(gemini_request.get_header("X-goog-api-key"), "gemini-unit-test-key")
        self.assertFalse(editorial_summary.QUOTA_EXHAUSTED_FOR_RUN)

    def test_retries_gemini_after_a_transient_timeout(self):
        response = self._gemini_response()
        with (
            patch.object(editorial_summary, "API_KEY", ""),
            patch.object(editorial_summary, "GEMINI_API_KEY", "gemini-unit-test-key"),
            patch.object(editorial_summary, "QUOTA_EXHAUSTED_FOR_RUN", False),
            patch.object(editorial_summary, "urlopen", side_effect=[TimeoutError(), response]) as mocked,
            patch.object(editorial_summary.time, "sleep") as sleep,
        ):
            summary, level = editorial_summary.generate_editorial_summary(
                self._article(), "Testo della fonte " * 100
            )
        self.assertEqual(level, "standard")
        self.assertEqual(editorial_summary._word_count(summary), 270)
        self.assertEqual(mocked.call_count, 2)
        self.assertEqual(mocked.call_args_list[0].kwargs["timeout"], 120)
        sleep.assert_called_once_with(5)

    def test_stops_repeating_gemini_after_repeated_transient_failures(self):
        with (
            patch.object(editorial_summary, "API_KEY", ""),
            patch.object(editorial_summary, "GEMINI_API_KEY", "gemini-unit-test-key"),
            patch.object(editorial_summary, "QUOTA_EXHAUSTED_FOR_RUN", False),
            patch.object(editorial_summary, "AI_PROVIDER_UNAVAILABLE_FOR_RUN", False),
            patch.object(editorial_summary, "urlopen", side_effect=[TimeoutError(), TimeoutError()]) as mocked,
            patch.object(editorial_summary.time, "sleep"),
        ):
            first = editorial_summary.generate_editorial_summary(
                self._article(), "Testo della fonte " * 100
            )
            second = editorial_summary.generate_editorial_summary(
                self._article(), "Altro testo della fonte " * 100
            )
        self.assertEqual(first, ("", ""))
        self.assertEqual(second, ("", ""))
        self.assertEqual(mocked.call_count, 2)
        self.assertTrue(editorial_summary.AI_PROVIDER_UNAVAILABLE_FOR_RUN)

    def test_groq_quota_and_gemini_timeout_do_not_trigger_daily_cooldown(self):
        def quota_error():
            error_body = json.dumps({
                "error": {"message": "Rate limit reached for requests per day", "type": "requests"}
            }).encode("utf-8")
            return HTTPError(
                "https://api.groq.com", 429, "Too Many Requests", {}, io.BytesIO(error_body)
            )
        with (
            patch.object(editorial_summary, "API_KEY", "groq-unit-test-key"),
            patch.object(editorial_summary, "GEMINI_API_KEY", "gemini-unit-test-key"),
            patch.object(editorial_summary, "MODEL", "openai/gpt-oss-120b"),
            patch.object(editorial_summary, "QUOTA_EXHAUSTED_FOR_RUN", False),
            patch.object(editorial_summary, "urlopen", side_effect=[
                quota_error(), quota_error(), TimeoutError(), TimeoutError()
            ]),
            patch.object(editorial_summary.time, "sleep"),
        ):
            result = editorial_summary.generate_editorial_summary(
                self._article(), "Testo della fonte " * 100
            )
        self.assertEqual(result, ("", ""))
        self.assertFalse(editorial_summary.QUOTA_EXHAUSTED_FOR_RUN)

    def test_uses_gemini_when_groq_key_is_not_configured(self):
        response = self._gemini_response()
        with (
            patch.object(editorial_summary, "API_KEY", ""),
            patch.object(editorial_summary, "GEMINI_API_KEY", "gemini-unit-test-key"),
            patch.object(editorial_summary, "QUOTA_EXHAUSTED_FOR_RUN", False),
            patch.object(editorial_summary, "urlopen", return_value=response) as mocked,
        ):
            summary, level = editorial_summary.generate_editorial_summary(
                self._article(), "Testo della fonte " * 100
            )
        self.assertEqual(level, "standard")
        self.assertEqual(mocked.call_count, 1)

    def test_quota_exhaustion_stops_repeated_requests_for_the_run(self):
        error_body = json.dumps({
            "error": {"message": "Rate limit reached for requests per day", "type": "requests"}
        }).encode("utf-8")
        errors = [
            HTTPError(
                "https://api.groq.com", 429, "Too Many Requests", {},
                io.BytesIO(error_body),
            )
            for _ in range(2)
        ]
        with (
            patch.object(editorial_summary, "API_KEY", "unit-test-key"),
            patch.object(editorial_summary, "MODEL", "openai/gpt-oss-120b"),
            patch.object(editorial_summary, "QUOTA_EXHAUSTED_FOR_RUN", False),
            patch.object(editorial_summary, "urlopen", side_effect=errors) as mocked,
        ):
            first = editorial_summary.generate_editorial_summary(
                self._article(), "Testo della fonte " * 100
            )
            second = editorial_summary.generate_editorial_summary(
                self._article(), "Altro testo della fonte " * 100
            )
        self.assertEqual(first, ("", ""))
        self.assertEqual(second, ("", ""))
        self.assertEqual(mocked.call_count, 2)


if __name__ == "__main__":
    unittest.main()
