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

Fonti configurate in `scripts/fetch_news.py`: Vogue Italia, Pambianco, AD Italia, Exibart, Finestre sull'Arte, Outpump e Sneakers Magazine. Le ultime due ampliano soprattutto la copertura di sneakers, streetwear e cultura pop. Le immagini mancanti nel feed vengono cercate nei metadati Open Graph delle pagine originali, con un numero limitato di richieste. La disponibilità effettiva di ogni feed può cambiare. Un filtro editoriale esclude alcune rubriche generiche fuori tema (per esempio oroscopi e contenuti sanitari generalisti); le notizie vengono inoltre assegnate a sezioni più specifiche in base a titolo e descrizione. Questi controlli automatici aiutano la selezione, ma non sostituiscono una verifica redazionale.

## Aggiornamento e pubblicazione

- **Update ATELIER news**: esecuzione programmata ogni 6 ore e avvio manuale da GitHub Actions.
- Il processo conserva l'archivio se le fonti non rispondono, elimina i contenuti non italiani e quelli più vecchi di 120 giorni e rimuove i duplicati tramite URL.
- Ogni aggiornamento registra per ciascun feed lo stato di risposta, il numero di articoli letti e, in caso di errore, il messaggio tecnico essenziale. È così possibile distinguere una fonte non raggiungibile da un feed valido senza nuove notizie e diagnosticare il problema.
- **Deploy ATELIER to GitHub Pages**: pubblicazione del sito statico.
- In **Settings → Pages**, la sorgente deve essere **GitHub Actions**.

La raccolta RSS non equivale a una verifica giornalistica: controllare sempre notizie, attribuzioni e diritti di utilizzo prima della pubblicazione.

## Controlli automatici prima della pubblicazione

Ogni pubblicazione tramite GitHub Pages passa prima da una verifica automatica:

- test unitari del generatore delle sintesi editoriali;
- controllo dell'integrità dell'archivio JSON e dell'assenza di URL duplicati;
- verifica del formato delle sintesi (4–6 paragrafi e intervalli di parole previsti);
- controllo dei metadati delle immagini marcate come verificate, con soglie di risoluzione applicate al lato lungo e al lato corto;
- controllo della sintassi JavaScript prima del deploy.

Se un controllo bloccante fallisce, la pubblicazione non procede. Un feed temporaneamente indisponibile viene invece segnalato come avviso: non blocca la pubblicazione delle notizie già valide.

## Lettura e verifica editoriale

- Ogni articolo si apre in una scheda interna: titolo, categoria, data, editore, autore quando disponibile e descrizione estesa ricavata dai contenuti RSS/Atom e dai metadati pubblici della fonte. Il raccoglitore privilegia il testo più informativo disponibile e arricchisce anche gli articoli già archiviati quando la fonte pubblica una descrizione migliore.
- Le fonti sono raccolte in fondo alla scheda. Il collegamento esterno è facoltativo e viene aperto solo se il lettore lo seleziona.
- ATELIER non ripubblica integralmente articoli protetti o contenuti paywall: mostra le informazioni e le sintesi effettivamente disponibili nei feed e nei metadati pubblici, senza inventare dettagli.
- Le fotografie vengono verificate prima della pubblicazione: risposta HTTP, tipo MIME, formato immagine reale, dimensioni minime 1000 px sul lato lungo e 500 px sul lato corto. Le immagini non conformi vengono escluse.
- Le immagini restano attribuite agli editori originali; la verifica tecnica non equivale a una licenza di riutilizzo.

## Redazione e sintesi editoriali ATELIER

Quando è configurato il secret GitHub Actions `GROQ_API_KEY`, il raccoglitore può creare una sintesi originale in italiano a partire dal titolo, dal testo disponibile nel feed e dal testo leggibile della pagina pubblica della fonte.

ATELIER usa l'API Chat Completions di Groq con il modello `openai/gpt-oss-120b`; se il modello raggiunge un limite temporaneo o di utilizzo, prova `openai/gpt-oss-20b`. Le richieste usano la modalità JSON e la risposta viene validata prima di essere salvata. I limiti del piano gratuito sono stabiliti da Groq, possono cambiare e si applicano per modello e per finestra temporale: consulta la dashboard del tuo account. Il piano gratuito non garantisce disponibilità illimitata.

