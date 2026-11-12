# ATELIER — Fashion, Design & Culture

Rivista digitale indipendente in italiano, pubblicata come sito statico tramite GitHub Pages.

## Pubblicazione

Il workflow **Deploy ATELIER to GitHub Pages** pubblica la root del repository a ogni push su `main`.

In **Settings → Pages**, imposta **Source: GitHub Actions**. La pubblicazione richiede che GitHub Pages sia abilitato per il repository e che l'account/repository ne abbia accesso.

## Aggiornamento automatico delle notizie

Il workflow **Update ATELIER news** prova ad aggiornare l'archivio ogni 6 ore e può essere avviato manualmente dalla scheda **Actions**.

- Le fonti sono feed RSS/Atom pubblici configurati in `scripts/fetch_news.py`.
- L'archivio viene salvato in `data/articles.json`.
- Sono importati titolo, descrizione, fonte, data, link e, quando presente, immagine fornita dal feed.
- Se una fonte non risponde o cambia formato, il processo registra l'errore e continua con le altre fonti.
- Le notizie restano nella lingua originale: non viene eseguita una traduzione automatica.
- La raccolta automatica non equivale a verifica giornalistica. Verificare sempre contenuti, attribuzione, diritti e condizioni d'uso delle immagini prima della pubblicazione.

La disponibilità e la frequenza di aggiornamento dipendono dai feed esterni e dalla pianificazione di GitHub Actions; GitHub può ritardare i workflow programmati.

## Funzioni attive

- Homepage editoriale responsive.
- Filtri per categoria e ricerca nell'archivio caricato.
- Apertura delle fonti originali.
- Fallback editoriale quando l'archivio non è disponibile o è vuoto.
- Cache PWA con aggiornamento degli asset e fallback offline.

La newsletter è **non attiva**: il sito non raccoglie né invia indirizzi email.

## File principali

- `index.html`: homepage e struttura.
- `style.css`: stile responsive.
- `app.js`: caricamento articoli, filtri, ricerca e menu.
- `data/articles.json`: archivio.
- `scripts/fetch_news.py`: raccolta RSS/Atom.
- `.github/workflows/deploy.yml`: pubblicazione.
- `.github/workflows/news.yml`: aggiornamento notizie.
- `manifest.webmanifest` e `sw.js`: installazione e cache PWA.
