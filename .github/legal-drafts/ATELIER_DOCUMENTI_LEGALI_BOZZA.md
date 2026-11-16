# ATELIER — Documenti legali (bozza interna)

> **STATO: BOZZA NON PUBBLICABILE.** Questo documento serve a preparare la documentazione del sito. Non è una Privacy Policy o un contratto definitivo e non deve essere collegato nel footer finché i punti bloccanti non sono verificati. La denominazione pubblica scelta è **ATELIER** e il recapito indicato è **atelierverse26@gmail.com**. La denominazione del progetto non sostituisce automaticamente l'identificazione giuridica del titolare del trattamento.

---

# 1. Informativa sul trattamento dei dati personali — bozza

**Ultimo aggiornamento della bozza:** 16 novembre 2026  
**Sito:** https://manuelamodeo26-dev.github.io/atelier-magazine/

## 1.1 Chi gestisce il sito e chi è il titolare

Il progetto editoriale è presentato al pubblico con la denominazione **ATELIER**.  
Contatto per richieste relative alla privacy: **atelierverse26@gmail.com**.

**Punto bloccante prima della pubblicazione:** deve essere indicato in modo giuridicamente corretto il titolare effettivo del trattamento (persona fisica o soggetto giuridico, con i dati identificativi richiesti). La sola denominazione «ATELIER» e un indirizzo email non sono sufficienti, se non corrispondono a un soggetto giuridico identificabile. Non pubblicare questa bozza come informativa definitiva finché il punto non è risolto.

## 1.2 Quali dati possono essere trattati

In base alle funzioni attualmente presenti nel codice e nel database, possono essere trattati:

- **Account e autenticazione:** indirizzo email, identificativo utente, credenziali gestite da Supabase Auth e informazioni tecniche della sessione. Il sito non conserva direttamente le password in un proprio database applicativo.
- **Profilo:** nickname pubblico, data di creazione del profilo e, se inseriti dall'utente, biografia, città/paese, sito web, nome Instagram e URL dell'avatar.
- **Preferenze e attività personali:** categorie selezionate, raccolte personali, articoli salvati, reazioni/like e voti ai sondaggi, ove la relativa funzione è utilizzata.
- **Community:** titoli e testi delle discussioni, commenti e risposte, categoria, date di creazione/modifica, reazioni e identificativi tecnici associati agli account.
- **Segnalazioni e moderazione:** motivo e dettagli facoltativi della segnalazione, contenuto e identificativo del contenuto segnalato, stato della segnalazione e informazioni necessarie alla gestione da parte dei moderatori.
- **ATELIER Lab e proposte editoriali:** messaggi o testi inviati dagli utenti, proposte di articoli, URL, note e stato della revisione, se tali funzioni sono utilizzate.
- **Dati tecnici:** informazioni necessarie al funzionamento e alla sicurezza del sito e dei servizi di hosting/autenticazione. Le categorie esatte, i log raccolti e i relativi tempi di conservazione devono essere confermati con i fornitori.

Non inserire nei campi pubblici dati personali delicati, credenziali, documenti, indirizzi privati o informazioni di terzi.

## 1.3 Per quali finalità

I dati possono essere utilizzati, nei limiti delle funzioni effettivamente attive, per:

1. creare e gestire account, autenticazione e profili;
2. salvare preferenze, raccolte e contenuti scelti dall'utente;
3. consentire discussioni, commenti, risposte, reazioni e sondaggi;
4. ricevere e gestire segnalazioni, prevenire abusi e moderare i contenuti;
5. gestire le proposte editoriali e le funzioni collaborative;
6. mantenere sicurezza, integrità e disponibilità del servizio;
7. generare sintesi editoriali o analisi di moderazione mediante servizi AI esterni, quando tali integrazioni sono configurate e utilizzate.

**Punto bloccante:** per ciascuna finalità il titolare deve determinare e documentare la corretta base giuridica ai sensi del GDPR (ad esempio esecuzione del servizio richiesto, obbligo di legge, legittimo interesse adeguatamente valutato o consenso quando necessario). Non si deve copiare una base giuridica standard senza una valutazione concreta.

## 1.4 Servizi e soggetti terzi

Dall'architettura del progetto risultano i seguenti servizi o collegamenti esterni:

