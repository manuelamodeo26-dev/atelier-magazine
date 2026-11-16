import unittest
import xml.etree.ElementTree as ET

from generate_sitemap import BASE_URL, build_sitemap

NS = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}


class SitemapTests(unittest.TestCase):
    def test_contains_public_pages_and_article_detail_urls(self):
        xml = build_sitemap({
            "updated_at": "2026-11-16T19:07:49Z",
            "articles": [
                {"id": "https://example.com/story?a=1&b=2", "date": "2026-11-15T10:00:00Z"},
                {"id": "fashion story/uno", "date": "2026-11-14"},
            ],
        })
        root = ET.fromstring(xml)
        locs = [node.text for node in root.findall("sm:url/sm:loc", NS)]
        self.assertEqual(locs[:3], [
            BASE_URL,
            BASE_URL + "community.html",
            BASE_URL + "atelier-hub.html",
        ])
        self.assertIn(
            BASE_URL + "article.html?id=https%3A%2F%2Fexample.com%2Fstory%3Fa%3D1%26b%3D2",
            locs,
        )
        self.assertIn(BASE_URL + "article.html?id=fashion%20story%2Funo", locs)

    def test_deduplicates_article_ids_and_skips_empty_ids(self):
        xml = build_sitemap({
            "updated_at": "2026-11-16",
            "articles": [
                {"id": "same"},
                {"id": "same", "url": "https://example.com/duplicate"},
                {"id": ""},
                {},
            ],
        })
        root = ET.fromstring(xml)
        locs = [node.text for node in root.findall("sm:url/sm:loc", NS)]
        self.assertEqual(len(locs), 4)
        self.assertEqual(locs.count(BASE_URL + "article.html?id=same"), 1)

    def test_sitemap_xml_is_well_formed_and_uses_fallback_lastmod(self):
        root = ET.fromstring(build_sitemap({
            "updated_at": "2026-11-16T19:07:49Z",
            "articles": [{"id": "story"}],
        }))
        dates = [node.text for node in root.findall("sm:url/sm:lastmod", NS)]
        self.assertTrue(dates)
        self.assertTrue(all(value == "2026-11-16" for value in dates))


if __name__ == "__main__":
    unittest.main()
