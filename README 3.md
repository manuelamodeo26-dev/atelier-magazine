# ATELIER — Fashion, Design & Culture

Rivista digitale indipendente in italiano. Versione iniziale ATELIER v3.

## Pubblicazione gratuita con GitHub Pages

1. Carica tutti i file e le cartelle di questo progetto nella root del repository `atelier-magazine`.
2. Apri **Settings → Pages**.
3. In **Build and deployment**, scegli **GitHub Actions** come Source.
4. Apri la scheda **Actions** e verifica l'esecuzione di `Deploy ATELIER to GitHub Pages`.
5. Quando il deploy termina correttamente, il sito sarà disponibile all'indirizzo `https://manuelamodeo26-dev.github.io/atelier-magazine/`.

## Aggiornamento notizie

Il workflow `Update ATELIER news` prova a raccogliere feed RSS ogni 15 minuti circa e può essere avviato manualmente da Actions → Update ATELIER news → Run workflow.

**Limiti importanti**
- GitHub Actions può ritardare o saltare gli avvii pianificati; non garantisce esecuzione esatta ogni 15 minuti.
- I feed RSS disponibili e i loro termini possono cambiare. Alcune fonti possono non rispondere.
- Le notizie sono mostrate nella lingua originale del feed: questa versione non inventa traduzioni automatiche. Un passaggio editoriale italiano affidabile va aggiunto separatamente.
- Le immagini RSS sono mostrate solo se il feed fornisce un URL immagine; prima dell'uso editoriale occorre verificare diritti, termini e attribuzione della fonte.
- Il workflow raccoglie titoli, estratti e link; non verifica autonomamente la veridicità delle notizie.
- La newsletter è solo un elemento grafico e non raccoglie indirizzi.
- Non esiste un pannello redazionale centrale in questa versione. Gli articoli automatici vengono gestiti in `data/articles.json`.

## Modifica manuale dei contenuti

Aggiungi articoli nell'array `articles` in `data/articles.json` usando questa struttura:

```json
{
  "title": "Titolo dell'articolo",
  "excerpt": "Breve descrizione.",
  "category": "Fashion",
  "source": "Nome della fonte",
  "date": "2026-11-11T10:00:00Z",
  "url": "https://esempio.com/articolo",
  "image": ""
}
```

Categorie consigliate: `Fashion`, `Streetwear`, `Design`, `Art & Culture`, `Technology`.

## Struttura

- `index.html`: homepage
- `assets/css/style.css`: identità visiva e layout responsive
- `assets/js/app.js`: filtri, ricerca, archivio
- `data/articles.json`: archivio editoriale
- `scripts/fetch_news.py`: raccolta RSS
- `.github/workflows/`: pubblicazione e aggiornamento automatico
- `manifest.webmanifest` e `sw.js`: installazione PWA e cache essenziale