- **GitHub Pages / GitHub:** distribuzione del sito statico e automazioni editoriali del repository.
- **Supabase:** autenticazione, database e funzioni serverless utilizzate da account e community.
- **Groq e Google Gemini:** provider AI potenzialmente utilizzati per sintesi editoriali e analisi di moderazione. Il codice prevede queste integrazioni, ma la presenza e l'effettivo utilizzo delle chiavi di servizio non sono stati verificati.
- **Google Fonts:** caricamento di caratteri tipografici da infrastruttura Google.
- **Editori e CDN delle immagini:** il sito carica collegamenti a immagini e contenuti distribuiti dalle fonti editoriali originali.

I fornitori possono trattare dati tecnici secondo i propri ruoli, accordi e informative. Prima della pubblicazione occorre verificare i contratti/accordi sul trattamento, i ruoli privacy, i sub-responsabili, i trasferimenti internazionali e le garanzie applicabili. La regione del progetto Supabase è stata verificata come **eu-west-1 (Irlanda)**. Il piano dell'organizzazione è Free. La configurazione effettiva dei provider AI non è stata verificata: i secret non sono leggibili tramite gli strumenti disponibili e non devono essere esposti.

## 1.5 Funzioni di intelligenza artificiale

Le automazioni editoriali possono inviare a un provider AI il titolo, il testo disponibile nel feed e il testo leggibile della pagina pubblica della fonte per produrre una sintesi. Il progetto dichiara di conservare la sintesi e non il testo integrale della pagina sorgente.

ATELIER Ghost è una funzione riservata agli amministratori che può inviare al provider configurato il testo sottoposto ad analisi e il contesto fornito dal moderatore. Ghost restituisce un supporto valutativo: non applica autonomamente sanzioni e non modifica i contenuti.

Prima dell'attivazione o dell'uso di tali funzioni, il titolare deve verificare quali provider sono configurati, quali dati vengono trasmessi, le condizioni contrattuali, i tempi di conservazione e l'eventuale trasferimento fuori dallo Spazio Economico Europeo. Evitare di inserire dati personali non necessari nei prompt.

## 1.6 Visibilità dei contenuti

Le discussioni e i commenti pubblicati nella community sono visibili pubblicamente. Il nickname e i campi del profilo scelti dall'utente possono essere mostrati agli altri visitatori. Email e credenziali non devono essere esposte nel profilo pubblico. Gli utenti devono evitare di pubblicare informazioni personali proprie o di terzi.

## 1.7 Conservazione

I dati sono conservati per il tempo necessario alle finalità per cui sono trattati, nel rispetto degli obblighi applicabili e delle esigenze documentate di sicurezza e moderazione.

**Punto bloccante:** questa formulazione generale non sostituisce un piano di conservazione. Prima della pubblicazione occorre stabilire periodi o criteri concreti per account inattivi, profili, discussioni, commenti rimossi/archiviati, segnalazioni, log tecnici, backup e dati trattati dai provider AI. Non sono stati inventati periodi in questa bozza perché non risultano verificati.

## 1.8 Diritti delle persone

Nei casi e nei limiti previsti dal GDPR, l'interessato può chiedere accesso, rettifica, cancellazione, limitazione, portabilità, opposizione e revoca del consenso, ove il trattamento si basi sul consenso. È inoltre possibile proporre reclamo al Garante per la protezione dei dati personali.

Le richieste possono essere inviate a **atelierverse26@gmail.com**. Prima della pubblicazione il titolare deve predisporre una procedura effettiva per verificare le richieste, rispondere nei termini previsti e gestire la cancellazione o esportazione dei dati anche presso i fornitori, quando applicabile.

## 1.9 Cookie, archiviazione locale e strumenti tecnici

Il progetto utilizza funzionalità tecniche del browser per sessioni di autenticazione, preferenze di accesso e cache del sito/PWA. Il codice include inoltre il caricamento di Google Fonts e contenuti/immagini da domini esterni.

**Verifica statica parziale (16 novembre 2026):** sono stati analizzati 12 file HTML/JavaScript del repository. Il codice contiene uso di localStorage/sessionStorage per preferenze di sessione e navigazione, service worker/PWA e caricamento di Google Fonts da domini Google. Nella scansione dei file esaminati non sono emersi riferimenti a Google Analytics, Meta Pixel, Hotjar o Microsoft Clarity. Questa scansione non rileva necessariamente cookie impostati a runtime dai provider, richieste indirette, header HTTP o comportamenti del browser. **Punto bloccante:** eseguire un'ispezione runtime su browser pulito, prima e dopo login, e verificare cookie, storage, richieste di rete e provider. Solo allora si potrà stabilire se e quale banner o gestione del consenso sia necessario. Non dichiarare «nessun cookie» sulla base della sola scansione statica.

