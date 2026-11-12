# ATELIER — Moda, Design e Cultura

Rivista digitale indipendente, in italiano, con un linguaggio visivo editoriale ispirato alla cultura dei magazine contemporanei e una direzione artistica originale.

## Identità editoriale

- Palette: avorio, nero, rosso e grigio cemento.
- Tipografia: Syne, Cormorant Garamond, DM Sans e IBM Plex Mono.
- Impaginazione editoriale ibrida: immagini, titoli forti, rubriche e percorsi tematici.
- Navigazione e interfaccia in italiano.
- Layout responsive per smartphone, tablet e desktop.

## Contenuti e immagini

Le notizie vengono raccolte da feed pubblici di editori italiani dedicati a moda, design, architettura e arte. I titoli e i sommari vengono mostrati nella lingua originale della fonte: il progetto non dichiara traduzioni automatiche che non esegue.

Le fotografie sono quelle distribuite dalle fonti nei rispettivi feed. Quando l'indirizzo dell'immagine consente parametri di dimensione, il raccoglitore richiede una versione più grande; la resa finale dipende comunque dal file originale, dal CDN e dalle condizioni d'uso del publisher. Le immagini non vengono copiate nel repository.

Fonti configurate in `scripts/fetch_news.py`: Vogue Italia, Pambianco, Fashion News Magazine, AD Italia, Artribune, Exibart, Finestre sull'Arte e Domus. La disponibilità effettiva di ogni feed può cambiare.

## Aggiornamento e pubblicazione

- **Update ATELIER news**: esecuzione programmata ogni 6 ore e avvio manuale da GitHub Actions.
- Il processo conserva l'archivio se le fonti non rispondono, elimina i contenuti non italiani e quelli più vecchi di 120 giorni e rimuove i duplicati tramite URL.
- **Deploy ATELIER to GitHub Pages**: pubblicazione del sito statico.
- In **Settings → Pages**, la sorgente deve essere **GitHub Actions**.

La raccolta RSS non equivale a una verifica giornalistica: controllare sempre notizie, attribuzioni e diritti di utilizzo prima della pubblicazione.

## Funzioni

- Ricerca e filtri per categoria.
- Schede editoriali con immagini responsive e caricamento differito.
- Collegamenti alle fonti originali.
- Cache PWA e supporto offline.
- Newsletter non attiva: il sito non raccoglie indirizzi email.

## File principali

- `index.html`: struttura e contenuti della homepage.
- `style.css`: sistema visivo e layout responsive.
- `app.js`: archivio, filtri, ricerca e navigazione.
- `data/articles.json`: articoli importati.
- `scripts/fetch_news.py`: raccolta RSS/Atom.
- `.github/workflows/deploy.yml`: pubblicazione.
- `.github/workflows/news.yml`: aggiornamento automatico delle notizie.
- `manifest.webmanifest` e `sw.js`: installazione e cache PWA.