- Notizie standard: 300–400 parole, in 4–6 paragrafi.
- Approfondimenti: 450–600 parole, in 4–6 paragrafi, soltanto quando il materiale contiene dettagli sufficienti.
- Le sintesi vengono mostrate separatamente dalla descrizione originale dell'editore.
- Se la fonte è troppo breve, il modello non risponde, il limite è raggiunto o il secret manca, resta visibile il testo originale: non vengono inventati contenuti.
- Vengono elaborate al massimo sei schede per esecuzione, dando priorità alle notizie nuove e poi recuperando gradualmente l'archivio. Se i limiti di entrambi i modelli sono raggiunti, il processo sospende le richieste AI per quella esecuzione.
- Le sintesi sono conservate in `data/articles.json`; il testo integrale della pagina sorgente non viene salvato.

### Configurazione facoltativa dell'AI

1. Crea un account gratuito su [GroqCloud](https://console.groq.com/) e genera una API key.
2. Nel repository GitHub apri **Settings → Secrets and variables → Actions → New repository secret**.
3. Inserisci come nome `GROQ_API_KEY` e incolla il valore della chiave nel campo secret.
4. Salva. La chiave viene letta soltanto da GitHub Actions e non viene inserita nel sito o nel repository.

Senza il secret il sito e la raccolta RSS continuano a funzionare normalmente, ma le sintesi editoriali AI non vengono generate. Verifica quote e condizioni del piano gratuito nel tuo account Groq. Non inserire mai la chiave in un file del progetto o in una chat.

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

Il progetto è collegato al database Supabase tramite una publishable key, destinata al browser. La protezione dei dati personali è applicata tramite Row Level Security (RLS): ogni utente può leggere e modificare esclusivamente i propri record.

### Impostazioni di autenticazione

In **Authentication → URL Configuration**, imposta come Site URL:
`https://manuelamodeo26-dev.github.io/atelier-magazine/`
e aggiungi lo stesso indirizzo tra i Redirect URLs.

In **Authentication → Providers → Email**, abilita Email. Per maggiore sicurezza lascia attiva la conferma dell'indirizzo email.

Gli account permettono registrazione e accesso con email e password, feed personale per argomenti, preferiti persistenti e Mi piace con conteggi condivisi. I preferiti restano visibili anche quando un articolo esce dall'archivio corrente di 120 giorni, conservando la scheda salvata e il collegamento alla fonte. Il primo accesso crea automaticamente profilo e preferenze predefinite.


## ATELIER Community

La community è disponibile in `community.html` e usa lo stesso progetto Supabase degli account del magazine.

- Discussioni pubbliche per Fashion Talk, Streetwear, Design & Creativity, Arte & Cultura, Fashion Industry, Your Style e Off Topic.
- Pubblicazione e commenti riservati agli utenti autenticati.
- Reazioni, segnalazioni e rimozione dei propri contenuti.
- Pannello segnalazioni visibile agli account con `app_metadata.role = "admin"`.
- Row Level Security attiva su tutte le tabelle della community; nessuna chiave privilegiata è esposta al browser.
- Limiti lato database: una nuova discussione al minuto e un commento ogni cinque secondi per account.
- I nomi degli autori sono volutamente minimizzati nella prima versione: gli altri utenti vedono "Membro ATELIER".

Tabelle Supabase: `community_discussions`, `community_comments`, `community_reactions`, `community_reports`.

Per abilitare la moderazione amministrativa, assegna il ruolo `admin` all'utente autorizzato tramite **Supabase Dashboard → Authentication → Users → utente → Edit app metadata**. Non usare `user_metadata` per i privilegi. Mantieni questo ruolo soltanto su account redazionali fidati.

La community è inizialmente senza messaggi privati e senza caricamento immagini: queste funzioni vanno introdotte solo dopo aver definito ulteriori strumenti di privacy e moderazione.
