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

Fonti configurate in `scripts/fetch_news.py`: Vogue Italia, Pambianco, AD Italia, Exibart e Finestre sull'Arte. Le immagini mancanti nel feed vengono cercate nei metadati Open Graph delle pagine originali, con un numero limitato di richieste. La disponibilità effettiva di ogni feed può cambiare.

## Aggiornamento e pubblicazione

- **Update ATELIER news**: esecuzione programmata ogni 6 ore e avvio manuale da GitHub Actions.
- Il processo conserva l'archivio se le fonti non rispondono, elimina i contenuti non italiani e quelli più vecchi di 120 giorni e rimuove i duplicati tramite URL.
- **Deploy ATELIER to GitHub Pages**: pubblicazione del sito statico.
- In **Settings → Pages**, la sorgente deve essere **GitHub Actions**.

La raccolta RSS non equivale a una verifica giornalistica: controllare sempre notizie, attribuzioni e diritti di utilizzo prima della pubblicazione.

## Lettura e verifica editoriale

- Ogni articolo si apre in una scheda interna: titolo, categoria, data, editore, autore quando disponibile e sintesi fornita dall'editore.
- Le fonti sono raccolte in fondo alla scheda. Il collegamento esterno è facoltativo e viene aperto solo se il lettore lo seleziona.
- ATELIER non ripubblica integralmente articoli protetti o contenuti paywall: mostra le informazioni e le sintesi effettivamente disponibili nei feed e nei metadati pubblici, senza inventare dettagli.
- Le fotografie vengono verificate prima della pubblicazione: risposta HTTP, tipo MIME, formato immagine reale, dimensioni minime 1000 px sul lato lungo e 500 px sul lato corto. Le immagini non conformi vengono escluse.
- Le immagini restano attribuite agli editori originali; la verifica tecnica non equivale a una licenza di riutilizzo.

## Funzioni

- Ricerca e filtri per categoria.
- Schede editoriali interne con immagini responsive e caricamento differito.
- Fonti e attribuzioni alla fine di ogni scheda, senza reindirizzamento automatico.
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

## Account, feed personale e preferiti

L'interfaccia account usa Supabase Auth e il database Supabase. Il sito statico non conserva password e non contiene chiavi segrete.

### Attivazione richiesta

1. Crea un progetto gratuito su https://supabase.com/ .
2. In **SQL Editor** del progetto, apri il file `supabase-setup.sql` presente nel repository, copia tutto il contenuto ed eseguilo una sola volta.
3. In **Project Settings → API** (o **Connect**), copia Project URL e la chiave pubblica **anon/publishable**. Non usare mai la chiave `service_role` o una secret key nel browser.
4. Apri `supabase-config.js` nel repository e sostituisci i due valori segnaposto:
   - `url`: Project URL Supabase;
   - `anonKey`: chiave pubblica anon/publishable.
5. In **Authentication → URL Configuration**, imposta come Site URL:
   `https://manuelamodeo26-dev.github.io/atelier-magazine/`
   e aggiungi lo stesso indirizzo tra i Redirect URLs.
6. In **Authentication → Providers → Email**, abilita Email. Per maggiore sicurezza lascia attiva la conferma dell'indirizzo email.

Il file SQL crea profili, preferenze e preferiti e attiva Row Level Security: ogni utente può leggere e modificare esclusivamente i propri record. Le chiavi pubbliche sono utilizzabili dal browser; la sicurezza dei dati è affidata alle policy RLS. Non pubblicare mai credenziali private.

Finché URL e chiave pubblica non vengono configurati, il pulsante account mostra l'avviso di configurazione e registrazione/accesso non sono attivi. Il feed generale e la lettura degli articoli restano disponibili senza account.
