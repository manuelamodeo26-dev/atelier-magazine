#!/usr/bin/env python3
"""Generate original Italian editorial summaries from publicly available source text."""
import json
import os
import re
import time
from html.parser import HTMLParser
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

USER_AGENT = "ATELIER-Magazine/2.0 (+https://github.com/manuelamodeo26-dev/atelier-magazine)"
MODEL = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")
API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
MAX_SOURCE_CHARS = 12000


class ArticleTextParser(HTMLParser):
    """Extract article headings and paragraphs while ignoring site chrome."""
    IGNORED = {"script", "style", "noscript", "svg", "nav", "header", "footer",
               "aside", "form", "button", "iframe", "picture", "figure"}
    TEXT_TAGS = {"p", "h1", "h2", "h3"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.ignored = 0
        self.current_tag = None
        self.buffer = []
        self.parts = []

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if tag in self.IGNORED:
            self.ignored += 1
            return
        if self.ignored:
            return
        if tag in self.TEXT_TAGS and self.current_tag is None:
            self.current_tag = tag
            self.buffer = []

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag in self.IGNORED:
            self.ignored = max(0, self.ignored - 1)
            return
        if self.ignored:
            return
        if self.current_tag == tag:
            value = re.sub(r"\s+", " ", " ".join(self.buffer)).strip()
            if len(value) >= 45 and value not in self.parts:
                self.parts.append(value)
            self.current_tag = None
            self.buffer = []

    def handle_data(self, data):
        if not self.ignored and self.current_tag and data.strip():
            self.buffer.append(data.strip())


def fetch_article_text(url):
    """Fetch only readable page text; never save or republish the source article."""
    try:
        request = Request(url, headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml",
        })
        with urlopen(request, timeout=10) as response:
            content_type = response.headers.get("Content-Type", "").lower()
            if "html" not in content_type:
                return ""
            raw = response.read(900000).decode("utf-8", errors="replace")
        parser = ArticleTextParser()
        parser.feed(raw)
        return "\n".join(parser.parts)[:MAX_SOURCE_CHARS]
    except (HTTPError, URLError, TimeoutError, ValueError, OSError):
        return ""


def _word_count(value):
    return len(re.findall(r"\b[\wÀ-ÖØ-öø-ÿ’'-]+\b", value, flags=re.UNICODE))


def generate_editorial_summary(article, source_text):
    """Return (summary, level) or empty values when evidence/API is insufficient."""
    if not API_KEY:
        return "", ""
    excerpt = str(article.get("excerpt") or "").strip()
    title = str(article.get("title") or "").strip()
    combined = "\n\n".join(part for part in (title, excerpt, source_text.strip()) if part)
    combined = combined[:MAX_SOURCE_CHARS]
    if len(combined) < 500:
        return "", ""

    prompt = (
        "Sei un redattore di ATELIER, rivista digitale italiana indipendente dedicata a moda, "
        "design, arte e cultura. Scrivi una sintesi editoriale originale in italiano basata "
        "ESCLUSIVAMENTE sul materiale della fonte qui sotto. Non copiare frasi estese, non "
        "inventare fatti, date, numeri, citazioni, intenzioni o conseguenze. Se un dettaglio "
        "non è presente, omettilo. Distingui chiaramente fatti e interpretazioni. Non aggiungere "
        "commenti generici per raggiungere la lunghezza.\n\n"
        "Valuta prima la rilevanza: usa livello 'approfondimento' soltanto se la fonte contiene "
        "sviluppi sostanziali, più elementi verificabili o un tema di particolare rilievo; in "
        "quel caso scrivi 300-450 parole. Per una notizia ordinaria usa livello 'standard' e "
        "scrivi 180-250 parole. In entrambi i casi usa 3-5 paragrafi, senza titolo, elenchi o "
        "sottotitoli. Apri con il fatto principale e il suo contesto; sviluppa i dettagli "
        "concreti; spiega la rilevanza per il settore solo se supportata dalla fonte; chiudi "
        "con una conclusione informativa, non promozionale. Se la fonte è troppo povera per "
        "una sintesi affidabile, restituisci summary vuoto.\n\n"
        "Rispondi esclusivamente in JSON valido con le chiavi 'level' (standard o approfondimento) "
        "e 'paragraphs' (array di 3-5 paragrafi).\n\n"
        "TITOLO: " + title + "\n"
        "FONTE: " + str(article.get("source") or "") + "\n"
        "MATERIALE DISPONIBILE:\n" + combined
    )
    endpoint = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        + quote(MODEL, safe="") + ":generateContent?key=" + quote(API_KEY, safe="")
    )
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.25,
            "maxOutputTokens": 1200,
            "responseMimeType": "application/json",
        },
    }
    request = Request(
        endpoint,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json", "User-Agent": USER_AGENT},
        method="POST",
    )
    for attempt in range(2):
        try:
            with urlopen(request, timeout=45) as response:
                result = json.loads(response.read().decode("utf-8"))
            candidates = result.get("candidates") or []
            parts = candidates[0].get("content", {}).get("parts", []) if candidates else []
            raw = "".join(part.get("text", "") for part in parts).strip()
            if raw.startswith("```"):
                raw = re.sub(r"^\`\`\`(?:json)?\s*|\s*\`\`\`$", "", raw, flags=re.I)
            data = json.loads(raw)
            level = data.get("level")
            paragraphs = data.get("paragraphs")
            if level not in ("standard", "approfondimento") or not isinstance(paragraphs, list):
                return "", ""
            paragraphs = [re.sub(r"\s+", " ", str(p)).strip() for p in paragraphs]
            paragraphs = [p for p in paragraphs if p]
            if not 3 <= len(paragraphs) <= 5:
                return "", ""
            summary = "\n\n".join(paragraphs)
            words = _word_count(summary)
            lower, upper = (300, 450) if level == "approfondimento" else (180, 250)
            if not lower <= words <= upper:
                return "", ""
            return summary, level
        except HTTPError as exc:
            # Quota/rate-limit errors are non-fatal: the source excerpt remains visible.
            if exc.code == 429 and attempt == 0:
                time.sleep(8)
                continue
            print("Sintesi AI non disponibile (HTTP {}).".format(exc.code))
            return "", ""
        except (URLError, TimeoutError, OSError, ValueError, KeyError, IndexError, TypeError) as exc:
            print("Sintesi AI non disponibile: {}".format(type(exc).__name__))
            return "", ""
    return "", ""
