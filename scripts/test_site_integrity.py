#!/usr/bin/env python3
"""Static integrity checks for ATELIER's GitHub Pages site."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]


class SiteParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.references = []
        self.ids = set()
        self.title_seen = False
        self.viewport_seen = False
        self.lang_seen = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if attrs.get("id"):
            value = attrs["id"]
            if value in self.ids:
                raise AssertionError("ID HTML duplicato: " + value)
            self.ids.add(value)
        if tag == "html":
            self.lang_seen = bool(attrs.get("lang"))
        if tag == "title":
            self.title_seen = True
        if tag == "meta" and attrs.get("name", "").lower() == "viewport":
            self.viewport_seen = True
        for key in ("src", "href"):
            value = attrs.get(key)
            if value:
                self.references.append(value)


def local_target(page, reference):
    parsed = urlsplit(reference.strip())
    if parsed.scheme or parsed.netloc or not parsed.path:
        return None
    path = unquote(parsed.path)
    if path.startswith("/"):
        target = ROOT / path.lstrip("/")
    else:
        target = page.parent / path
    target = target.resolve()
    if target.is_dir():
        target = target / "index.html"
    return target


def main():
    pages = sorted(ROOT.glob("*.html"))
    assert pages, "Nessuna pagina HTML trovata"
    checked = 0
    for page in pages:
        parser = SiteParser()
        parser.feed(page.read_text(encoding="utf-8"))
        assert parser.lang_seen, f"{page.name}: manca lang su html"
        assert parser.title_seen, f"{page.name}: manca il titolo"
        assert parser.viewport_seen, f"{page.name}: manca meta viewport"
        for reference in parser.references:
            target = local_target(page, reference)
            if target is None:
                continue
            assert target.is_file(), (
                f"{page.name}: riferimento locale non trovato: {reference}"
            )
            checked += 1
    home = (ROOT / "index.html").read_text(encoding="utf-8")
    app = (ROOT / "app.js").read_text(encoding="utf-8")
    assert 'id="maintenance-screen"' in home, "Homepage: schermata manutenzione assente"
    assert "data.archive_status!=='active'" in app, "Homepage: manca il blocco fail-closed"
    assert "setMaintenanceMode(true)" in app, "Homepage: la modalità manutenzione non viene applicata"
    print(f"Integrità sito OK: {len(pages)} pagine HTML, {checked} riferimenti locali verificati; manutenzione fail-closed verificata.")


if __name__ == "__main__":
    main()
