#!/usr/bin/env python3
"""Generate original Italian editorial summaries using the Groq API."""
import json
import os
import re
import time
from html.parser import HTMLParser
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

USER_AGENT = "ATELIER-Magazine/2.0 (+https://github.com/manuelamodeo26-dev/atelier-magazine)"
MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
API_KEY = os.getenv("GROQ_API_KEY", "").strip()
API_ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"
MAX_SOURCE_CHARS = 12000
QUOTA_EXHAUSTED_FOR_RUN = False


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
            value = re.sub(r"\\s+", " ", " ".join(self.buffer)).strip()
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
    return len(re.findall(r"\\b[\\wÀ-ÖØ-öø-ÿ’'-]+\\b", value, flags=re.UNICODE))


def generate_editorial_summary(article, source_text):
    """Return (summary, level) or empty values when evidence/API is insufficient."""
    global QUOTA_EXHAUSTED_FOR_RUN
    if not API_KEY or QUOTA_EXHAUSTED_FOR_RUN:
        return "", ""
    quota_exhausted_during_attempts = False
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
        "commenti generici per raggiungere la lunghezza.\\n\\n"
        "Valuta prima la rilevanza: usa livello 'approfondimento' soltanto se la fonte contiene "
        "sviluppi sostanziali, più elementi verificabili o un tema di particolare rilievo; in "
        "quel caso scrivi 450-600 parole. Per una notizia ordinaria usa livello 'standard' e "
        "scrivi 300-400 parole. Quando produci una sintesi usa 4-6 paragrafi, senza titolo, elenchi o "
        "sottotitoli. Apri con il fatto principale e il suo contesto; sviluppa i dettagli "
        "concreti; spiega la rilevanza per il settore solo se supportata dalla fonte; chiudi "
        "con una conclusione informativa, non promozionale. Se la fonte è troppo povera per "
        "una sintesi affidabile, restituisci esattamente JSON con level 'standard' e paragraphs come array vuoto. Non aggiungere testo fuori dal JSON.\\n\\n"
        "Rispondi esclusivamente in JSON valido con le chiavi 'level' (standard o approfondimento) "
        "e 'paragraphs' (array di 4-6 paragrafi).\\n\\n"
        "TITOLO: " + title + "\\n"
        "FONTE: " + str(article.get("source") or "") + "\\n"
        "MATERIALE DISPONIBILE:\\n" + combined
    )
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,
        "max_completion_tokens": 1800,
        "response_format": {"type": "json_object"},
        "reasoning_effort": "low",
        "reasoning_format": "hidden",
    }
    fallback_models = ["openai/gpt-oss-20b"]
    models = list(dict.fromkeys([MODEL] + fallback_models))
    for model in models:
        payload["model"] = model
        request = Request(
            API_ENDPOINT,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer " + API_KEY,
                "User-Agent": USER_AGENT,
            },
            method="POST",
        )
        for attempt in range(2):
            try:
                with urlopen(request, timeout=45) as response:
                    result = json.loads(response.read().decode("utf-8"))
                if not isinstance(result, dict):
                    print("Risposta Groq non strutturata su {}.".format(model))
                    break
                choices = result.get("choices") or []
                if not choices or not isinstance(choices[0], dict):
                    print("Groq {} senza contenuto utilizzabile.".format(model))
                    break
                choice = choices[0]
                message = choice.get("message") or {}
                raw = str(message.get("content") or "").strip()
                if not raw:
                    print("Groq {} ha restituito testo vuoto ({}).".format(
                        model, choice.get("finish_reason", "non indicato")
                    ))
                    break
                try:
                    data = json.loads(raw)
                except json.JSONDecodeError:
                    start_json = raw.find("{")
                    if start_json < 0:
                        print("Groq {} ha restituito JSON non valido.".format(model))
                        break
                    try:
                        data, _ = json.JSONDecoder().raw_decode(raw[start_json:])
                    except json.JSONDecodeError:
                        print("Groq {} ha restituito JSON incompleto.".format(model))
                        break
                if not isinstance(data, dict):
                    break
                level = data.get("level")
                paragraphs = data.get("paragraphs")
                if level not in ("standard", "approfondimento") or not isinstance(paragraphs, list):
                    print("Groq {}: struttura della sintesi non valida.".format(model))
                    break
                paragraphs = [re.sub(r"\\s+", " ", str(p)).strip() for p in paragraphs]
                paragraphs = [p for p in paragraphs if p]
                if not 4 <= len(paragraphs) <= 6:
                    print("Groq {}: numero di paragrafi non valido.".format(model))
                    break
                summary = "\n\n".join(paragraphs)
                words = _word_count(summary)
                if level == "approfondimento" and 300 <= words <= 400:
                    print("Groq {}: sintesi riclassificata come standard ({} parole).".format(model, words))
                    level = "standard"
                lower, upper = (450, 600) if level == "approfondimento" else (300, 400)
                if not lower <= words <= upper:
                    print("Groq {}: sintesi scartata ({} parole).".format(model, words))
                    break
                if model != MODEL:
                    print("Sintesi generata con modello alternativo {}.".format(model))
                return summary, level
            except HTTPError as exc:
                detail = ""
                try:
                    error_body = exc.read().decode("utf-8", errors="replace")
                    error_data = json.loads(error_body) if error_body else {}
                    detail = str(error_data.get("error", {}).get("message") or "").strip()
                except (ValueError, AttributeError, TypeError):
                    detail = ""
                if exc.code == 429:
                    quota_exhausted = any(token in detail.lower() for token in (
                        "rate_limit", "tokens per day", "requests per day", "quota", "limit"
                    ))
                    if quota_exhausted:
                        quota_exhausted_during_attempts = True
                        print("Groq {}: limite di utilizzo raggiunto; provo il modello alternativo.".format(model))
                        break
                    if attempt == 0:
                        retry_after = exc.headers.get("Retry-After") if exc.headers else None
                        try:
                            delay = min(20, max(3, int(retry_after))) if retry_after else 8
                        except (TypeError, ValueError):
                            delay = 8
                        print("Groq {}: limite richieste (HTTP 429); nuovo tentativo tra {}s.".format(
                            model, delay
                        ))
                        time.sleep(delay)
                        continue
                message = (" — " + detail[:220]) if detail else ""
                print("Groq non disponibile (HTTP {}){}.".format(exc.code, message))
                break
            except (URLError, TimeoutError, OSError) as exc:
                print("Groq non disponibile: {}.".format(type(exc).__name__))
                break
            except (ValueError, KeyError, IndexError, TypeError) as exc:
                print("Risposta Groq non valida: {}.".format(type(exc).__name__))
                break
    if quota_exhausted_during_attempts:
        QUOTA_EXHAUSTED_FOR_RUN = True
        print("Limiti Groq esauriti: sospendo gli altri tentativi AI per questa esecuzione.")
    print("Sintesi AI non disponibile: esauriti modello principale e modello alternativo Groq.")
    return "", ""
