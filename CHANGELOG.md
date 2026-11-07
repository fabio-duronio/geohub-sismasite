# Changelog

## Non rilasciato

**Stampa A4 per la relazione**
- Nuovo layout di stampa A4 pensato come allegato: frontespizio con titolo e riferimenti normativi, sezioni numerate (1. Dati del sito, 2. Parametri, 3. Spettri, 4. Inquadramento sismico, 5. Note metodologiche e fonti), tabella dei dati del sito, mappa centrata sul sito con legenda MPS04 a lato e didascalia (Figura 1).
- Intestazione con sito/commessa e data del calcolo; piè di pagina con riferimento dell'allegato, «pag. x di y» e versione (Chrome/Edge). Nuovo campo «Riferimento dell'allegato» (predefinito «Allegato E1»).
- Stile da relazione: Arial, testo giustificato, tabelle con bordi sottili e intestazioni colorate.
- Nuova casella «Includi in stampa gli elenchi completi dei cataloghi» (disattivata in partenza): senza la spunta la sezione 4 riporta solo la sintesi di eventi strumentali, storia sismica e terremoti storici; le faglie ITHACA sono sempre elencate. Con la spunta gli elenchi sono stampati per intero in formato compatto.
- Mappa in stampa a dimensione fissa (135 × 100 mm), centrata sul segnaposto.
- Il pulsante «Stampa / Salva PDF» ridisegna mappa e grafici alla larghezza della pagina A4 e attende il caricamento della mappa prima di aprire la stampa.

**Formato dei numeri e grafici**
- Virgola decimale in tutti i valori mostrati (tabelle, indicatori, coordinate, assi e suggerimenti dei grafici).
- Tabella degli stati limite: F_0 con 3 decimali, come nelle altre tabelle e negli indicatori.
- Asse dei periodi degli spettri con etichette e griglia ogni 0,5 s.
- Sottotitoli degli spettri con lo stato limite rappresentato (es. «stato limite SLV»).

**Documentazione**
- README: P_VR degli stati limite riferita alla Tab. 3.2.I delle NTC 2018 (prima indicata per errore come Tab. 2.5.I).

- Immagine di anteprima del link (`assets/og-image.png`) aggiornata con il nuovo indirizzo in minuscolo `fabio-duronio.github.io/geohub-sismasite` (il vecchio indirizzo non viene reindirizzato). Già attiva sul sito pubblicato; entrerà nella prossima release.

## 1.7.0 — 2026-11-06

Nuova impaginazione e carta di pericolosità INGV. I parametri calcolati non cambiano (verifiche `verifica_numeri.py` e `verifica_indipendente.py` superate).

**Impaginazione**
- Mappa in primo piano, grande, accanto al pannello di input (sotto i 1000 px di larghezza la mappa va in cima).
- Barra dello stato limite con pulsanti SLO, SLD, SLV, SLC e valori principali sempre in vista: `T_R`, `a_g`, `F_0`, `T*_C`, S, `a_max`.
- Risultati in tre schede: Parametri, Spettri, Inquadramento sismico (navigabili da tastiera). In stampa compaiono tutte, una dopo l'altra.
- Su telefono e tablet le tabelle restano dentro il proprio riquadro: il testo va a capo tra le parole, le tabelle lunghe scorrono in orizzontale al loro interno; le schede restano su una riga. Nella scheda Inquadramento le sezioni non hanno più un riquadro interno, così hanno la stessa larghezza delle altre schede.
- Nel pannello del sito: coordinate ED50 e comune con zona sismica, aggiornati a ogni calcolo.
- Grafica rinnovata (caratteri IBM Plex, colori e spaziature); screening di liquefazione in un riquadro richiudibile.