## 1.10 Minori

Prima di consentire l'iscrizione di minori occorre definire una disciplina coerente con l'età degli utenti, il tipo di servizio, le regole applicabili in Italia e le misure di tutela della community. L'età minima e gli eventuali requisiti di consenso/assistenza genitoriale devono essere definiti e implementati prima del lancio pubblico.

## 1.11 Modifiche

L'informativa definitiva dovrà riportare la data di aggiornamento e descrivere le modifiche sostanziali al trattamento.

---

# 2. Termini di utilizzo e regole della community — bozza

**STATO: BOZZA NON PUBBLICABILE FINCHÉ I PUNTI BLOCCANTI NON SONO RISOLTI.**

## 2.1 Ambito

ATELIER è un progetto editoriale digitale dedicato a moda, design, arte e cultura contemporanea. Il sito mette a disposizione contenuti editoriali, strumenti di consultazione e, ove attivi, account personali e funzioni community.

## 2.2 Account

L'utente è responsabile della correttezza delle informazioni fornite e della riservatezza delle proprie credenziali. Non è consentito utilizzare account altrui, impersonare altre persone o tentare di aggirare i controlli di sicurezza. Il nickname della community deve rispettare le regole mostrate nell'interfaccia e non deve essere ingannevole o offensivo.

## 2.3 Regole di comportamento

Nella community non sono ammessi:
- minacce, molestie, discriminazioni, odio o attacchi personali;
- spam, truffe, pubblicità insistente o account ingannevoli;
- pubblicazione non autorizzata di dati personali o immagini private;
- contenuti illeciti, diffamatori o che violino diritti altrui;
- violazioni del diritto d'autore o condivisione di materiali senza i necessari diritti;
- tentativi di compromettere il sito, gli account o i servizi.

Le critiche devono riguardare le idee e i contenuti, non la dignità delle persone. Gli utenti devono segnalare contenuti problematici e non pubblicare credenziali o informazioni riservate.

## 2.4 Contenuti degli utenti

L'utente mantiene i diritti sui contenuti che crea, nei limiti dei diritti di terzi. Pubblicando un contenuto, l'utente rende il contenuto visibile secondo le impostazioni e le caratteristiche della funzione utilizzata.

**Punto bloccante:** prima della pubblicazione definitiva deve essere definita in modo proporzionato e chiaro la licenza concessa ad ATELIER per ospitare, mostrare, moderare, riprodurre tecnicamente e distribuire i contenuti necessari al funzionamento del servizio. Non viene introdotta in questa bozza una cessione generale dei diritti.

L'utente dichiara di avere i diritti o le autorizzazioni necessari per pubblicare i materiali e di non violare diritti di terzi.

## 2.5 Moderazione

ATELIER può esaminare le segnalazioni e intervenire sui contenuti che violano le regole, anche nascondendoli, archiviandoli o rimuovendoli secondo le funzioni disponibili. Le decisioni di moderazione sono umane. Gli strumenti AI eventualmente utilizzati hanno funzione di supporto e non decidono autonomamente sanzioni o rimozioni.

**Punto bloccante:** definire criteri, tempi di gestione delle segnalazioni, durata delle limitazioni, procedura di contestazione e canale di ricorso.

## 2.6 Contenuti editoriali e fonti

I contenuti di terzi restano attribuiti ai rispettivi editori e titolari. I collegamenti alle fonti originali sono forniti per consentire la consultazione. La presenza di un'immagine o di un testo in un feed pubblico non costituisce automaticamente autorizzazione alla ripubblicazione. ATELIER deve pubblicare immagini e materiali solo dopo aver verificato i diritti o una base legittima per il loro utilizzo.

## 2.7 Disponibilità e sicurezza

Il servizio può essere aggiornato, sospeso o reso temporaneamente indisponibile per manutenzione, sicurezza o interventi tecnici. Nessuna clausola di questa bozza limita i diritti inderogabili riconosciuti agli utenti dalla legge.

## 2.8 Segnalazioni e contatti

Per questioni relative alla community o ai contenuti è possibile utilizzare gli strumenti di segnalazione disponibili sul sito. Per richieste generali e privacy: **atelierverse26@gmail.com**.

## 2.9 Legge applicabile e controversie

