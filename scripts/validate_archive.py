#!/usr/bin/env python3
"""Validate the ATELIER article archive before deployment."""
import json
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

from editorial_summary import is_valid_editorial_summary, _word_count

ROOT = Path(__file__).resolve().parent.parent
ARCHIVE = ROOT / "data" / "articles.json"

def validate_payload(payload):
    errors, warnings = [], []
    if not isinstance(payload, dict):
        return ["La radice JSON deve essere un oggetto."], warnings
    articles = payload.get("articles")
    if not isinstance(articles, list):
        return ["Il campo articles deve essere un array."], warnings
    maintenance = payload.get("archive_status") == "maintenance"
    if not articles and not maintenance:
        errors.append("Archivio vuoto: pubblicazione bloccata.")
    if maintenance and articles:
        errors.append("La modalità manutenzione deve avere un archivio vuoto.")
    if len(articles) > 180:
        errors.append("Archivio oltre il limite di 180 articoli.")
    total, ok = payload.get("feeds_total"), payload.get("feeds_ok")
    if maintenance:
        if total != 0 or ok != 0 or payload.get("feed_status") != []:
            errors.append("Metadati feed non validi per la modalità manutenzione.")
    elif not isinstance(total, int) or not isinstance(ok, int) or total < 1 or not 0 <= ok <= total:
        errors.append("Metadati dei feed non validi.")
    elif ok < total:
        warnings.append("Feed disponibili: {}/{}.".format(ok, total))
    feed_status = payload.get("feed_status")
    if feed_status is not None:
        if not isinstance(feed_status, list) or (isinstance(total, int) and len(feed_status) != total):
            errors.append("Diagnostica feed non coerente con il numero di fonti.")
        else:
            sources = set()
            for feed in feed_status:
                if not isinstance(feed, dict) or not isinstance(feed.get("source"), str) or not feed["source"].strip():
                    errors.append("Voce diagnostica feed non valida.")
                    continue
                if feed["source"] in sources:
                    errors.append("Fonte duplicata nella diagnostica feed.")
                sources.add(feed["source"])
                if not isinstance(feed.get("ok"), bool) or not isinstance(feed.get("articles"), int) or feed["articles"] < 0:
                    errors.append("Stato o conteggio articoli del feed non valido.")
                if "error" in feed and not isinstance(feed["error"], str):
                    errors.append("Dettaglio errore del feed non valido.")
    seen = set()
    for number, article in enumerate(articles, 1):
        label = "Articolo {}: ".format(number)
        if not isinstance(article, dict):
            errors.append(label + "record non valido.")
            continue
        for field in ("id", "title", "url", "date", "category", "source"):
            if not isinstance(article.get(field), str) or not article[field].strip():
                errors.append(label + "campo {} mancante.".format(field))
        url = article.get("url", "")
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            errors.append(label + "URL della fonte non valido.")
        if url in seen:
            errors.append(label + "URL duplicato.")
        seen.add(url)
        if article.get("id") and url and article["id"] != url:
            errors.append(label + "ID e URL non coincidono.")
        if article.get("language") != "it":
            errors.append(label + "lingua diversa dall’italiano.")
        try:
            datetime.fromisoformat(str(article.get("date", "")).replace("Z", "+00:00"))
        except ValueError:
            errors.append(label + "data non valida.")
        summary = article.get("editorial_summary")
        if summary:
            if not is_valid_editorial_summary(summary, article.get("editorial_level")):
                errors.append(label + "sintesi editoriale fuori standard.")
            stored_count = article.get("editorial_word_count")
            if stored_count is not None and stored_count != _word_count(summary):
                errors.append(label + "conteggio parole della sintesi non coerente.")
        if article.get("image_verified") is True:
            image = urlparse(str(article.get("image", "")))
            if image.scheme != "https" or not image.netloc:
                errors.append(label + "immagine verificata senza URL HTTPS.")
            width, height = article.get("image_width"), article.get("image_height")
            if not isinstance(width, int) or not isinstance(height, int):
                errors.append(label + "dimensioni immagine verificate mancanti.")
            elif max(width, height) < 1000 or min(width, height) < 500:
                errors.append(label + "risoluzione immagine verificata inferiore a 1000x500.")
            if article.get("image_format") not in ("jpeg", "png", "webp"):
                errors.append(label + "formato immagine verificata non supportato.")
    return errors, warnings

def main():
    try:
        payload = json.loads(ARCHIVE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print("Impossibile leggere l’archivio: {}".format(exc), file=sys.stderr)
        return 1
    errors, warnings = validate_payload(payload)
    for warning in warnings:
        print("AVVISO: " + warning)
    for error in errors:
        print("ERRORE: " + error, file=sys.stderr)
    if errors:
        print("Controllo archivio fallito: {} errori.".format(len(errors)), file=sys.stderr)
        return 1
    print("Archivio valido: {} articoli; sintesi e immagini conformi.".format(len(payload["articles"])))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