**Mappa**
- Carta di `a_g` del modello INGV MPS04 dal servizio WMS ufficiale (Meletti et al., 2006, CC BY 4.0): 9 periodi di ritorno (predefinito `T_R` = 475 anni, cioè 10 % in 50 anni, il livello della mappa di riferimento nazionale) e percentili 16°/50°/84°, legenda ufficiale, opacità regolabile. Segue lo stato limite selezionato (livello con `T_R` più vicino), oppure si sceglie a mano. È un inquadramento visivo: il calcolo usa il reticolo.
- Basi cartografiche a scelta: stradale (OpenStreetMap) e satellitare (Esri). La carta di pericolosità resta visibile sopra entrambe.
- Vertici della maglia del reticolo usati nell'interpolazione, riportati da ED50 a WGS84, con ID e distanza.
- Legenda della carta in un riquadro proprio in basso a destra, richiudibile (sul telefono parte chiusa e si alterna al pannello dei livelli). La legenda occupa solo lo spazio libero sotto il pannello dei livelli e scorre al suo interno: i due riquadri non si sovrappongono. Il pannello dei livelli si può ridurre su ogni schermo.
- Blocco della mappa: rotella disattivata sul computer e trascinamento disattivato sul telefono finché non si tocca il lucchetto, per non spostare la mappa scorrendo la pagina. Scala grafica.

**App future**
- I testi dell'app non citano più i nomi provvisori delle future app GeoHub, ancora in progetto: k_h, k_v e lo screening di liquefazione sono indicati come destinati a future app dedicate.

**Pericolosità di base per i 9 periodi di ritorno**
- Tabella di `a_g`, `F_0`, `T*_C` del sito per i 9 `T_R` del reticolo e spettri elastici su suolo A, T1, come la Fase 1 del foglio Spettri-NTC del CSLP.

## 1.6.0 — 2026-11-05

**Disaggregazione rimossa da SismaSite**
- Il pannello con i campi manuali M, R, ε è stato eliminato: la disaggregazione non entra nella definizione della pericolosità sismica di base (parametri `a_g`, `F_0`, `T*_C`, spettri NTC) e i valori inseriti non venivano usati in alcun calcolo. Per la relazione il riferimento è il report ufficiale del nodo dall'applicazione INGV esse1-gis (modello MPS04-S1; Spallarossa e Barani 2007, Progetto DPC-INGV S1, Deliverable D14), da allegare così com'è.
- La disaggregazione sarà gestita nell'app che usa la magnitudo (es. GeoHub-LiquiSite, fattore di scala della magnitudo).
- Verificati e non adottati per SismaSite i servizi INGV/ESM REXEL (valori modali, distanza Joyner-Boore, 4 `T_R`) e BMSE (scenario per la selezione di accelerogrammi): da rivalutare nelle app successive.
- Rimosso dal foglio di stile di stampa il codice della matrice di disaggregazione eliminata nella 1.5.0.

**Altre modifiche (già su main)**

- README: corretti un errore di sintassi nel riquadro «Cos'è e cosa non è» e uno spazio iniziale; la struttura del progetto elenca tutti i file (anche `assets/`, `NOTICE`, modelli delle segnalazioni), raggruppati per funzione.
- Codice: rimossi un import inutilizzato in `convert_grid.py` e una funzione mai usata in `convert_classificazione.py`.
- Titolo della pagina, titolo per la condivisione (`og:title`) e sottotitolo nell'intestazione: «Parametri sismici del sito» al posto di «Analisi sismica del sito», che poteva far pensare a un'analisi di risposta sismica locale.
- README: il riquadro «Cos'è e cosa non è» elenca anche gli spettri di progetto, che l'app calcola; tolta la frase che diceva il contrario.
- Nomi provvisori delle app future: **GeoHub-LiquiSite** (screening di liquefazione) e **GeoHub-SoilSite** (coefficienti k_h, k_v per i pendii), al posto di GeoHub-Liquefazione e GeoHub-Versanti.
- **Nuovi indirizzi in minuscolo**: repository `github.com/fabio-duronio/geohub-sismasite`, app `fabio-duronio.github.io/geohub-sismasite/`. I vecchi link al repository vengono reindirizzati da GitHub; il vecchio indirizzo di GitHub Pages (`/GeoHub-SismaSite/`) non viene reindirizzato. Aggiornati README, NOTICE e i metadati di condivisione (`og:url`, `og:image`) di `index.html`.

## 1.5.1 — 2026-11-04

Revisione a seguito di una verifica esterna del codice. Sui 7 punti di controllo del README i parametri restano invariati entro gli arrotondamenti mostrati.

