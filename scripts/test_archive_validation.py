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

    def test_accepts_empty_archive_only_in_maintenance(self):
        payload = {
            "archive_status": "maintenance", "feeds_ok": 0, "feeds_total": 0,
            "feed_status": [], "image_verification": {"method": "test", "verified_count": 0},
            "articles": [],
        }
        errors, warnings = validate_payload(payload)
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

    def test_accepts_archived_articles_while_publication_gate_is_closed(self):
        payload = {
            "archive_status": "maintenance",
            "feeds_ok": 7,
            "feeds_total": 7,
            "feed_status": [
                {"source": "feed{}.example".format(index), "ok": True, "articles": 1}
                for index in range(7)
            ],
            "image_verification": {"method": "test", "verified_count": 0},
            "articles": [self.article()],
        }
        errors, warnings = validate_payload(payload)
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

    def test_accepts_empty_archive_for_clean_public_launch(self):
        payload = {"archive_status": "active", "feeds_ok": 7, "feeds_total": 7, "feed_status": [
            {"source": "one.example", "ok": True, "articles": 1},
            {"source": "two.example", "ok": True, "articles": 1},
            {"source": "three.example", "ok": True, "articles": 1},
            {"source": "four.example", "ok": True, "articles": 1},
            {"source": "five.example", "ok": True, "articles": 1},
            {"source": "six.example", "ok": True, "articles": 1},
            {"source": "seven.example", "ok": True, "articles": 1},
        ], "articles": []}
        errors, warnings = validate_payload(payload)
        self.assertEqual(errors, [])
        self.assertTrue(any("Archivio editoriale vuoto" in warning for warning in warnings))

    def test_rejects_incomplete_feed_diagnostics(self):
        payload = self.payload()
        payload["feed_status"] = [{"source": "example.com", "ok": True, "articles": 1}]
        errors, _ = validate_payload(payload)
        self.assertTrue(any("numero di fonti" in error for error in errors))

    def test_accepts_complete_feed_diagnostics(self):
        payload = self.payload()
        payload["feed_status"] = [{"source": "one.example", "ok": True, "articles": 2}, {"source": "two.example", "ok": False, "articles": 0}, {"source": "three.example", "ok": True, "articles": 1}, {"source": "four.example", "ok": True, "articles": 3}, {"source": "five.example", "ok": True, "articles": 4}, {"source": "six.example", "ok": True, "articles": 1}, {"source": "seven.example", "ok": True, "articles": 2}]
        errors, _ = validate_payload(payload)
        self.assertEqual(errors, [])

    def test_rejects_stale_verified_image_count(self):
        payload = self.payload()
        payload["image_verification"] = {"method": "test", "verified_count": 1}
        errors, _ = validate_payload(payload)
        self.assertTrue(any("Conteggio immagini verificate" in error for error in errors))

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
        payload["articles"][0]["editorial_summary"] = "\n\n".join([" ".join(["moda"] * 110) for _ in range(3)])
        payload["articles"][0]["editorial_level"] = "standard"
        errors, _ = validate_payload(payload)
        self.assertTrue(any("sintesi editoriale fuori standard" in error for error in errors))

    def test_accepts_portrait_images_with_minimum_short_and_long_edges(self):
        payload = self.payload()
        payload["articles"][0].update({"image_verified": True, "image": "https://example.com/photo.jpg", "image_width": 683, "image_height": 1024, "image_format": "jpeg"})
        errors, _ = validate_payload(payload)
        self.assertEqual(errors, [])

    def test_rejects_unverified_dimensions_marked_as_verified(self):
        payload = self.payload()
        payload["articles"][0].update({"image_verified": True, "image": "https://example.com/photo.jpg", "image_width": 300, "image_height": 1100, "image_format": "jpeg"})
        errors, _ = validate_payload(payload)
        self.assertTrue(any("risoluzione immagine" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
