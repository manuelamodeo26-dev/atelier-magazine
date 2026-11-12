#!/usr/bin/env python3
"""Collect public RSS/Atom metadata for the ATELIER editorial archive."""
import html
import json
import os
import re
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse
from urllib.request import Request, urlopen

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "articles.json")
FEEDS = [
    ("https://www.theguardian.com/fashion/rss", "Fashion"),
    ("https://hypebeast.com/feed", "Streetwear"),
    ("https://www.wallpaper.com/feeds.xml", "Design"),
    ("https://www.dezeen.com/feed/", "Design"),
    ("https://www.designboom.com/architecture/feed/", "Architecture"),
    ("https://www.theguardian.com/artanddesign/rss", "Art & Culture"),
    ("https://www.itsnicethat.com/rss", "Art & Culture"),
    ("https://www.theguardian.com/technology/rss", "Technology"),
    ("https://www.theguardian.com/business/rss", "Business"),
    ("https://www.theguardian.com/lifeandstyle/rss", "Lifestyle"),
]
MAX_PER_FEED = 18
MAX_ARTICLES = 180
USER_AGENT = "ATELIER-Magazine/2.0 (+https://github.com/manuelamodeo26-dev/atelier-magazine)"
TRACKING_KEYS = {"fbclid", "gclid", "mc_cid", "mc_eid"}


def local_name(tag):
    return tag.rsplit("}", 1)[-1].lower()


def clean(value):
    value = html.unescape(re.sub(r"<[^>]*>", " ", value or ""))
    return re.sub(r"\s+", " ", value).strip()


def child(node, *names):
    wanted = {name.lower() for name in names}
    for item in list(node):
        if local_name(item.tag) in wanted:
            return item
    return None


def child_text(node, *names):
    item = child(node, *names)
    if item is None:
        return ""
    return clean(" ".join(part.strip() for part in item.itertext() if part.strip()))


def canonical_url(value):
    value = html.unescape((value or "").strip())
    try:
        parsed = urlparse(value)
        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            return ""
        query = [(key, val) for key, val in parse_qsl(parsed.query, keep_blank_values=True)
                 if not key.lower().startswith("utm_") and key.lower() not in TRACKING_KEYS]
        return urlunparse((parsed.scheme, parsed.netloc.lower(), parsed.path,
                           parsed.params, urlencode(query), ""))
    except (TypeError, ValueError):
        return ""


def article_link(node):
    links = [item for item in list(node) if local_name(item.tag) == "link"]
    for item in links:
        href = canonical_url(item.attrib.get("href") or item.text or "")
        if href and item.attrib.get("rel", "alternate").lower() == "alternate":
            return href
    for item in links:
        href = canonical_url(item.attrib.get("href") or item.text or "")
        if href:
            return href
    return ""


def article_image(node):
    for item in node.iter():
        name = local_name(item.tag)
        candidate = item.attrib.get("url") or item.attrib.get("href")
        if name in ("thumbnail", "content", "enclosure", "image") and candidate:
            image_url = canonical_url(candidate)
            media_type = item.attrib.get("type", "")
            if image_url and (name != "enclosure" or media_type.startswith("image/")):
                return image_url
    for item in node.iter():
        if local_name(item.tag) in ("description", "summary", "encoded", "content"):
            raw = "".join(item.itertext())
            match = re.search(r"""<img\b[^>]*\b(?:src|data-src)\s*=\s*["']([^"']+)""", raw, re.I)
            if match:
                image_url = canonical_url(match.group(1))
                if image_url:
                    return image_url
    return ""


def article_date(node):
    raw = child_text(node, "pubDate", "published", "updated", "date", "dateCreated")
    if not raw:
        return ""
    try:
        try:
            parsed = parsedate_to_datetime(raw)
        except (TypeError, ValueError):
            parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc).isoformat()
    except (TypeError, ValueError, OverflowError):
        return ""


def fetch(url):
    request = Request(url, headers={
        "User-Agent": USER_AGENT,
        "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml",
    })
    with urlopen(request, timeout=18) as response:
        return response.read()


def parse_feed(feed_url, category):
    for attempt in range(2):
        try:
            root = ET.fromstring(fetch(feed_url))
            nodes = [item for item in root.iter()
                     if local_name(item.tag) in ("item", "entry")]
            host = urlparse(feed_url).netloc.lower().removeprefix("www.")
            articles = []
            for node in nodes[:MAX_PER_FEED]:
                title = child_text(node, "title")
                link = article_link(node)
                if not title or not link:
                    continue
                description = child_text(node, "description", "summary", "encoded", "content")
                articles.append({
                    "id": link,
                    "title": title[:300],
                    "excerpt": description[:700],
                    "category": category,
                    "source": host,
                    "date": article_date(node),
                    "url": link,
                    "image": article_image(node),
                    "language": "en",
                })
            print(f"{host}: {len(articles)} articoli")
            return articles
        except Exception as exc:
            if attempt == 0:
                time.sleep(1.5)
            else:
                print(f"Feed non disponibile {feed_url}: {exc}")
    return []


def load_previous():
    try:
        with open(OUT, encoding="utf-8") as file:
            payload = json.load(file)
        articles = payload.get("articles", [])
        previous = {}
        for item in articles:
            if isinstance(item, dict):
                url = canonical_url(item.get("url"))
                if url:
                    previous[url] = item
        return previous
    except (OSError, ValueError, TypeError):
        return {}


def main():
    previous = load_previous()
    fresh = []
    successful_feeds = 0
    for feed_url, category in FEEDS:
        items = parse_feed(feed_url, category)
        if items:
            successful_feeds += 1
            fresh.extend(items)

    if not fresh:
        print("Nessun feed disponibile: archivio precedente preservato.")
        if not previous:
            raise SystemExit("Archivio vuoto e nessun feed valido: aggiornamento annullato.")
        return

    merged = dict(previous)
    for article in fresh:
        merged[article["url"]] = article
    articles = sorted(merged.values(),
                      key=lambda item: item.get("date") or "0000", reverse=True)[:MAX_ARTICLES]

    if articles == sorted(previous.values(),
                          key=lambda item: item.get("date") or "0000", reverse=True)[:MAX_ARTICLES]:
        print(f"Nessuna modifica: {len(articles)} articoli già archiviati.")
        return

    payload = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "feeds_ok": successful_feeds,
        "feeds_total": len(FEEDS),
        "articles": articles,
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    temporary = OUT + ".tmp"
    with open(temporary, "w", encoding="utf-8") as file:
        json.dump(payload, file, ensure_ascii=False, indent=2)
        file.write("\n")
    os.replace(temporary, OUT)
    print(f"Archivio aggiornato: {len(articles)} articoli da {successful_feeds}/{len(FEEDS)} feed.")


if __name__ == "__main__":
    main()
