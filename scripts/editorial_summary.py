#!/usr/bin/env python3
"""Generate original Italian editorial summaries using Groq with Gemini fallback."""
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
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash").strip()
GEMINI_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/{}:generateContent"
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


def is_valid_editorial_summary(summary, level):
    """Check that a stored summary meets ATELIER's editorial format."""
    if level not in ("standard", "approfondimento") or not isinstance(summary, str):
        return False
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", summary) if part.strip()]
    words = _word_count(summary)
    if level == "standard":
        return 3 <= len(paragraphs) <= 4 and 250 <= words <= 300
    return 4 <= len(paragraphs) <= 5 and 350 <= words <= 450


def generate_editorial_summary(article, source_text):
    """Return (summary, level) or empty values when evidence/API is insufficient."""
    global QUOTA_EXHAUSTED_FOR_RUN
    if (not API_KEY and not GEMINI_API_KEY) or QUOTA_EXHAUSTED_FOR_RUN:
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
        "commenti generici per raggiungere la lunghezza.\n\n"
        "Scrivi un articolo editoriale completo ma scorrevole, pensato per un pubblico giovane. "
        "Per una notizia standard usa 250-300 parole in 3-4 paragrafi; per un vero approfondimento "
        "usa 350-450 parole in 4-5 paragrafi. Non allungare artificialmente il testo e non ripetere "
        "concetti. Usa un italiano naturale, contemporaneo e preciso, senza gergo inutile e senza "
        "tono scolastico o pubblicitario. Apri spiegando chiaramente che cosa è successo e perché "
        "è interessante; sviluppa i fatti, il contesto e i dettagli concreti; spiega le possibili "
        "ricadute sul settore solo se supportate dalla fonte. Inserisci nel terzo paragrafo una "
        "frase centrale che riassuma il punto più importante: sarà evidenziata in grassetto sul sito, "
        "quindi deve essere autonoma, informativa e non generica. Chiudi con una conclusione utile. "
        "Non usare titoli, elenchi o sottotitoli nei paragrafi. Se la fonte è troppo povera per "
        "una sintesi affidabile, restituisci JSON con level 'standard' e paragraphs come array vuoto. "
        "Non aggiungere fatti non presenti nel materiale.\n\n"
        "Rispondi esclusivamente in JSON valido con le chiavi 'level' (standard o approfondimento) "
        "e 'paragraphs' (array di 3-5 paragrafi, secondo la lunghezza scelta).\n\n"
        "TITOLO: " + title + "\n"
        "FONTE: " + str(article.get("source") or "") + "\n"
        "MATERIALE DISPONIBILE:\n" + combined
    )
    def parse_summary(raw, provider):
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            start_json = raw.find("{")
            if start_json < 0:
                print("{} ha restituito JSON non valido.".format(provider))
                return "", ""
            try:
                data, _ = json.JSONDecoder().raw_decode(raw[start_json:])
            except json.JSONDecodeError:
                print("{} ha restituito JSON incompleto.".format(provider))
                return "", ""
        if not isinstance(data, dict):
            return "", ""
        level = data.get("level")
        paragraphs = data.get("paragraphs")
        if level not in ("standard", "approfondimento") or not isinstance(paragraphs, list):
            print("{}: struttura della sintesi non valida.".format(provider))
            return "", ""
        paragraphs = [re.sub(r"\s+", " ", str(p)).strip() for p in paragraphs]
        paragraphs = [p for p in paragraphs if p]
        summary = "\n\n".join(paragraphs)
        words = _word_count(summary)
        min_paragraphs, max_paragraphs = (4, 5) if level == "approfondimento" else (3, 4)
        min_words, max_words = (350, 450) if level == "approfondimento" else (250, 300)
        if not min_paragraphs <= len(paragraphs) <= max_paragraphs:
            print("{}: numero di paragrafi non valido.".format(provider))
            return "", ""
        if not min_words <= words <= max_words:
            print("{}: articolo scartato ({} parole).".format(provider, words))
            return "", ""
        return summary, level

    quota_exhausted_during_attempts = False
    if API_KEY:
        payload = {
            "model": MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
            "max_completion_tokens": 2400,
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
                    choices = result.get("choices") or [] if isinstance(result, dict) else []
                    if not choices or not isinstance(choices[0], dict):
                        print("Groq {} senza contenuto utilizzabile.".format(model))
                        break
                    raw = str((choices[0].get("message") or {}).get("content") or "").strip()
                    if not raw:
                        print("Groq {} ha restituito testo vuoto.".format(model))
                        break
                    summary, level = parse_summary(raw, "Groq")
                    if summary:
                        if model != MODEL:
                            print("Sintesi generata con modello alternativo {}.".format(model))
                        return summary, level
                    break
                except HTTPError as exc:
                    detail = ""
                    try:
                        error_body = exc.read().decode("utf-8", errors="replace")
                        error_data = json.loads(error_body) if error_body else {}
                        detail = str(error_data.get("error", {}).get("message") or "").strip()
                    except (ValueError, AttributeError, TypeError):
                        pass
                    if exc.code == 429:
                        quota_exhausted = any(token in detail.lower() for token in (
                            "rate_limit", "tokens per day", "requests per day", "quota", "limit"
                        ))
                        if quota_exhausted:
                            quota_exhausted_during_attempts = True
                            print("Groq {}: quota esaurita; passo al fallback.".format(model))
                            break
                        if attempt == 0:
                            retry_after = exc.headers.get("Retry-After") if exc.headers else None
                            try:
                                delay = min(20, max(3, int(retry_after))) if retry_after else 8
                            except (TypeError, ValueError):
                                delay = 8
                            print("Groq {}: HTTP 429; nuovo tentativo tra {}s.".format(model, delay))
                            time.sleep(delay)
                            continue
                    print("Groq non disponibile (HTTP {}).".format(exc.code))
                    break
                except (URLError, TimeoutError, OSError, ValueError, KeyError, IndexError, TypeError) as exc:
                    print("Groq non disponibile: {}.".format(type(exc).__name__))
                    break

    # Gemini is an independent provider: it is tried after Groq quota exhaustion
    # and also when Groq is absent or temporarily unavailable.
    gemini_quota_exhausted = False
    if GEMINI_API_KEY:
        gemini_payload = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.2,
                "maxOutputTokens": 2400,
                "responseMimeType": "application/json",
            },
        }
        gemini_request = Request(
            GEMINI_ENDPOINT.format(GEMINI_MODEL),
            data=json.dumps(gemini_payload, ensure_ascii=False).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "x-goog-api-key": GEMINI_API_KEY,
                "User-Agent": USER_AGENT,
            },
            method="POST",
        )
        for attempt in range(2):
            try:
                # Gemini can take longer on long editorial prompts; retry one
                # transient network failure before deferring this article.
                with urlopen(gemini_request, timeout=120) as response:
                    result = json.loads(response.read().decode("utf-8"))
                candidates = result.get("candidates") or [] if isinstance(result, dict) else []
                parts = ((candidates[0].get("content") or {}).get("parts") or []) if candidates else []
                raw = "\n".join(str(part.get("text") or "") for part in parts if isinstance(part, dict)).strip()
                if raw:
                    summary, level = parse_summary(raw, "Gemini")
                    if summary:
                        print("Sintesi generata con Gemini ({}).".format(GEMINI_MODEL))
                        return summary, level
                print("Gemini ha restituito una risposta non utilizzabile.")
                break
            except HTTPError as exc:
                detail = ""
                try:
                    error_body = exc.read().decode("utf-8", errors="replace")
                    error_data = json.loads(error_body) if error_body else {}
                    detail = str(error_data.get("error", {}).get("message") or "").strip()
                except (ValueError, AttributeError, TypeError):
                    pass
                gemini_quota_exhausted = exc.code == 429
                print("Gemini non disponibile (HTTP {}){}.".format(
                    exc.code, (" — " + detail[:180]) if detail else ""
                ))
                break
            except (URLError, TimeoutError, OSError, ValueError, KeyError, IndexError, TypeError) as exc:
                if attempt == 0:
                    print("Gemini: errore temporaneo {}; nuovo tentativo tra 5s.".format(type(exc).__name__))
                    time.sleep(5)
                    continue
                print("Gemini non disponibile: {}.".format(type(exc).__name__))

    # Groq quota exhaustion alone must not start a 24-hour cooldown when
    # Gemini is configured but only encountered a transient error.
    if gemini_quota_exhausted or (quota_exhausted_during_attempts and not GEMINI_API_KEY):
        QUOTA_EXHAUSTED_FOR_RUN = True
        print("Quote AI esaurite: sospendo gli altri tentativi per questa esecuzione.")
    print("Sintesi AI non disponibile: Groq e Gemini non hanno prodotto un risultato valido.")
    return "", ""
