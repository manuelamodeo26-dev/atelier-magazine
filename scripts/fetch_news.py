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
from editorial_summary import fetch_article_text, generate_editorial_summary, is_valid_editorial_summary

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "articles.json")
FEEDS = [
    ("https://www.vogue.it/feed/rss", "Fashion"),
    ("https://www.pambianconews.com/feed/", "Fashion"),
    ("https://www.ad-italia.it/feed/rss", "Design"),
    ("https://www.exibart.com/feed/", "Art & Culture"),
    ("https://www.finestresullarte.info/finestresullarte.xml", "Art & Culture"),
    ("https://outpump.com/feed/", "Streetwear"),
    ("https://www.sneakersmagazine.it/feed/", "Streetwear"),
]
MAX_PER_FEED = 18
MAX_ARTICLES = 180
MAX_AGE_DAYS = 120
MAX_SUMMARIES_PER_RUN = 6
MAX_IMAGE_BACKFILLS_PER_RUN = 10

# Keep the archive focused on fashion, design and contemporary culture.
# Exclude recurring general-interest formats that broad publisher feeds can contain.
EXCLUDED_CONTENT = re.compile(
    r"oroscop|segno zodiacale|zodiac|horoscope|apnee? del sonno|sleep apnea|"
    r"come smettere di guardare il telefono|telefono continuamente|"
    r"abitudini facili|dieta|dimagr|ricett[ae]|cucin[ae]|sintomi|"
    r"farmac[io]|integrator[ei]|consigli per dormire|routine del sonno|"
    r"allerg|destinazioni esotiche|paradisi dove fuggire dal freddo|"
    r"galateo|come posizionare i bicchieri",
    re.IGNORECASE,
)
MAX_IMAGE_BYTES = 8 * 1024 * 1024
MIN_IMAGE_LONG_EDGE = 1000
MIN_IMAGE_SHORT_EDGE = 500
USER_AGENT = "ATELIER-Magazine/2.0 (+https://github.com/manuelamodeo26-dev/atelier-magazine)"
TRACKING_KEYS = {"fbclid", "gclid", "mc_cid", "mc_eid"}


def is_relevant(article):
    title = str(article.get("title") or "")
    excerpt = str(article.get("excerpt") or "")
    url = str(article.get("url") or "")
    # Match exclusion rules against the headline and URL only. Publisher
    # descriptions can mention unrelated terms in passing and should not
    # disqualify an otherwise relevant fashion/design/culture story.
    text = " ".join((title, url))
    return not EXCLUDED_CONTENT.search(text)




def summary_retry_due(article, now=None):
    retry_after = article.get("editorial_retry_after")
    if not retry_after:
        return True
    try:
        retry_at = datetime.fromisoformat(str(retry_after).replace("Z", "+00:00"))
        if retry_at.tzinfo is None:
            retry_at = retry_at.replace(tzinfo=timezone.utc)
        return retry_at <= (now or datetime.now(timezone.utc))
    except (TypeError, ValueError):
        return True


def source_category(article):
    source = str(article.get("source") or "").lower().removeprefix("www.")
    if source in ("vogue.it", "pambianconews.com"):
        return "Fashion"
    if source in ("outpump.com", "sneakersmagazine.it"):
        return "Streetwear"
    if source == "ad-italia.it":
        return "Design"
    if source in ("exibart.com", "finestresullarte.info"):
        return "Art & Culture"
    return article.get("category") or "Fashion"


