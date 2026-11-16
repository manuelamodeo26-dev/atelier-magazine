#!/usr/bin/env python3
"""Generate the ATELIER XML sitemap from the current editorial archive."""
from __future__ import annotations

import argparse
import html
import json
import re
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE_PATH = ROOT / "data" / "articles.json"
SITEMAP_PATH = ROOT / "sitemap.xml"
BASE_URL = "https://manuelamodeo26-dev.github.io/atelier-magazine/"
STATIC_PATHS = ("", "community.html", "atelier-hub.html")


def valid_date(value: object) -> str:
    match = re.match(r"^(\d{4}-\d{2}-\d{2})", str(value or ""))
    return match.group(1) if match else ""


def build_sitemap(archive: dict) -> str:
    """Return deterministic XML containing public pages and every article URL."""
    fallback_date = valid_date(archive.get("updated_at"))
    entries: list[tuple[str, str]] = [
        (BASE_URL + path, fallback_date) for path in STATIC_PATHS
    ]
    seen: set[str] = set()

    for article in archive.get("articles", []):
        if not isinstance(article, dict):
            continue
        article_id = str(article.get("id") or article.get("url") or "").strip()
        if not article_id or article_id in seen:
            continue
        seen.add(article_id)
        encoded_id = quote(article_id, safe="~!*'()-._")
        loc = BASE_URL + "article.html?id=" + encoded_id
        lastmod = valid_date(article.get("date")) or fallback_date
        entries.append((loc, lastmod))

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    for loc, lastmod in entries:
        lines.extend(("  <url>", f"    <loc>{html.escape(loc, quote=True)}</loc>"))
        if lastmod:
            lines.append(f"    <lastmod>{lastmod}</lastmod>")
        lines.append("  </url>")
    lines.append("</urlset>")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true",
                        help="fail if sitemap.xml is not up to date")
    args = parser.parse_args()
    archive = json.loads(ARCHIVE_PATH.read_text(encoding="utf-8"))
    generated = build_sitemap(archive)
    if args.check:
        current = SITEMAP_PATH.read_text(encoding="utf-8") if SITEMAP_PATH.exists() else ""
        if current != generated:
            print("Sitemap non aggiornato: esegui python scripts/generate_sitemap.py")
            return 1
        print("Sitemap valido e sincronizzato con l'archivio.")
        return 0
    SITEMAP_PATH.write_text(generated, encoding="utf-8")
    print(f"Sitemap generato: {generated.count('<url>')} URL pubblici.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
