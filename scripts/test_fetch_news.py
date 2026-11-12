import unittest
from unittest.mock import patch

import fetch_news


class FeedStatusTests(unittest.TestCase):
    def test_valid_feed_with_no_matching_stories_is_still_healthy(self):
        with patch.object(fetch_news, "fetch", return_value=b"<rss><channel></channel></rss>"):
            items, ok, error = fetch_news.parse_feed("https://example.com/feed", "Fashion")
        self.assertEqual(items, [])
        self.assertTrue(ok)
        self.assertEqual(error, "")

    def test_unavailable_feed_is_reported_as_failed(self):
        with patch.object(fetch_news, "fetch", side_effect=ValueError("invalid feed")), patch.object(fetch_news.time, "sleep"):
            items, ok, error = fetch_news.parse_feed("https://example.com/feed", "Fashion")
        self.assertEqual(items, [])
        self.assertFalse(ok)
        self.assertIn("ValueError", error)

    def test_valid_feed_with_story_returns_items_and_healthy_status(self):
        description = "Dettagli sulla nuova collezione e sul lavoro creativo. " * 25
        xml = (
            "<rss><channel><item>"
            "<title>Una nuova collezione di moda</title>"
            "<link>https://example.com/story</link>"
            "<description><![CDATA[" + description + "]]></description>"
            "<author>Redazione</author>"
            "<pubDate>Wed, 12 Nov 2026 10:00:00 GMT</pubDate>"
            "<enclosure url='https://example.com/image.jpg' type='image/jpeg'/>"
            "</item></channel></rss>"
        ).encode("utf-8")
        with patch.object(fetch_news, "fetch", return_value=xml):
            items, ok, error = fetch_news.parse_feed("https://example.com/feed", "Fashion")
        self.assertTrue(ok)
        self.assertEqual(error, "")
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["url"], "https://example.com/story")


if __name__ == "__main__":
    unittest.main()