**Calcolo**
- **Datum**: le coordinate WGS84 inserite sono convertite in ED50, il datum del reticolo, prima dell'interpolazione (Molodensky ridotta, EPSG:1133). Prima non c'era conversione: scarto di circa 100–150 m, con effetto su `a_g` in genere < 0,2 % e fino al 2–3 % in zone a forte gradiente. Il report mostra le coordinate in entrambi i datum.
- **Ordine dell'interpolazione** allineato all'Allegato A e a Spettri-NTC: interpolazione in `T_R` su ciascun vertice della maglia, poi media pesata spaziale (prima era l'inverso). Scarto rispetto alla 1.5.0 < 0,06 % su 1.500 siti.
- **Minimo `S_d ≥ 0,2·a_g`** applicato solo agli spettri ridotti con `q > 1` (§3.2.3.5): con `q = 1`, e quindi sempre per lo SLO, lo spettro di progetto coincide con l'elastico (§3.2.3.4). Prima il minimo era applicato anche allo SLO.
- **Clamp di sicurezza su `T*_C`** abbassato da 0,10 a 0,05 s: il reticolo ufficiale contiene `T*_C` = 0,095 s a `T_R` = 30 anni in 24 nodi (Alto Adige), che venivano alterati del +5 %.

**Interfaccia**
- Avviso nel riquadro principale quando il punto è in mare (fuori da ogni comune e oltre 2 km dal più vicino), anche se ricade nell'area di un'isola della Tabella 2.
- Corretto l'overflow orizzontale su mobile della riga dei filtri (sezione eventi).

**Documentazione e verifiche**
- README allineato al codice: per `a_g` > 0,4 g `k_h`, `k_v` non sono calcolati (il README citava ancora β_s = 0,36 / 0,32, rimosso nella 1.5.0).
- Nuovo `verifica_allegato_b.py`: confronto con il PDF ufficiale del D.M. 14/01/2008. I 10.751 nodi di `grid-data.json` coincidono con la Tabella 1 entro l'arrotondamento della stampa; i 5 gruppi della Tabella 2 (isole) sono identici.
- Nuovo `verifica_indipendente.py`: ricalcolo dell'intera catena in Python puro su 60 siti e confronto con l'app nel browser; il README distingue ora verifica dei dati, verifica indipendente e non regressione.

## 1.5.0 — 2026-11-03

Nuova sezione **Inquadramento sismico del sito** e due correzioni. I parametri di pericolosità di base (`a_g`, `F_0`, `T*_C`), gli spettri e i coefficienti di amplificazione non cambiano (verificato su 7 punti di controllo rispetto alla 1.4.1).

**Correzioni**
- **Disaggregazione**: eliminata la stima automatica di M_w, R, ε (regole empiriche dall'`a_g`) con il grafico e la matrice sintetici, che non erano dati INGV. Restano i campi per inserire a mano i valori del report ufficiale INGV-DPC, con un campo per la fonte.
- **Coefficienti k_h, k_v**: per `a_g` > 0,4 g l'app usava β_s = 0,36 (categoria A) e 0,32 (B–E), valori non previsti dalla Tab. 7.11.I delle NTC 2018 (verificata sul testo in G.U.). Ora oltre 0,4 g k_h e k_v non sono calcolati e un avviso lo spiega.

**Nuove funzioni**
- **Comune e classificazione sismica**: comune individuato automaticamente dai confini ISTAT al 1° gennaio 2026 (conferma richiesta entro 200 m dal confine); zona dall'elenco DPC "Classificazione sismica aggiornata a maggio 2025", con le sottozone regionali così come pubblicate e avviso per i comuni divisi in più sottozone. Solo fini programmatori e amministrativi.
- **Eventi sismici strumentali nel raggio**: servizio FDSN dell'INGV in tempo reale; predefiniti raggio 30 km, M ≥ 2,5, dal 1985 (modificabili); tipo di magnitudo per ogni evento; avvertenza sulla completezza del catalogo.
- **Storia sismica della località** (DBMI15 v4.0): località più vicina proposta automaticamente, con alternative entro 10 km; tutte le osservazioni, codici di intensità spiegati.
- **Terremoti storici con epicentro nel raggio** (CPTI15 v4.0).
- **Faglie attive e capaci** (ISPRA ITHACA) entro un raggio di ricerca non normativo (predefinito 10 km), ordinate per distanza, con cinematica, ultima attività e scheda ISPRA; tracce sulla mappa, nessuna fascia di rispetto; rimando alle Linee guida FAC (2015).
- Nuovi file dati e script: `classificazione-data.json`, `comuni-data.json`, `storica-data.json`; `convert_classificazione.py`, `convert_comuni.py`, `convert_storica.py`, `verifica_dati.py`. I file dati si caricano solo quando servono.

**Note**
- Lo screening di liquefazione e i coefficienti k_h, k_v restano, con l'indicazione che passeranno alle app GeoHub-Liquefazione e GeoHub-Versanti.
- NOTICE e README aggiornati con fonti, licenze e citazioni dei dati.

## 1.4.1 — 2026-10-31

Identità grafica. Nessuna modifica al calcolo.

- **Logo** di SismaSite (forma dello spettro di risposta con il rombo blu dell'intestazione) nell'intestazione dell'app e come icona della pagina; file in `assets/logo.svg`, `assets/icon-512.png`, `assets/apple-touch-icon.png`.
- **Anteprima del link** (Open Graph): condividendo l'indirizzo dell'app su LinkedIn, Facebook o WhatsApp compare `assets/og-image.png` con titolo e descrizione.
- Meta tag `description`, `author` e `theme-color`.

## 1.4.0 — 2026-10-31

Cambio di titolarità e di licenza. Nessuna modifica al calcolo.

- **Licenza**: da MIT a **GNU AGPL-3.0** con termini aggiuntivi (Sez. 7): attribuzione obbligatoria all'autore nelle versioni derivate, marcatura delle versioni modificate, nessun diritto sui nomi "SismaSite" e "GeoHub". Le versioni fino alla 1.3.1 restano pubblicate con licenza MIT.
- **Titolare del copyright**: Fabio Duronio (in precedenza "Geologiaintasca").
- **Nuovi indirizzi**: repository `github.com/fabio-duronio/GeoHub-SismaSite`, app `fabio-duronio.github.io/GeoHub-SismaSite/`. I vecchi link al repository reindirizzano; il vecchio indirizzo dell'app no.
- **Piè di pagina dell'app**: autore, licenza e link al codice sorgente, come richiesto dalla AGPL per i programmi usati via rete.

## 1.3.1 — 2026-10-31

- Aggiunta l'icona della pagina (SVG inline nel `<head>`, nessun file aggiuntivo): elimina l'errore 404 su `/favicon.ico` nella console del browser. Nessuna modifica al calcolo.

## 1.3.0 — 2026-10-31

Revisione di conformità all'Allegato A e alle NTC 2018 dopo la validazione indipendente (300 siti casuali confrontati con un'implementazione separata delle formule: scarti dell'ordine di 1e-14).

### Correzioni normative

- **Interpolazione spaziale (Allegato A, eq. [3])** — la media pesata usa ora i **4 vertici della maglia del reticolo che contiene il sito**, come prescritto, e non più i 4 nodi più vicini. I due criteri coincidono in circa l'80 % dei siti; negli altri `a_g` poteva differire fino al 5–7 % (p95 ≈ 2 %). La maglia è individuata dalla numerazione per righe del reticolo (passo ricavato dai dati, 222) con un test punto-in-quadrilatero. Se il sito non ricade in una maglia completa (bordo del reticolo, lacune costiere) si ripiega sui 4 nodi più vicini **con avviso**. Valore di collaudo cambiato: **Cosenza** `a_g` 0,272 → 0,271 g, `k_h` 0,0864 → 0,0861; le altre località di riferimento sono invariate.
- **Fattore di comportamento allo SLD (§7.3, Tab. 7.3.I)** — `q` è limitato a **1,5** per lo SLD, con avviso quando il valore inserito è maggiore. Prima un `q` da SLV (es. 3,9) veniva applicato anche allo SLD, con spettro di danno non a favore di sicurezza. Il valore inserito resta applicato a SLV e SLC.

### Chiarimenti (nessuna modifica al calcolo)

- **Periodo di riferimento `V_R` (§2.4.3)** — confermato `V_R = V_N·C_U` **senza valore minimo**: il limite `V_R ≥ 35` anni delle NTC 2008 è stato eliminato dalle NTC 2018. Aggiunti una nota sotto i campi `V_N`/`C_U` e un avviso quando `V_R < 35` anni.
- **`β_s` oltre 0,4 g** — la Tab. 7.11.I non è definita oltre 0,4 g. I valori 0,36 / 0,32 adottati dalla v1.1.0 sono ora dichiarati come **scelta conservativa non normativa**, con avviso a schermo e nel report (la v1.1.0 li elencava erroneamente fra le correzioni normative).

### Tracciabilità e testi

- Il report indica, oltre agli ID e alle distanze dei nodi, il **criterio di selezione** adottato (vertici della maglia, nodo coincidente, 4 nodi più vicini).
- Nota metodologica a schermo allineata al nuovo criterio di interpolazione.
- `grid-data.json` e `convert_grid.py`: sostituiti i testi provvisori nei metadati (`source` con il riferimento ad Allegato B e Open Data MIT, `datum` = ED50). Dati numerici invariati.
- README e LICENSE aggiornati al nuovo nome del repository (**GeoHub-SismaSite**) e al nuovo indirizzo della demo; il vecchio URL di GitHub Pages non viene reindirizzato.
- `verifica_numeri.py`: aggiunti i controlli su passo del reticolo, criterio di selezione dei nodi, limite di `q` allo SLD e assenza del minimo di `V_R`.

## 1.2.0 — 2026-10-23

### Nuova funzionalità: spettri di risposta di progetto S_d(T)

- Nuovo pannello **"Spettri di risposta di progetto S_d(T)"** con grafico sovrapposto a quello elastico (elastici tratteggiati, di progetto in continuo, componenti orizzontale e verticale) e tabella di sintesi (`q`, `S_d(0)`, plateau, `S_d` a 1 s e 2 s, verifica del minimo).
- **SLO (§3.2.3.4)**: lo spettro di progetto coincide con l'elastico, per entrambe le componenti → `q` forzato a 1,0 anche per la verticale.
- **SLD / SLV / SLC (§3.2.3.5)**: applicata la sostituzione `η → 1/q` nelle formule [3.2.2] e [3.2.8]. Nel primo tratto `(T < T_B)` la riduzione **non** è una semplice divisione per `q`, perché `η` compare anche nel termine correttivo: `S_d(T) = a_g·S·(1/q)·F_0·[T/T_B + (q/F_0)(1 − T/T_B)]`.
- Applicato il minimo **`S_d(T) ≥ 0,2·a_g`** previsto dalla norma, con indicazione in tabella quando governa.
- Nuovo campo **fattore di comportamento `q`** (1–6, default 1,5) con richiamo ai limiti della Tab. 7.3.I; componente verticale con `q = 1,5` (1,0 per SLO).
- `verifica_numeri.py` esteso: verifica dei valori di `S_d` contro il calcolo manuale e del comportamento di SLO.

## 1.1.0 — 2026-10-23

Revisione tecnica di conformità alle NTC 2018 e correzione di anomalie emerse dai test.

### Correzioni normative

- **Isole (Allegato B, Tabella 2)** — aggiunta la tabella completa dei valori `a_g`, `F_0`, `T*_C` per i 5 gruppi di isole (Arcipelago Toscano, Egadi, Pantelleria, Sardegna, Pelagie, Ponza; Ventotene/S. Stefano; Ustica/Tremiti; Alicudi/Filicudi; Panarea/Stromboli/Lipari/Vulcano/Salina) con riconoscimento geografico puntuale (Sardegna per area rettangolare a sud del Capo Pertusato; le altre isole per centro + raggio, per non attribuire i valori tabellari alla costa antistante). Prima, per questi siti, l'app interpolava i nodi della costa: Sardegna −12,5 % su `a_g` e −13,1 % su `F_0`, Ustica −30,8 % su `a_g`.
- **Spettro elastico verticale (§3.2.3.2.2, Tab. 3.2.VI)** — corretto l'uso del coefficiente di amplificazione: `S_S = 1` per tutte le categorie e `S_T` da Tab. 3.2.V. Prima lo spettro verticale era sovrastimato del +20 % (cat. B) ÷ +48 % (cat. D) e sottostimato del 29 % con topografia T4.
- **Coefficiente `β_s` (Tab. 7.11.I)** — aggiunta la fascia `a_g > 0,4 g` (0,36 per cat. A, 0,32 per B–C–D–E): per `a_g` = 0,625 g il `k_h` passa da 0,175 a 0,200 (+12,5 %).
- **Liquefazione (§7.11.3.4.2)** — sostituita l'euristica con i criteri di esclusione **1** (`a_max` < 0,1 g) e **2** (falda > **15 m**, prima era 5 m, valore non previsto dalla norma). Aggiunta la dichiarazione esplicita che i criteri 3 e 4 richiedono indagini dirette.

### Affidabilità del dato

- **Punti fuori dal reticolo** — controllo della distanza dal nodo più vicino: oltre 15 km compare un avviso bloccante in pagina e nel PDF.
- **`T_R` fuori dall'intervallo 30–2475 anni** — il troncamento (previsto dall'Allegato A, nota 1) ora è segnalato con i valori richiesti.
- **Reticolo non caricato** — il calcolo è **disattivato** (pulsante disabilitato, risultati azzerati). Prima veniva usato un reticolo di riserva a 3 nodi che, per qualunque punto d'Italia, restituiva i valori dell'Aquila.
- **`F_0`** non più limitato a 3,2 (valore che la norma non prevede): il caricamento del reticolo ufficiale contiene nodi fino a 3,25.

### Tracciabilità del report

- Intestazione del report con **sito/commessa, data e ora, versione dell'applicativo, coordinate, fonte dei parametri** (reticolo o Tabella 2) e **ID e distanza dei 4 nodi interpolati**.
- Versione dell'applicativo riportata anche a piè di pagina.
- Campo libero "Nome sito / commessa".

### Disaggregazione

- Badge **"scenario illustrativo"** accanto al titolo del pannello.
- Avvertenza "non è un dato INGV" **spostata fuori** dal contenitore comprimibile (prima era visibile solo dopo aver espanso la matrice, e quindi mai a schermo).
- Titolo della sezione cambiato da "Terremoto dominante" a "Scenario dominante (illustrativo)".

### Interfaccia

- Corretto l'overflow orizzontale su schermi piccoli (392 px su viewport 375 px): `grid-template-columns: minmax(0,1fr)`, `min-width:0` su colonne e campi, tabella comprimibile sotto 560 px.

### Script di conversione

- `convert_grid.py`: corretto il ramo **CSV/TXT**, che falliva sul file ufficiale (`ValueError: Impossibile determinare l'ordine LAT/LON`). Ora gestisce campi fra virgolette, colonna `OBJECTID` anteposta, intestazioni su due righe, delimitatori `,`/`;`/tab e virgola decimale.
- `--decimals-val` portato da 3 a 4 decimali (la fonte ufficiale ne ha 4–5 in g/10).
- Aggiunti controlli su ID duplicati, numero di valori per `T_R` e numero di nodi.

### Documentazione

- README riscritto: comando di clone corretto (`GeoHub-Parametri-sismici`, prima puntava a un repository inesistente), metodo di calcolo con riferimenti puntuali alle norme, sezione **Limiti e perimetro d'uso**, nota **ED50/WGS84**, fonte dati con URL, tabella dei **valori di riferimento** per il collaudo.
- Aggiunto `verifica_numeri.py`: verifica automatica dei valori di riferimento, utile come test di non regressione.

### Note

- Nessuna modifica al formato di `grid-data.json`, che resta compatibile con le versioni precedenti.
- Il nome dell'applicazione (SismaSite) e quello del repository (GeoHub-Parametri-sismici) restano distinti: valutare se uniformarli.
