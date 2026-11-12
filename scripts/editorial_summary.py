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
MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
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
        "quel caso scrivi 450-600 parole. Per una notizia ordinaria usa livello 'standard' e "
        "scrivi 300-400 parole. Quando produci una sintesi usa 4-6 paragrafi, senza titolo, elenchi o "
        "sottotitoli. Apri con il fatto principale e il suo contesto; sviluppa i dettagli "
        "concreti; spiega la rilevanza per il settore solo se supportata dalla fonte; chiudi "
        "con una conclusione informativa, non promozionale. Se la fonte è troppo povera per "
        "una sintesi affidabile, restituisci esattamente JSON con level 'standard' e paragraphs come array vuoto. Non aggiungere testo fuori dal JSON.\n\n"
        "Rispondi esclusivamente in JSON valido con le chiavi 'level' (standard o approfondimento) "
        "e 'paragraphs' (array di 4-6 paragrafi).\n\n"
        "TITOLO: " + title + "\n"
        "FONTE: " + str(article.get("source") or "") + "\n"
        "MATERIALE DISPONIBILE:\n" + combined
    )
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "thinkingConfig": {"thinkingLevel": "low"},
            "maxOutputTokens": 3500,
            "responseMimeType": "application/json",
        },
    }
    fallback_models = ["gemini-3.7-flash", "gemini-3.6-flash", "gemini-3.5-flash-lite"]
    models = list(dict.fromkeys([MODEL] + fallback_models))
    for model in models:
        endpoint = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            + quote(model, safe="") + ":generateContent?key=" + quote(API_KEY, safe="")
        )
        request = Request(
            endpoint,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json", "User-Agent": USER_AGENT},
            method="POST",
        )
        for attempt in range(2):
            try:
                with urlopen(request, timeout=24) as response:
                    result = json.loads(response.read().decode("utf-8"))
                if not isinstance(result, dict):
                    print("Risposta Gemini non strutturata su {}.".format(model))
                    break
                candidates = result.get("candidates") or []
                if not candidates:
                    reason = (result.get("promptFeedback") or {}).get("blockReason", "nessun candidato")
                    print("Gemini {} senza contenuto utilizzabile: {}.".format(model, reason))
                    break
                candidate = candidates[0]
                if not isinstance(candidate, dict):
                    break
                finish_reason = candidate.get("finishReason", "non indicato")
                content_data = candidate.get("content") or {}
                parts = content_data.get("parts", []) if isinstance(content_data, dict) else []
                if not isinstance(parts, list):
                    parts = []
                raw = "".join(
                    part.get("text", "") for part in parts if isinstance(part, dict)
                ).strip()
                if raw.startswith(chr(96) * 3):
                    raw = raw.split("\n", 1)[-1]
                    raw = raw.rsplit(chr(96) * 3, 1)[0].strip()
                if not raw:
                    print("Gemini {} ha restituito testo vuoto ({}).".format(model, finish_reason))
                    break
                try:
                    data = json.loads(raw)
                except json.JSONDecodeError:
                    start_json = raw.find("{")
                    if start_json < 0:
                        print("Gemini {} ha restituito JSON non valido.".format(model))
                        break
                    try:
                        data, _ = json.JSONDecoder().raw_decode(raw[start_json:])
                    except json.JSONDecodeError:
                        print("Gemini {} ha restituito JSON incompleto.".format(model))
                        break
                if not isinstance(data, dict):
                    break
                level = data.get("level")
                paragraphs = data.get("paragraphs")
                if level not in ("standard", "approfondimento") or not isinstance(paragraphs, list):
                    print("Gemini {}: struttura della sintesi non valida.".format(model))
                    break
                paragraphs = [re.sub(r"\s+", " ", str(p)).strip() for p in paragraphs]
                paragraphs = [p for p in paragraphs if p]
                if not 4 <= len(paragraphs) <= 6:
                    print("Gemini {}: numero di paragrafi non valido.".format(model))
                    break
                summary = "\n\n".join(paragraphs)
                words = _word_count(summary)
                # Keep a useful 300–400-word text if a model mislabels it as an in-depth feature.
                if level == "approfondimento" and 300 <= words <= 400:
                    print("Gemini {}: sintesi riclassificata come standard ({} parole).".format(model, words))
                    level = "standard"
                lower, upper = (450, 600) if level == "approfondimento" else (300, 400)
                if not lower <= words <= upper:
                    print("Gemini {}: sintesi scartata ({} parole).".format(model, words))
                    break
                if model != MODEL:
                    print("Sintesi generata con modello alternativo {}.".format(model))
                return summary, level
            except HTTPError as exc:
                # Respect Google's rate-limit window instead of hammering
                # every model immediately with the same project quota.
                detail = ""
                try:
                    error_body = exc.read().decode("utf-8", errors="replace")
                    error_data = json.loads(error_body) if error_body else {}
                    detail = str(
                        ((error_data.get("error") or {}).get("message")) or ""
                    ).strip()
                except (ValueError, AttributeError, TypeError):
                    detail = ""
                if exc.code == 429:
                    quota_exhausted = any(token in detail.lower() for token in (
                        "quota", "resource_exhausted", "exceeded your current"
                    ))
                    if quota_exhausted:
                        print("Gemini {}: quota esaurita; passo al modello alternativo senza ripetere la richiesta.".format(model))
                        break
                    if attempt == 0:
                        retry_after = exc.headers.get("Retry-After") if exc.headers else None
                        try:
                            delay = min(20, max(3, int(retry_after))) if retry_after else 8
                        except (TypeError, ValueError):
                            delay = 8
                        print("Gemini {}: limite richieste (HTTP 429); nuovo tentativo tra {}s.".format(
                            model, delay
                        ))
                        time.sleep(delay)
                        continue
                message = (" — " + detail[:220]) if detail else ""
                print("Gemini {} non disponibile (HTTP {}){}.".format(
                    model, exc.code, message
                ))
                break
            except (URLError, TimeoutError, OSError) as exc:
                print("Gemini {} non disponibile: {}.".format(model, type(exc).__name__))
                break
            except (ValueError, KeyError, IndexError, TypeError) as exc:
                print("Risposta Gemini {} non valida: {}.".format(model, type(exc).__name__))
                break
    print("Sintesi AI non disponibile: esauriti modello principale e modelli alternativi.")
    return "", ""