def infer_category(title, excerpt, current="Fashion"):
    title_text = str(title or "").lower()
    excerpt_text = str(excerpt or "").lower()
    rules = [
        ("Streetwear", r"streetwear|street style|street-style|sneaker|skateboard|hip.?hop"),
        ("Business", r"fatturato|ricavi|utile netto|bilancio|acquisizion|quotazione|"
                     r"margini|vendite|retail|ceo|amministratore delegato|investiment[oi]|"
                     r"mln|milion|miliard|\bq[1-4]\b|risultati finanziari|trimestre|"
                     r"mercato azionario|export|import|asta|boutique|negozi|"
                     r"asset light|pricing|distribuzion|partnership|collaborazion|"
                     r"accordo|multibrand|diritti tv|rallentamento|piano da"),
        ("Architecture", r"architettur|edificio|edifici|appartamento|villa|palazzo|"
                         r"hôtel particulier|interior design|interior|interni|urbanistica"),
        ("Technology", r"intelligenza artificiale|\bia\b|tecnolog|digitale|"
                       r"realtà virtuale|realtà aumentata|videogiochi|gaming"),
        ("Design", r"\bdesign\b|arredamento|arredo|prodotto|oggetto|"
                   r"progettazione|industrial design|mobili|materiali"),
        ("Art & Culture", r"arte|artist[ai]|mostra|museo|galleria|fotografia|fotografo|"
                          r"cinema|film|musica|music|libr[oi]|romanzo|letteratura|teatro|"
                          r"cultura|festival|curator|fumett|biennale|documentario|"
                          r"serie tv|netflix|ricordo|memoria|omaggio|tributo"),
        ("Lifestyle", r"lifestyle|stile di vita|viagg[io]|travel|hotel|ospitalità|"
                      r"sport|fitness|running|outdoor|wellness|benessere|vita quotidiana"),
    ]
    for category, pattern in rules:
        if re.search(pattern, title_text, re.IGNORECASE):
            return category

    # Keep clearly fashion-led headlines in Fashion even if the excerpt mentions
    # another subject in passing.
    fashion_headline = (
        r"moda|fashion|collezion|sfilat|outfit|look|abiti?|cappotto|blazer|"
        r"scarpe|sneaker|streetwear|make.?up|skincare|profum|gioiell|anell|"
        r"orolog|bors[ae]|accessori|tendenz|trend|beauty|designer|brand|maison|"
        r"tailoring|menswear|womenswear|maglieria|tessut|fashion week|"
        r"abbinar|indoss|vestire|camicia|pantalon|gonna|giacca|décolleté|"
        r"direzione creativa|direttore creativo|direttrice creativa"
    )
    if current == "Fashion" and re.search(fashion_headline, title_text, re.IGNORECASE):
        return "Fashion"

    # Only the broad Fashion feeds need excerpt-based refinement. Dedicated
    # art and design feeds keep their editorial section unless the headline
    # itself clearly identifies a more specific topic.
    if current == "Fashion":
        for category, pattern in rules:
            if re.search(pattern, excerpt_text, re.IGNORECASE):
                return category
    return current or "Fashion"


def local_name(tag):
    return tag.rsplit("}", 1)[-1].lower()


def clean(value):
    value = html.unescape(re.sub(r"<[^>]*>", " ", value or ""))
    # Remove media URLs often embedded at the start of publisher RSS content.
    value = re.sub(r"https?://\S+", " ", value, flags=re.I)
    value = re.sub(r"\b(?:https?://)?(?:www\.)?[^\s]+\.(?:jpe?g|png|webp|gif)(?:\?[^\s]*)?", " ", value, flags=re.I)
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


def best_description(node, *names, limit=2400):
    """Prefer the most informative publisher-supplied RSS/Atom description."""
    wanted = {name.lower() for name in names}
    candidates = []
    for item in node.iter():
        if local_name(item.tag) in wanted:
            value = clean(" ".join(part.strip() for part in item.itertext() if part.strip()))
            if value and value not in candidates:
                candidates.append(value)
    return max(candidates, key=len, default="")[:limit]


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
        if tag.lower() != "meta":
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
    last_error = "Errore non specificato"
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
                description = best_description(node, "description", "summary", "encoded", "content")
                author = child_text(node, "creator", "author", "artist")
                article = {
                    "id": link,
                    "title": title[:300],
                    "excerpt": description[:2200],
                    "author": author[:160],
                    "category": infer_category(title, description, category),
                    "source": host,
                    "date": article_date(node),
                    "url": link,
                    "image": upgrade_image_url(article_image(node)),
                    "image_verified": False,
                    "language": "it",
                }
                if is_relevant(article):
                    articles.append(article)
            metadata_attempts = 0
            for article in articles:
                if (not article["image"] or len(article["excerpt"]) < 900 or not article["author"]) and metadata_attempts < 18:
                    metadata_attempts += 1
                    metadata = fetch_page_metadata(article["url"])
                    if not article["image"]:
                        article["image"] = metadata["image"]
                    if len(metadata["description"]) > len(article["excerpt"]):
                        article["excerpt"] = metadata["description"][:2200]
                    if not article["author"]:
                        article["author"] = metadata["author"]
            print(f"{host}: {len(articles)} articoli")
            return articles, True, ""
        except Exception as exc:
            last_error = "{}: {}".format(type(exc).__name__, str(exc)[:220])
            if attempt == 0:
                time.sleep(1.5)
            else:
                print(f"Feed non disponibile {feed_url}: {exc}")
    return [], False, last_error


