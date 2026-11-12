#!/usr/bin/env python3
"""Collect public RSS/Atom metadata for the ATELIER editorial archive."""
import html
from html.parser import HTMLParser
import json
import os
import re
import time
import io
import concurrent.futures
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import parse_qsl, quote, urlencode, urljoin, urlparse, urlunparse
from urllib.request import Request, urlopen
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "articles.json")
FEEDS = [
    ("https://www.vogue.it/feed/rss", "Fashion"),
    ("https://www.pambianconews.com/feed/", "Fashion"),
    ("https://www.ad-italia.it/feed/rss", "Design"),
    ("https://www.exibart.com/feed/", "Art & Culture"),
    ("https://www.finestresullarte.info/finestresullarte.xml", "Art & Culture"),
]
MAX_PER_FEED = 18
MAX_ARTICLES = 180
MAX_AGE_DAYS = 120
MAX_IMAGE_BYTES = 8 * 1024 * 1024
MIN_IMAGE_LONG_EDGE = 1000
MIN_IMAGE_SHORT_EDGE = 500
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
        return urlunparse((parsed.scheme, parsed.netloc.lower(), quote(parsed.path, safe="/%:@!$&'()*+,;=-._~"),
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


def upgrade_image_url(value):
    value = canonical_url(value)
    if not value:
        return ""
    try:
        parsed = urlparse(value)
        query = dict(parse_qsl(parsed.query, keep_blank_values=True))
        if "width" in query:
            query["width"] = "1600"
        if "w" in query:
            query["w"] = "1600"
        if "quality" in query:
            query["quality"] = "88"
        if "q" in query:
            query["q"] = "88"
        return urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params,
                           urlencode(query), ""))
    except (TypeError, ValueError):
        return value


class ImageMetaParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.image = ""
        self.description = ""
        self.author = ""

    def handle_starttag(self, tag, attrs):
        if tag.lower() != "meta" or self.image:
            return
        values = {key.lower(): value for key, value in attrs if key and value}
        key = (values.get("property") or values.get("name") or "").lower()
        content = values.get("content", "").strip()
        if key in ("og:image", "twitter:image") and not self.image:
            self.image = content
        elif key in ("og:description", "twitter:description", "description") and not self.description:
            self.description = content
        elif key in ("author", "article:author") and not self.author:
            self.author = content


def fetch_page_metadata(article_url):
    try:
        request = Request(article_url, headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml",
        })
        with urlopen(request, timeout=8) as response:
            parser = ImageMetaParser()
            parser.feed(response.read(350000).decode("utf-8", errors="replace"))
        return {
            "image": upgrade_image_url(urljoin(article_url, parser.image)),
            "description": clean(parser.description)[:1400],
            "author": clean(parser.author)[:160],
        }
    except Exception:
        return {"image": "", "description": "", "author": ""}


def verify_image(article):
    image_url = canonical_url(article.get("image"))
    if not image_url or not image_url.startswith("https://"):
        return {**article, "image": "", "image_verified": False}
    try:
        request = Request(image_url, headers={
            "User-Agent": USER_AGENT,
            "Referer": article.get("url", ""),
            "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
        })
        with urlopen(request, timeout=12) as response:
            content_type = response.headers.get("Content-Type", "").split(";", 1)[0].lower()
            if not content_type.startswith("image/"):
                raise ValueError("Il server non ha restituito un file immagine")
            raw = response.read(MAX_IMAGE_BYTES + 1)
        if len(raw) > MAX_IMAGE_BYTES:
            raise ValueError("Immagine troppo pesante")
        if len(raw) < 12000:
            raise ValueError("File immagine troppo piccolo")
        with Image.open(io.BytesIO(raw)) as picture:
            picture.verify()
        with Image.open(io.BytesIO(raw)) as picture:
            width, height = picture.size
            image_format = (picture.format or "").upper()
        if max(width, height) < MIN_IMAGE_LONG_EDGE or min(width, height) < MIN_IMAGE_SHORT_EDGE:
            raise ValueError(f"Risoluzione insufficiente: {width}x{height}")
        if image_format not in ("JPEG", "PNG", "WEBP"):
            raise ValueError(f"Formato non supportato: {image_format}")
        return {
            **article,
            "image": image_url,
            "image_verified": True,
            "image_width": width,
            "image_height": height,
            "image_format": image_format.lower(),
        }
    except Exception as exc:
        print(f"Foto scartata per verifica: {image_url} ({exc})")
        return {
            **article,
            "image": "",
            "image_verified": False,
            "image_width": 0,
            "image_height": 0,
            "image_format": "",
        }


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
                author = child_text(node, "creator", "author", "artist")
                articles.append({
                    "id": link,
                    "title": title[:300],
                    "excerpt": description[:1400],
                    "author": author[:160],
                    "category": category,
                    "source": host,
                    "date": article_date(node),
                    "url": link,
                    "image": upgrade_image_url(article_image(node)),
                    "image_verified": False,
                    "language": "it",
                })
            metadata_attempts = 0
            for article in articles:
                if (not article["image"] or not article["excerpt"] or not article["author"]) and metadata_attempts < 8:
                    metadata_attempts += 1
                    metadata = fetch_page_metadata(article["url"])
                    if not article["image"]:
                        article["image"] = metadata["image"]
                    if not article["excerpt"]:
                        article["excerpt"] = metadata["description"]
                    if not article["author"]:
                        article["author"] = metadata["author"]
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
        cutoff = datetime.now(timezone.utc) - timedelta(days=MAX_AGE_DAYS)
        for item in articles:
            if not isinstance(item, dict) or item.get("language") != "it":
                continue
            url = canonical_url(item.get("url"))
            if not url:
                continue
            try:
                published = datetime.fromisoformat((item.get("date") or "").replace("Z", "+00:00"))
                if published.tzinfo is None:
                    published = published.replace(tzinfo=timezone.utc)
                if published < cutoff:
                    continue
            except (TypeError, ValueError):
                continue
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
    cutoff = datetime.now(timezone.utc) - timedelta(days=MAX_AGE_DAYS)
    recent = []
    for item in merged.values():
        if item.get("language") != "it":
            continue
        try:
            published = datetime.fromisoformat((item.get("date") or "").replace("Z", "+00:00"))
            if published.tzinfo is None:
                published = published.replace(tzinfo=timezone.utc)
            if published < cutoff:
                continue
        except (TypeError, ValueError):
            continue
        recent.append(item)
    articles = sorted(recent,
                      key=lambda item: item.get("date") or "0000", reverse=True)[:MAX_ARTICLES]

    to_verify = [item for item in articles if item.get("image") and not item.get("image_verified")]
    if to_verify:
        print(f"Verifica fotografica: {len(to_verify)} immagini da controllare.")
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            checked = list(executor.map(verify_image, to_verify))
        checked_by_url = {item["url"]: item for item in checked}
        articles = [checked_by_url.get(item["url"], item) for item in articles]
        valid_images = sum(1 for item in articles if item.get("image_verified"))
        print(f"Fotografie verificate: {valid_images}/{len(articles)} articoli.")

    if articles == sorted(previous.values(),
                          key=lambda item: item.get("date") or "0000", reverse=True)[:MAX_ARTICLES]:
        print(f"Nessuna modifica: {len(articles)} articoli già archiviati.")
        return

    payload = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "feeds_ok": successful_feeds,
        "feeds_total": len(FEEDS),
        "language": "it",
        "image_verification": {
            "method": "HTTP, MIME, formato reale e risoluzione minima 1000x500",
            "verified_count": sum(1 for item in articles if item.get("image_verified")),
        },
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
