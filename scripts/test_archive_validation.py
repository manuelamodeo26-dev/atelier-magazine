import unittest

from validate_archive import validate_payload


class ArchiveValidationTests(unittest.TestCase):
    def article(self):
        return {
            "id": "https://example.com/story",
            "title": "Una notizia di moda",
            "url": "https://example.com/story",
            "date": "2026-11-12T10:00:00+00:00",
            "category": "Fashion",
            "source": "example.com",
            "language": "it",
            "image_verified": False,
        }

    def payload(self):
        return {"feeds_ok": 7, "feeds_total": 7, "articles": [self.article()]}

    def test_accepts_valid_archive(self):
        errors, warnings = validate_payload(self.payload())
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

    def test_rejects_duplicate_urls(self):
        payload = self.payload()
        payload['articles'].append(self.article())
        errors, _ = validate_payload(payload)
        self.assertTrue(any("duplicato" in error for error in errors))

    def test_warns_when_a_feed_is_unavailable(self):
        payload = self.payload()
        payload['feeds_ok'] = 6
        _, warnings = validate_payload(payload)
        self.assertTrue(any("6/7" in warning for warning in warnings))

    def test_rejects_summary_with_too_few_paragraphs(self):
        payload = self.payload()
        payload["articles"][0]["editorial_summary"] = "\\n\\n".join([" ".join(["moda"] * 110) for _ in range(3)])
        payload["articles"][0]["editorial_level"] = "standard"
        errors, _ = validate_payload(payload)
        self.assertTrue(any("sintesi editoriale fuori standard" in error for error in errors))

    def test_rejects_unverified_dimensions_marked_as_verified(self):
        payload = self.payload()
        payload["articles"][0].update({"image_verified": True, "image": "https://example.com/photo.jpg", "image_width": 600, "image_height": 300, "image_format": "jpeg"})
        errors, _ = validate_payload(payload)
        self.assertTrue(any("larghezza immagine" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
