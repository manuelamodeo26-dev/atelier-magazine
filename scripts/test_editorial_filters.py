import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

import fetch_news
from fetch_news import infer_category, is_relevant, source_category, summary_retry_due


class EditorialFilterTests(unittest.TestCase):
    def test_excludes_general_interest_feed_noise(self):
        samples = [
            {"title": "Oroscopo di oggi della Bilancia", "url": "https://example.com/oroscopo"},
            {"title": "Apnee del sonno: sintomi e rimedi", "url": "https://example.com/salute"},
            {"title": "Come smettere di guardare il telefono continuamente", "url": "https://example.com"},
            {"title": "Allergie mattutine e materiali in camera da letto", "url": "https://example.com"},
            {"title": "Destinazioni esotiche per l'inverno", "url": "https://example.com"},
        ]
        for article in samples:
            with self.subTest(title=article["title"]):
                self.assertFalse(is_relevant(article))

    def test_unrelated_excerpt_terms_do_not_exclude_a_story(self):
        self.assertTrue(is_relevant({
            "title": "La nuova collezione debutta a Milano",
            "excerpt": "Il testo cita dieta e sintomi soltanto come esempi secondari.",
        }))

    def test_failed_summary_has_a_retry_cooldown(self):
        now = datetime.now(timezone.utc)
        self.assertFalse(summary_retry_due({
            "editorial_retry_after": (now.replace(microsecond=0)).isoformat()
        }, now=now.replace(microsecond=0) - __import__("datetime").timedelta(seconds=1)))
        self.assertTrue(summary_retry_due({
            "editorial_retry_after": (now - __import__("datetime").timedelta(seconds=1)).isoformat()
        }, now=now))

    def test_legacy_archive_is_cleaned_and_saved(self):
        original_path = fetch_news.OUT
        with tempfile.TemporaryDirectory() as directory:
            archive_path = Path(directory) / "articles.json"
            fetch_news.OUT = str(archive_path)
            today = datetime.now(timezone.utc).isoformat()
            archive_path.write_text(json.dumps({
                "articles": [
                    {"id": "https://example.com/fashion", "url": "https://example.com/fashion",
                     "title": "La nuova collezione", "excerpt": "Una notizia di moda.",
                     "source": "vogue.it", "category": "Fashion", "language": "it", "date": today},
                    {"id": "https://example.com/oroscopo", "url": "https://example.com/oroscopo",
                     "title": "Oroscopo della settimana", "excerpt": "Previsioni astrologiche.",
                     "source": "vogue.it", "category": "Fashion", "language": "it", "date": today},
                ]
            }), encoding="utf-8")
            try:
                previous = fetch_news.load_previous()
                saved = json.loads(archive_path.read_text(encoding="utf-8"))
                self.assertEqual(len(previous), 1)
                self.assertEqual(len(saved["articles"]), 1)
                self.assertEqual(saved["articles"][0]["title"], "La nuova collezione")
            finally:
                fetch_news.OUT = original_path

    def test_keeps_editorial_topics(self):
        samples = [
            {"title": "La nuova collezione debutta a Milano"},
            {"title": "Una mostra di fotografia contemporanea"},
            {"title": "Un progetto di architettura nel centro storico"},
            {"title": "Il design dei nuovi oggetti in ceramica"},
        ]
        for article in samples:
            with self.subTest(title=article["title"]):
                self.assertTrue(is_relevant(article))

    def test_restores_feed_base_category(self):
        self.assertEqual(source_category({"source": "exibart.com", "category": "Technology"}), "Art & Culture")
        self.assertEqual(source_category({"source": "ad-italia.it", "category": "Architecture"}), "Design")
        self.assertEqual(source_category({"source": "pambianconews.com", "category": "Business"}), "Fashion")

    def test_classifies_editorial_sections(self):
        cases = [
            ("Sneakers e streetwear", "", "Fashion", "Streetwear"),
            ("Golden Goose: oltre 200 mln nel Q3", "", "Fashion", "Business"),
            ("Una villa di architettura contemporanea", "", "Design", "Architecture"),
            ("L'intelligenza artificiale nel progetto creativo", "", "Fashion", "Technology"),
            ("Il nuovo design degli oggetti", "", "Fashion", "Design"),
            ("Una mostra di fotografia", "", "Fashion", "Art & Culture"),
            ("Gli anelli del potere: storia e significato", "Un approfondimento con parole AI e ai materiali", "Fashion", "Fashion"),
            ("A Milano si apre il cantiere del futuro Museo nazionale", "Un progetto di tecnologia e cultura", "Art & Culture", "Art & Culture"),
            ("Come abbinare cappotto midi e décolleté", "Un racconto di street style e moda", "Fashion", "Fashion"),
            ("The game is NOT HER: il progetto di Elena Bellantoni", "Investimenti e retail nel sistema dell'arte", "Art & Culture", "Art & Culture"),
        ]
        for title, excerpt, current, expected in cases:
            with self.subTest(title=title):
                self.assertEqual(infer_category(title, excerpt, current), expected)


if __name__ == "__main__":
    unittest.main()
