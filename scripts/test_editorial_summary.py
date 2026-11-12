import io
import json
import unittest
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError

import editorial_summary


class EditorialSummaryTests(unittest.TestCase):
    def _response(self, level="standard"):
        paragraphs = [" ".join(["moda"] * 80) for _ in range(4)]
        body = json.dumps({
            "candidates": [{
                "finishReason": "STOP",
                "content": {"parts": [{"text": json.dumps({
                    "level": level,
                    "paragraphs": paragraphs,
                })}]},
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

    def test_respects_retry_after_for_rate_limits(self):
        response = self._response()
        rate_limit = HTTPError(
            "https://example.com", 429, "Too Many Requests",
            {"Retry-After": "7"}, None,
        )

        with (
            patch.object(editorial_summary, "API_KEY", "unit-test-key"),
            patch.object(editorial_summary, "MODEL", "primary-test-model"),
            patch.object(editorial_summary, "urlopen", side_effect=[rate_limit, response]),
            patch.object(editorial_summary.time, "sleep") as sleep,
        ):
            summary, level = editorial_summary.generate_editorial_summary(
                self._article(), "Testo della fonte " * 100
            )

        self.assertEqual(level, "standard")
        self.assertEqual(editorial_summary._word_count(summary), 320)
        sleep.assert_called_once_with(7)


    def test_quota_exhaustion_skips_retry_and_uses_next_model(self):
        error_body = json.dumps({
            "error": {"message": "You exceeded your current quota", "status": "RESOURCE_EXHAUSTED"}
        }).encode("utf-8")
        quota_error = HTTPError(
            "https://example.com", 429, "Too Many Requests", {}, io.BytesIO(error_body)
        )
        response = self._response()
        with (
            patch.object(editorial_summary, "API_KEY", "unit-test-key"),
            patch.object(editorial_summary, "MODEL", "primary-test-model"),
            patch.object(editorial_summary, "urlopen", side_effect=[quota_error, response]) as mocked,
            patch.object(editorial_summary.time, "sleep") as sleep,
        ):
            summary, level = editorial_summary.generate_editorial_summary(
                self._article(), "Testo della fonte " * 100
            )
        self.assertEqual(level, "standard")
        self.assertEqual(editorial_summary._word_count(summary), 320)
        self.assertEqual(mocked.call_count, 2)
        self.assertIn("gemini-3.7-flash", mocked.call_args_list[1].args[0].full_url)
        sleep.assert_not_called()

    def test_reclassifies_short_in_depth_text_as_standard(self):
        response = self._response(level="approfondimento")
        with (
            patch.object(editorial_summary, "API_KEY", "unit-test-key"),
            patch.object(editorial_summary, "MODEL", "primary-test-model"),
            patch.object(editorial_summary, "urlopen", return_value=response),
        ):
            summary, level = editorial_summary.generate_editorial_summary(
                self._article(), "Testo della fonte " * 100
            )
        self.assertEqual(level, "standard")
        self.assertEqual(editorial_summary._word_count(summary), 320)

    def test_falls_back_when_primary_model_is_overloaded(self):
        response = self._response()

        with (
            patch.object(editorial_summary, "API_KEY", "unit-test-key"),
            patch.object(editorial_summary, "MODEL", "primary-test-model"),
            patch.object(editorial_summary, "urlopen", side_effect=[
                HTTPError("https://example.com", 503, "Unavailable", {}, None),
                response,
            ]) as mocked,
        ):
            summary, level = editorial_summary.generate_editorial_summary(
                self._article(), "Testo della fonte " * 100
            )

        self.assertEqual(level, "standard")
        self.assertEqual(editorial_summary._word_count(summary), 320)
        self.assertEqual(mocked.call_count, 2)
        self.assertIn("gemini-3.7-flash", mocked.call_args_list[1].args[0].full_url)


if __name__ == "__main__":
    unittest.main()
