import unittest

from fetch_news import infer_category, is_relevant


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
        ]
        for title, excerpt, current, expected in cases:
            with self.subTest(title=title):
                self.assertEqual(infer_category(title, excerpt, current), expected)


if __name__ == "__main__":
    unittest.main()