def load_previous():
    try:
        with open(OUT, encoding="utf-8") as file:
            payload = json.load(file)
        articles = payload.get("articles", [])
        if not isinstance(articles, list):
            return {}
        original_snapshot = json.dumps(articles, ensure_ascii=False, sort_keys=True)
        previous = {}
        cutoff = datetime.now(timezone.utc) - timedelta(days=MAX_AGE_DAYS)
        for item in articles:
            if not isinstance(item, dict) or item.get("language") != "it":
                continue
            if not is_relevant(item):
                continue
            item["category"] = infer_category(item.get("title"), item.get("excerpt"), source_category(item))
            if item.get("editorial_summary") and not is_valid_editorial_summary(
                item.get("editorial_summary"), item.get("editorial_level")
            ):
                print("Sintesi editoriale non conforme: verrà rigenerata — {}.".format(
                    str(item.get("title") or "")[:90]
                ))
                for key in ("editorial_summary", "editorial_level", "editorial_word_count"):
                    item.pop(key, None)
                # Requeue legacy summaries immediately; future failed attempts
                # receive a cooldown in the generation loop below.
                item.pop("editorial_attempted_at", None)
                item.pop("editorial_retry_after", None)
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

        # Persist archive cleanup even when every RSS feed is temporarily down
        # or no new story arrives. Otherwise excluded legacy stories reappear.
        cleaned = sorted(previous.values(),
                         key=lambda item: item.get("date") or "0000", reverse=True)[:MAX_ARTICLES]
        cleaned_snapshot = json.dumps(cleaned, ensure_ascii=False, sort_keys=True)
        if cleaned_snapshot != original_snapshot:
            payload["updated_at"] = datetime.now(timezone.utc).isoformat()
            payload["articles"] = cleaned
            temporary = OUT + ".tmp"
            with open(temporary, "w", encoding="utf-8") as file:
                json.dump(payload, file, ensure_ascii=False, indent=2)
                file.write("\n")
            os.replace(temporary, OUT)
            print("Archivio ripulito: rimossi {} contenuti non pertinenti, non validi o scaduti.".format(
                len(articles) - len(previous)
            ))
        return previous
    except (OSError, ValueError, TypeError):
        return {}


