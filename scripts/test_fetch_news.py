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

    def test_outpump_falls_back_to_google_news_when_publisher_feed_is_blocked(self):
        from urllib.error import HTTPError
        xml = b"""<rss><channel><item>
            <title>Outpump streetwear: nuova collezione</title>
            <link>https://news.google.com/rss/articles/OUTPUMP123</link>
            <description>Una nuova storia di moda e streetwear raccontata da Outpump.</description>
            <pubDate>Wed, 11 Nov 2026 10:00:00 GMT</pubDate>
        </item></channel></rss>"""
        with patch.object(fetch_news, "fetch", side_effect=[
            HTTPError("https://outpump.com/feed/", 403, "Forbidden", {}, None),
            HTTPError("https://outpump.com/feed/", 403, "Forbidden", {}, None),
            xml,
        ]) as mocked, patch.object(fetch_news.time, "sleep"):
            items, ok, error = fetch_news.parse_feed("https://outpump.com/feed/", "Streetwear")
        self.assertTrue(ok)
        self.assertEqual(error, "")
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["source"], "outpump.com")
        self.assertIn("news.google.com", items[0]["url"])
        self.assertEqual(mocked.call_count, 3)

    def test_summary_backfill_is_balanced_with_new_stories(self):
        selected = fetch_news.select_summary_candidates(
            ["new-1", "new-2", "new-3"],
            ["old-1", "old-2", "old-3"],
            2,
        )
        self.assertEqual(selected, ["new-1", "old-1"])

    def test_summary_backfill_uses_available_pool_when_one_side_is_empty(self):
        selected = fetch_news.select_summary_candidates([], ["old-1", "old-2"], 2)
        self.assertEqual(selected, ["old-1", "old-2"])

    def test_outpump_uses_browser_user_agent(self):
        with patch.object(fetch_news, "fetch", return_value=b"<rss><channel></channel></rss>") as mocked:
            items, ok, error = fetch_news.parse_feed("https://outpump.com/feed/", "Streetwear")
        self.assertEqual(items, [])
        self.assertTrue(ok)
        self.assertEqual(error, "")
        self.assertEqual(mocked.call_args.kwargs["user_agent"], fetch_news.BROWSER_USER_AGENT)

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
