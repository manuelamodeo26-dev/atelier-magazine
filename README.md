# ATELIER — Fashion, Design & Culture

Rivista digitale indipendente in italiano.

## Pubblicazione GitHub Pages
Il workflow **Deploy ATELIER to GitHub Pages** pubblica il contenuto della root. In **Settings → Pages**, imposta **Source: GitHub Actions** se non è già selezionato.

## Aggiornamento automatico delle notizie
Il workflow **Update ATELIER news** raccoglie notizie dai feed RSS configurati in `scripts/fetch_news.py` ogni 6 ore e può essere avviato manualmente da **Actions**.

L'archivio viene scritto in `data/articles.json` e letto dalla homepage. Le fonti possono non essere disponibili o cambiare formato; i contenuti restano nella lingua originale e l'automazione non equivale a verifica giornalistica. Controllare attribuzione e diritti delle immagini prima di un uso editoriale.

## File principali
- `index.html`: homepage
- `style.css`: stile responsive
- `app.js`: filtri, ricerca e caricamento articoli
- `data/articles.json`: archivio
- `scripts/fetch_news.py`: raccolta RSS
- `.github/workflows/deploy.yml`: pubblicazione
- `.github/workflows/news.yml`: aggiornamento notizie
- `manifest.webmanifest` e `sw.js`: installazione e cache PWA

La newsletter è solo grafica e non raccoglie indirizzi email.
