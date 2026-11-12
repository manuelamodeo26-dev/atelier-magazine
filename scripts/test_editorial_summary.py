import json
import unittest
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError

import editorial_summary


class EditorialSummaryTests(unittest.TestCase):
    def test_falls_back_when_primary_model_is_overloaded(self):
        paragraphs = [" ".join(["moda"] * 60) for _ in range(3)]
        body = json.dumps({
            "candidates": [{
                "finishReason": "STOP",
                "content": {"parts": [{"text": json.dumps({
                    "level": "standard",
                    "paragraphs": paragraphs,
                })}]},
            }]
        }).encode("utf-8")
        response = MagicMock()
        response.__enter__.return_value.read.return_value = body

        with patch.object(editorial_summary, "API_KEY", "unit-test-key"), \
             patch.object(editorial_summary, "MODEL", "primary-test-model"), \
             patch.object(editorial_summary, "urlopen", side_effect=[
                 HTTPError("https://example.com", 503, "Unavailable", {}, None),
                 response,
             ]) as mocked:
            summary, level = editorial_summary.generate_editorial_summary(
                {"title": "Una nuova collezione", "excerpt": "Contesto editoriale " * 40,
                 "source": "Fonte di prova"},
                "Testo della fonte " * 100,
            )

        self.assertEqual(level, "standard")
        self.assertEqual(editorial_summary._word_count(summary), 180)
        self.assertEqual(mocked.call_count, 2)
        self.assertIn("gemini-3.7-flash", mocked.call_args_list[1].args[0].full_url)


if __name__ == "__main__":
    unittest.main()