def main():
    previous = load_previous()
    # Capture an immutable baseline before any in-place enrichment or AI work.
    # Comparing live dictionaries against themselves misses mutations.
    previous_snapshot = json.dumps(
        sorted(previous.values(), key=lambda item: item.get("date") or "0000", reverse=True)[:MAX_ARTICLES],
        ensure_ascii=False,
        sort_keys=True,
    )
    fresh = []
    successful_feeds = 0
    feed_status = []
    for feed_url, category in FEEDS:
        items, feed_ok, feed_error = parse_feed(feed_url, category)
        feed_status.append({
            "source": urlparse(feed_url).netloc.lower().removeprefix("www."),
            "ok": feed_ok,
            "articles": len(items),
            "error": feed_error,
        })
        if feed_ok:
            successful_feeds += 1
        fresh.extend(items)

    if not fresh:
        print("Nessun nuovo articolo: archivio precedente preservato.")
        if not previous:
            raise SystemExit("Archivio vuoto e nessun nuovo articolo utilizzabile: aggiornamento annullato.")
        try:
            with open(OUT, encoding="utf-8") as file:
                payload = json.load(file)
            if payload.get("feed_status") != feed_status or payload.get("feeds_ok") != successful_feeds:
                payload["updated_at"] = datetime.now(timezone.utc).isoformat()
                payload["feeds_ok"] = successful_feeds
                payload["feeds_total"] = len(FEEDS)
                payload["feed_status"] = feed_status
                temporary = OUT + ".tmp"
                with open(temporary, "w", encoding="utf-8") as file:
                    json.dump(payload, file, ensure_ascii=False, indent=2)
                    file.write("\n")
                os.replace(temporary, OUT)
        except (OSError, ValueError, TypeError) as exc:
            print("Stato feed non salvato: {}.".format(type(exc).__name__))
        return

    # Do not re-import or overwrite stories already in the archive.
    # Normalize every URL before comparing so tracking parameters and URL
    # variants do not create duplicate entries.
    merged = dict(previous)
    seen_urls = set(previous)
    added = 0
    duplicates = 0
    new_article_urls = set()
    for article in fresh:
        url = canonical_url(article.get("url"))
        if not url:
            continue
        article["url"] = url
        article["id"] = url
        if not is_relevant(article):
            continue
        article["category"] = infer_category(article.get("title"), article.get("excerpt"), article.get("category"))
        if url in seen_urls:
            duplicates += 1
            # Keep the existing record and its verified image, but enrich its
            # publisher-supplied description when the fresh feed has more detail.
            existing = merged[url]
            if len(article.get("excerpt", "")) > len(existing.get("excerpt", "")):
                existing["excerpt"] = article["excerpt"][:2200]
            if not existing.get("author") and article.get("author"):
                existing["author"] = article["author"]
            continue
        seen_urls.add(url)
        new_article_urls.add(url)
        merged[url] = article
        added += 1
    print(f"Nuovi articoli: {added}; già presenti/duplicati ignorati: {duplicates}.")
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

    new_urls = {canonical_url(item.get("url")) for item in fresh}

    # Recover missing editorial images from each publisher's Open Graph metadata.
    # Backfill a small batch per run, then verify the actual image bytes and dimensions.
    image_backfill_urls = set()
    missing_image_candidates = [
        item for item in articles if not item.get("image")
    ][:MAX_IMAGE_BACKFILLS_PER_RUN]
    if missing_image_candidates:
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
            metadata_rows = list(executor.map(
                fetch_page_metadata,
                [item.get("url", "") for item in missing_image_candidates],
            ))
        for article, metadata in zip(missing_image_candidates, metadata_rows):
            if metadata.get("image"):
                article["image"] = metadata["image"]
                image_backfill_urls.add(canonical_url(article.get("url")))
            if len(metadata.get("description", "")) > len(article.get("excerpt", "")):
                article["excerpt"] = metadata["description"][:2200]
            if not article.get("author") and metadata.get("author"):
                article["author"] = metadata["author"]

    # Generate a small batch of source-grounded editorial summaries per run.
    # The publisher excerpt remains the fallback whenever source text is thin
    # or the optional AI service is unavailable.
    if os.getenv("GROQ_API_KEY", "").strip():
        now = datetime.now(timezone.utc)
        new_candidates = sorted(
            (item for item in articles
             if canonical_url(item.get("url")) in new_article_urls
             and not item.get("editorial_summary")
             and summary_retry_due(item, now)),
            key=lambda item: item.get("date") or "0000",
            reverse=True,
        )
        older_candidates = sorted(
            (item for item in articles
             if canonical_url(item.get("url")) not in new_article_urls
             and not item.get("editorial_summary")
             and summary_retry_due(item, now)),
            key=lambda item: item.get("date") or "9999",
            reverse=False,
        )
        candidates = (new_candidates + older_candidates)[:MAX_SUMMARIES_PER_RUN]
        print("Sintesi AI in coda: {} (massimo {} per esecuzione).".format(len(candidates), MAX_SUMMARIES_PER_RUN))
        for article in candidates:
            source_text = fetch_article_text(article.get("url", ""))
            summary, level = generate_editorial_summary(article, source_text)
            if summary:
                article["editorial_summary"] = summary
                article["editorial_level"] = level
                article["editorial_word_count"] = len(re.findall(r"\b[\wÀ-ÖØ-öø-ÿ’'-]+\b", summary, flags=re.UNICODE))
                article.pop("editorial_retry_after", None)
                article.pop("editorial_attempted_at", None)
                print("Sintesi editoriale generata: {}".format(article.get("title", "")[:90]))
            else:
                attempted_at = datetime.now(timezone.utc)
                article["editorial_attempted_at"] = attempted_at.isoformat()
                article["editorial_retry_after"] = (attempted_at + timedelta(hours=12)).isoformat()
                print("Sintesi editoriale rinviata per 12 ore: {}".format(article.get("title", "")[:90]))
    else:
        print("GROQ_API_KEY non configurata: si mantiene il testo originale delle fonti.")

    # Verify only images belonging to newly imported articles. Existing
    # archive entries are left untouched and are not downloaded again.
    new_urls = {canonical_url(item.get("url")) for item in fresh}
    to_verify = [item for item in articles
                 if (canonical_url(item.get("url")) in new_urls
                     or canonical_url(item.get("url")) in image_backfill_urls)
                 and item.get("image") and not item.get("image_verified")]
    if to_verify:
        print(f"Verifica fotografica: {len(to_verify)} immagini da controllare.")
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            checked = list(executor.map(verify_image, to_verify))
        checked_by_url = {item["url"]: item for item in checked}
        articles = [checked_by_url.get(item["url"], item) for item in articles]
        valid_images = sum(1 for item in articles if item.get("image_verified"))
        print(f"Fotografie verificate: {valid_images}/{len(articles)} articoli.")

    current_snapshot = json.dumps(articles, ensure_ascii=False, sort_keys=True)
    if current_snapshot == previous_snapshot:
        try:
            with open(OUT, encoding="utf-8") as file:
                current_payload = json.load(file)
            if current_payload.get("feed_status") == feed_status and current_payload.get("feeds_ok") == successful_feeds:
                print(f"Nessuna modifica: {len(articles)} articoli già archiviati.")
                return
        except (OSError, ValueError, TypeError):
            pass
        print("Aggiorno soltanto lo stato diagnostico dei feed.")

    payload = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "feeds_ok": successful_feeds,
        "feeds_total": len(FEEDS),
        "feed_status": feed_status,
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
