#!/usr/bin/env python3
"""Import public RSS/Atom metadata into the ATELIER article archive."""
import html
import json
import os
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import urlparse
from urllib.request import Request, urlopen

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "articles.json")
FEEDS = [
    ("https://www.vogue.com/feed/rss", "Fashion"),
    ("https://www.businessoffashion.com/feed/", "Fashion"),
    ("https://www.dezeen.com/feed/", "Design"),
    ("https://www.designboom.com/design/feed/", "Design"),
    ("https://www.itsnicethat.com/rss", "Art & Culture"),
    ("https://hypebeast.com/feed", "Streetwear"),
    ("https://techcrunch.com/category/design/feed/", "Technology"),
]
MAX_PER_FEED = 15
MAX_ARTICLES = 100
USER_AGENT = "ATELIER-Magazine-RSS/1.1 (+https://github.com/manuelamodeo26-dev/atelier-magazine)"


def local_name(tag):
    return tag.rsplit("}", 1)[-1].lower()


def child_text(node, *names):
    wanted = {name.lower() for name in names}
    for child in list(node):
        if local_name(child.tag) in wanted:
            value = " ".join(part.strip() for part in child.itertext() if part.strip())
            if value:
                return clean(value)
    return ""


def clean(value):
    value = html.unescape(re.sub(r"<[^>]*>", " ", value or ""))
    return re.sub(r"\s+", " ", value).strip()


def valid_url(value):
    value = html.unescape((value or "").strip())
    try:
        parsed = urlparse(value)
        return value if parsed.scheme in ("http", "https") and parsed.netloc else ""
    except ValueError:
        return ""


def article_link(node):
    for child in list(node):
        if local_name(child.tag) == "link":
            href = child.attrib.get("href")
            if href:
                return valid_url(href)
            if child.text:
                return valid_url(child.text)
    return ""


def article_image(node, description):
    for element in node.iter():
        name = local_name(element.tag)
        if name in ("thumbnail", "content", "enclosure"):
            candidate = element.attrib.get("url") or element.attrib.get("href")
            candidate = valid_url(candidate)
            if candidate and (name != "enclosure" or element.attrib.get("type", "").startswith("image/")):
                return candidate
    match = re.search(r"""<img\b[^>]*\bsrc\s*=\s*["']([^"']+)""", description or "", re.I)
    return valid_url(match.group(1)) if match else ""


def article_date(node):
    raw = child_text(node, "pubDate", "published", "updated", "date")
    if raw:
        try:
            try:
                parsed = parsedate_to_datetime(raw)
            except (TypeError, ValueError):
                parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed.astimezone(timezone.utc).isoformat()
        except (TypeError, ValueError, OverflowError):
            pass
    return ""


def fetch(url):
    request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml"})
    with urlopen(request, timeout=20) as response:
        return response.read()


def parse_feed(feed_url, category):
    try:
        root = ET.fromstring(fetch(feed_url))
        nodes = [node for node in root.iter() if local_name(node.tag) in ("item", "entry")]
        articles = []
        for node in nodes[:MAX_PER_FEED]:
            title = child_text(node, "title")
            link = article_link(node)
            description = child_text(node, "description", "summary", "content", "encoded")
            if not title or not link:
                continue
            host = urlparse(feed_url).netloc.lower().removeprefix("www.")
            articles.append({
                "title": title[:300],
                "excerpt": description[:500],
                "category": category,
                "source": host,
                "date": article_date(node),
                "url": link,
                "image": article_image(node, description),
            })
        print(f"{host if 'host' in locals() else feed_url}: {len(articles)} articoli")
        return articles
    except Exception as exc:
        print(f"Feed non disponibile {feed_url}: {exc}")
        return []


def main():
    old = {}
    if os.path.exists(OUT):
        try:
            with open(OUT, encoding="utf-8") as file:
                previous = json.load(file)
            for article in previous.get("articles", []):
                url = valid_url(article.get("url"))
                if url:
                    old[url] = article
        except (OSError, ValueError, TypeError) as exc:
            print(f"Archivio precedente non leggibile: {exc}")

    fresh = []
    for feed_url, category in FEEDS:
        fresh.extend(parse_feed(feed_url, category))

    merged = dict(old)
    for article in fresh:
        merged[article["url"]] = article

    articles = list(merged.values())
    articles.sort(key=lambda item: item.get("date") or "", reverse=True)
    payload = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "articles": articles[:MAX_ARTICLES],
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    temporary = OUT + ".tmp"
    with open(temporary, "w", encoding="utf-8") as file:
        json.dump(payload, file, ensure_ascii=False, indent=2)
        file.write("\n")
    os.replace(temporary, OUT)
    print(f"Archivio aggiornato: {len(payload['articles'])} articoli; {len(fresh)} nuovi/aggiornati.")


if __name__ == "__main__":
    main()