**Punto bloccante:** la legge applicabile, il foro competente e le informazioni obbligatorie devono essere definiti in base all'identità e alla natura giuridica del gestore, al pubblico a cui il servizio si rivolge e alle norme inderogabili applicabili. Non vengono indicati in questa bozza per non inventare una qualificazione giuridica.

---

# 3. Checklist obbligatoria prima della pubblicazione

- [ ] Identificare correttamente il titolare del trattamento e la sua forma giuridica. «ATELIER» può restare la denominazione pubblica, ma non va presentata come soggetto giuridico se non lo è.
- [x] Regione Supabase verificata: eu-west-1 (Irlanda).
- [ ] Confermare hosting, sub-responsabili e accordi sul trattamento.
- [ ] Verificare quali secret AI sono effettivamente configurati in GitHub e Supabase; registrare i provider realmente utilizzati.
- [ ] Definire basi giuridiche per ogni finalità.
- [ ] Definire periodi di conservazione e procedura di cancellazione per ogni categoria di dati.
- [x] Scansione statica iniziale di 12 file HTML/JS: Google Fonts e storage locale/sessione rilevati; nessun riferimento ai tracker elencati nella scansione.
- [ ] Verificare cookie, storage, service worker e richieste di terze parti in browser reale.
- [ ] Definire regole per utenti minorenni.
- [ ] Definire licenza dei contenuti community, procedura di moderazione e ricorso.
- [ ] Verificare licenze/permessi per immagini e altri materiali editoriali.
- [ ] Far revisionare i documenti definitivi da un professionista competente in materia privacy/consumeristica.
- [ ] Solo dopo la revisione, creare le pagine pubbliche, collegarle nei footer e aggiungere eventuali checkbox/consensi richiesti.

## 4. Verifiche tecniche già eseguite per preparare la bozza

- Schema Supabase consultato per profili, preferenze, community, segnalazioni, raccolte, proposte e sondaggi.
- Codice del sito consultato per autenticazione, profilo, community e integrazioni AI.
- Funzione Supabase `atelier-ghost` rilevata come attiva (versione 9); ciò non dimostra che le chiavi dei provider AI siano configurate o che l'analisi sia operativa.
- Advisor Supabase: avviso sulla protezione password compromesse disattivata; 13 indici inutilizzati segnalati come informazioni di performance. Nessuna modifica a pagamento è stata effettuata.
- Nessun test manuale completo su browser reale è stato eseguito in questa sessione.


---

# 5. Appendice tecnica — controlli effettuati il 16 novembre 2026

- **Supabase:** progetto in stato ACTIVE_HEALTHY, regione eu-west-1 (Irlanda), PostgreSQL 17.11, organizzazione su piano Free.
- **Ghost:** Edge Function atelier-ghost attiva, versione 9, verify_jwt=true; il codice verifica anche app_metadata.role === "admin", accetta Groq e Gemini come provider alternativi e restituisce un errore esplicito se entrambi i secret mancano.
- **Ghost non collaudato end-to-end:** non è stato possibile leggere i valori/segnali di configurazione dei secret né invocare la funzione con una sessione admin valida. Nessun log della Edge Function è risultato nella finestra di log consultata. La presenza della funzione non dimostra che i provider AI siano configurati.
- **Migrazioni:** inizialmente erano presenti 5 file su 25. Ho recuperato le 20 migrazioni mancanti leggendo gli statement originali conservati in `supabase_migrations.schema_migrations` e li ho ripristinati nel repository senza riapplicarli al database. Verifica finale: 25 file SQL nel repository per 25 migrazioni registrate nel database, nessun file mancante e nessun file orfano. I file ripristinati vanno comunque sottoposti a revisione e mantenuti in ordine di versione.
- **Advisor sicurezza:** un avviso, protezione password compromesse disattivata. Non è stato eseguito alcun upgrade.
- **Advisor prestazioni:** 13 indici segnalati come mai usati; nessuno rimosso perché i dati di utilizzo possono essere incompleti su un progetto giovane e alcuni indici servono a query future o vincoli.
- **Advisor health:** nessun avviso restituito.
- **Accessibilità del sito live:** i tentativi di apertura automatica delle pagine pubbliche non sono riusciti; il deploy GitHub Actions è riuscito, ma non è stato eseguito un collaudo visivo/browser.
- **Diritti immagini:** nessuna licenza o autorizzazione di riutilizzo è stata verificata. La verifica tecnica del caricamento delle immagini non prova il diritto di pubblicazione.
