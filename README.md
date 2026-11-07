# SismaSite — Parametri sismici del sito secondo NTC 2018

Applicazione web *client-side* per il calcolo dei parametri di pericolosità sismica di base e delle azioni sismiche su un sito, secondo il **D.M. 17/01/2018 (NTC 2018)**, la **Circolare n. 7/2019** e gli **Allegati A e B al D.M. 14/01/2008**.

Repository: [`fabio-duronio/geohub-sismasite`](https://github.com/fabio-duronio/geohub-sismasite) · Demo: <https://fabio-duronio.github.io/geohub-sismasite/>

Autore: **Fabio Duronio**, geologo.

> **Cos'è e cosa non è.** È uno strumento di *screening e supporto preliminare* per geologi e ingegneri: restituisce i parametri di pericolosità sismica ufficiale (`a_g`, `F_0`, `T*_C`), i coefficienti di amplificazione, gli spettri elastici e di progetto (con `q` scelto dal progettista), i coefficienti sismici `k_h`, `k_v` e un inquadramento sismico del sito (classificazione, sismicità strumentale e storica, faglie capaci). **Non** sostituisce la relazione geologica/geotecnica e non esegue analisi di risposta sismica locale. Vedi la sezione [Limiti e perimetro d'uso](#limiti-e-perimetro-duso).

---

## Funzionalità

- **Ubicazione del sito** su mappa interattiva (Leaflet) o per coordinate inserite a mano, con basi cartografiche stradale (OpenStreetMap) e satellitare (Esri), vertici della maglia del reticolo usati nel calcolo e blocco della mappa contro gli spostamenti involontari.
- **Carta di pericolosità INGV** (dalla v1.7.0): carta di `a_g` del modello MPS04 dal servizio WMS ufficiale INGV, per i 9 periodi di ritorno del reticolo (probabilità di eccedenza in 50 anni dall'81 % al 2 %; predefinito `T_R` = 475 anni, cioè 10 % in 50 anni) e i percentili 16°, 50° e 84°, con legenda ufficiale e opacità regolabile; per impostazione predefinita segue lo stato limite selezionato (livello con `T_R` più vicino). È un **inquadramento visivo**: il calcolo usa sempre il reticolo dell'Allegato B.
- **Parametri di pericolosità sismica di base**: `a_g`, `F_0`, `T*_C` per i quattro stati limite (SLO, SLD, SLV, SLC), interpolati dal **reticolo di riferimento ufficiale a 10.751 nodi** (Allegato B) e, per le isole, dalla **Tabella 2** dello stesso Allegato.
- **Periodo di ritorno** `T_R` calcolato da `V_R = V_N · C_U` e `P_VR` secondo NTC §2.4.3.
- **Coefficienti di amplificazione** `S_S`, `C_C`, `S_T` e periodi `T_B`, `T_C`, `T_D` (NTC §3.2.3.2.1, Tabb. 3.2.IV e 3.2.V).
- **Pericolosità di base per i 9 periodi di ritorno** del reticolo (dalla v1.7.0): tabella di `a_g`, `F_0`, `T*_C` e spettri elastici su suolo A, T1, come la Fase 1 del foglio Spettri-NTC del CSLP.
- **Spettri di risposta elastici** orizzontale `S_e(T)` e verticale `S_ve(T)`, con effetto dello smorzamento `η`.
- **Spettri di risposta di progetto** orizzontale `S_d(T)` e verticale `S_dv(T)` secondo §3.2.3.4 (SLO: q = 1) e §3.2.3.5 (SLD/SLV/SLC: sostituzione `η → 1/q`), con fattore di comportamento `q` impostabile e applicazione del minimo `S_d ≥ 0,2·a_g`.
- **Coefficienti sismici** `k_h = β_s · a_max/g` e `k_v = ±0,5 k_h` per analisi pseudostatica dei pendii (NTC §7.11.3.5.2, Tab. 7.11.I); non calcolati se `a_g` > 0,4 g, oltre il campo della tabella. Destinati a essere trasferiti in una futura app GeoHub sulla stabilità dei pendii (in progetto).
- **Screening liquefazione** con i criteri di esclusione 1 e 2 del §7.11.3.4.2 (destinato a essere trasferito in una futura app GeoHub sulla liquefazione, in progetto).
- **Inquadramento sismico del sito** (dalla v1.5.0):
  - **comune e classificazione sismica**: comune individuato dai confini ISTAT 2026, zona dall'elenco DPC (maggio 2025) così come pubblicata, sottozone comprese; *solo fini programmatori e amministrativi*;
  - **eventi strumentali nel raggio** dal servizio FDSN dell'INGV, in tempo reale (predefiniti: 30 km, M ≥ 2,5, dal 1985), con il tipo di magnitudo di ogni evento;
  - **storia sismica della località** (DBMI15 v4.0) e **terremoti storici con epicentro nel raggio** (CPTI15 v4.0);
  - **faglie attive e capaci** dal catalogo ISPRA ITHACA, in tempo reale, entro un raggio di ricerca non normativo (predefinito 10 km), senza fasce di rispetto, con rimando alle Linee guida FAC.
- **Interfaccia a schede** (dalla v1.7.0): Parametri, Spettri, Inquadramento sismico; la stampa le riporta tutte in sequenza.
- **Stampa A4 come allegato alla relazione** (pulsante «Stampa / Salva PDF»): frontespizio, 1. Dati del sito con mappa e legenda, 2. Parametri, 3. Spettri, 4. Inquadramento sismico, 5. Note metodologiche e fonti. Intestazione con sito/commessa e data, piè di pagina con riferimento dell'allegato (modificabile, predefinito «Allegato E1»), «pag. x di y» e versione. Carattere Arial, testo giustificato, virgola decimale, intestazioni delle tabelle colorate. Tracciabilità: coordinate WGS84 ed ED50, fonte dei parametri, **ID e distanza dei nodi del reticolo utilizzati**. Intestazione e numerazione delle pagine richiedono Chrome o Edge (in «Altre impostazioni» disattivare «Intestazioni e piè di pagina» del browser).

## Prerequisiti

- Un browser moderno (Chrome, Firefox, Edge, Safari).
- Python 3 per servire la cartella in locale durante lo sviluppo (necessario: i browser bloccano `fetch()` di `grid-data.json` se la pagina è aperta come `file://`).

Per rigenerare `grid-data.json`:

- Python 3.10+, `pandas`, `xlrd` (file `.xls`) e/o `openpyxl` (file `.xlsx`). Il ramo CSV/TXT usa solo la libreria standard.

## Installazione e avvio

```bash
git clone https://github.com/fabio-duronio/geohub-sismasite.git
cd geohub-sismasite
python3 -m http.server 8000
```

Apri <http://localhost:8000/>. Non serve alcuna build né installazione di dipendenze: l'applicazione è HTML/CSS/JavaScript puro, eseguita interamente nel browser.

**Deploy**: la cartella è già pubblicabile così com'è su GitHub Pages (branch `main`, root). Non ci sono passaggi di compilazione.

## Rigenerare `grid-data.json`

Il file `grid-data.json` già presente nel repository è **verificato** e corrisponde ai dati ufficiali (vedi [Validazione](#validazione)). Va rigenerato solo se si cambia la fonte dati.

```bash
pip install pandas xlrd openpyxl

# sorgente ufficiale in Excel
python3 convert_grid.py spettri2008.xls grid-data.json

# oppure sorgente ufficiale in CSV (stesso risultato)
python3 convert_grid.py spettri2008.csv grid-data.json
```

Lo script rileva automaticamente foglio, riga di intestazione, colonne `ID/LON/LAT` (anche in presenza della colonna `OBJECTID` anteposta), delimitatori `,`/`;`/tab, virgola decimale e **unità di misura di `ag`** (il reticolo ufficiale esprime `a_g` in **g/10**: lo script lo riconosce e converte in g). Al termine stampa un riepilogo e avvisa se il numero di nodi non è 10.751.

Opzioni utili: `--sheet`, `--header-row`, `--decimals-val` (default 4), `--decimals-coord` (default 4), `--force-ag-unit g|g10`.

**Fonte dei dati**: Open Data del Ministero delle Infrastrutture e dei Trasporti, dataset *Parametri Spettrali Sismici* — <https://dati.mit.gov.it/catalog/dataset/parametri-spettrali> (Allegato B al D.M. 14/01/2008, G.U.R.I. 4 febbraio 2008, S.O. n. 30).

## Metodo di calcolo

1. **Periodo di ritorno** — `T_R = −V_R / ln(1 − P_VR)`, con `V_R = V_N · C_U` (NTC 2018 §2.4.3, **senza valore minimo**: il limite `V_R ≥ 35` anni delle NTC 2008 è stato eliminato; per `V_R < 35` anni l'app mostra una nota) e `P_VR` = 81 %, 63 %, 10 %, 5 % rispettivamente per SLO, SLD, SLV, SLC (NTC 2018, Tab. 3.2.I). Il valore è limitato all'intervallo tabulato **30–2475 anni** (Allegato A, nota 1); quando il limite interviene l'app lo segnala.
2. **Datum** — le coordinate inserite (WGS84) sono convertite in **ED50**, il datum del reticolo, prima di interrogarlo (Molodensky ridotta, parametri EPSG:1133; accuratezza di alcuni metri). Il report riporta entrambe le coppie di coordinate. Comuni, eventi, storia sismica e faglie restano in WGS84, il loro datum nativo.
3. **Interpolazione** — per ciascuno dei **4 vertici della maglia del reticolo che contiene il sito** il parametro è interpolato in `T_R` con legge logaritmica tra i due periodi tabulati che racchiudono `T_R` (Allegato A, eq. [2]); i quattro valori sono poi combinati con una media pesata con pesi = inversi delle distanze (Allegato A, eq. [3]), nello stesso ordine del foglio CS.LL.PP. Spettri-NTC. La maglia è individuata dalla numerazione per righe del reticolo (passo di riga ricavato dai dati: 222) con un test punto-in-quadrilatero. Se il sito non ricade in una maglia completa (bordo del reticolo, lacune lungo la costa) si usano i 4 nodi più vicini e l'app lo segnala. Il criterio adottato è riportato nel report insieme agli ID dei nodi.
4. **Isole** — per tutte le isole escluse Sicilia, Ischia, Procida e Capri i parametri sono **costanti** e sono presi dalla **Tabella 2 dell'Allegato B**; per questi siti il reticolo non viene interrogato. Il riconoscimento è geografico e approssimato: Sardegna per area rettangolare, le altre isole per centro + raggio (Elba, Pianosa, Capraia, Gorgona, Giglio, Giannutri, Montecristo, Egadi, Pantelleria, Lampedusa, Linosa, Ponza, Palmarola, Zannone, Ventotene, S. Stefano, Ustica, Tremiti, Alicudi, Filicudi, Panarea, Stromboli, Lipari, Vulcano, Salina). Un punto sulla costa antistante (es. Piombino, Argentario) resta correttamente sul reticolo.
5. **Amplificazione** — `S_S` e `C_C` (Tab. 3.2.IV), `S_T` (Tab. 3.2.V), `T_B = T_C/3`, `T_C = C_C·T*_C`, `T_D = 4a_g + 1,6`, `η = √(10/(5+ξ))` con limite inferiore 0,55.
6. **Spettri elastici** — orizzontale: NTC eq. 3.2.6–3.2.8; verticale (§3.2.3.2.2): `F_v = 1,35·F_0·√(a_g/g)`, **`S_S = 1`**, `S_T` da Tab. 3.2.V, `T_B` = 0,05 s, `T_C` = 0,15 s, `T_D` = 1,0 s.
7. **Spettri di progetto** — per **SLO** coincidono con gli elastici (q = 1,0, §3.2.3.4), per entrambe le componenti. Per **SLD, SLV, SLC** si sostituisce `η` con `1/q` nelle formule [3.2.2] e [3.2.8] (§3.2.3.5): ne risulta, per `0 ≤ T < T_B`, `S_d(T) = a_g·S·(1/q)·F_0·[T/T_B + (q/F_0)(1 − T/T_B)]`, mentre per `T ≥ T_B` vale `S_d = S_e/q`. Agli spettri ridotti con `q > 1` si applica il minimo `S_d(T) ≥ 0,2·a_g`; con `q = 1` (sempre per SLO) lo spettro di progetto è l'elastico, senza minimo. Il fattore `q` impostato dall'utente vale per **SLV e SLC** (Tab. 7.3.I: dissipativo ≥ 1,5 / non dissipativo ≤ 1,5); per **SLD** l'app adotta `min(q; 1,5)` e segnala quando il valore inserito viene limitato; per **SLO** `q = 1`. Per la componente verticale si adotta `q = 1,5` (per SLO `q = 1`).
8. **Coefficienti sismici** — `a_max = S_S·S_T·a_g`, `k_h = β_s·a_max/g`, `k_v = ±0,5·k_h`, con `β_s` dalla Tab. 7.11.I (0,20 / 0,27 / 0,30 per categoria A e 0,20 / 0,24 / 0,28 per B–C–D–E nelle fasce ≤ 0,1 g / 0,1–0,2 g / 0,2–0,4 g; oltre 0,4 g la tabella non è definita: l'app **non calcola** `k_h` e `k_v` e lo segnala con un avviso; il coefficiente va giustificato dal progettista).

## Validazione

La validazione si articola su tre livelli, distinti:

- **Dati**: `grid-data.json` è generato da `convert_grid.py` a partire dal file ufficiale MIT (`spettri2008.xls`), con controllo di cardinalità (10.751 nodi), ID, coordinate, unità di `a_g` (g/10 → g) e valori estremi (`a_g` 0,009–0,625 g; `F_0` 2,20–3,25; `T*_C` 0,095–0,601 s).
- **Testo ufficiale** (`verifica_allegato_b.py`): confronto con le Tabelle 1 e 2 dell'Allegato B lette dal PDF del D.M. 14/01/2008 (G.U. 4/2/2008, S.O. n. 30). Esito: 10.751 nodi su 10.751 con ID identici, scarti entro l'arrotondamento della stampa (≤ 0,005 su `a_g` in g/10, `F_0`, `T*_C`; ≤ 0,0005° sulle coordinate); Tabella 2 delle isole identica nei 5 gruppi.
- **Verifica indipendente** (`verifica_indipendente.py`): ricalcola in Python puro, senza riusare codice dell'app, l'intera catena (datum, maglia, interpolazione, `S_S`, `C_C`, `S_T`, `T_B`, `T_C`, `T_D`, `a_max`, `β_s`, `k_h`) su 20 città e 40 siti casuali con categorie di sottosuolo, topografia e `V_R` diversi, e la confronta con l'app nel browser (tolleranza 0,01 %). Controlla inoltre lo spettro SLO, il `T*_C` minimo del reticolo, l'avviso per i punti in mare e l'assenza di overflow su mobile.
- **Non regressione** (`verifica_numeri.py`): confronta l'app con la tabella di riferimento qui sotto (comprese le isole, Tabella 2).

Valori di riferimento per il collaudo (**SLV**, categoria **B**, topografia **T1**, `V_N` = 50 anni, `C_U` = 1,0; `T_R` = 475 anni):

| Località | a_g (g) | F_0 | T*_C (s) | S_S | a_max (g) | k_h |
|---|---|---|---|---|---|---|
| L'Aquila | 0,261 | 2,36 | 0,347 | 1,154 | 0,301 | 0,0842 |
| Milano | 0,050 | 2,66 | 0,280 | 1,200 | 0,060 | 0,0120 |
| Roma | 0,120 | 2,62 | 0,297 | 1,200 | 0,144 | 0,0346 |
| Napoli | 0,168 | 2,37 | 0,338 | 1,200 | 0,201 | 0,0483 |
| Catania | 0,206 | 2,46 | 0,357 | 1,197 | 0,247 | 0,0691 |
| Cosenza | 0,271 | 2,43 | 0,372 | 1,137 | 0,308 | 0,0861 |
| Cagliari (Tab. 2, isole) | 0,050 | 2,88 | 0,340 | 1,200 | 0,060 | 0,0120 |

Spettro di progetto di riferimento (**L'Aquila, SLV, cat. B, T1, q = 1,5**): `S_d(0)` = 0,3007 g · plateau `S_d` = 0,4738 g · `S_d(1,0 s)` = 0,2233 g · `S_dv` plateau = 0,2831 g · minimo `0,2·a_g` = 0,0521 g. Con SLO il fattore `q` è forzato a 1,0 per entrambe le componenti.

`T_R` attesi: SLO 30 · SLD 50 · SLV 475 · SLC 975 anni (con `V_R` = 50 anni).

Per rieseguire la verifica automatica (facoltativa, richiede `playwright`):

```bash
pip install playwright && python3 -m playwright install chromium
python3 verifica_numeri.py          # non regressione
python3 verifica_indipendente.py    # calcolo indipendente
```

`verifica_numeri.py` controlla i parametri di pericolosità per 7 località (compresa un'isola), il criterio di selezione dei nodi (vertici della maglia), lo spettro di progetto `S_d`, il comportamento di SLO e SLD (limite `q ≤ 1,5`) e l'assenza del minimo di `V_R`, ed esce con codice diverso da zero se qualcosa non torna: è utilizzabile come test di non regressione in CI.

## Limiti e perimetro d'uso

Cosa l'applicazione **non** fa, e che resta a carico del professionista:

- **Spettri di progetto** `S_d(T)`: l'applicazione li calcola con il metodo semplificato delle NTC (riduzione delle ordinate elastiche tramite `q`, §3.2.3.5), ma **non sceglie né giustifica `q`**: il valore va definito dal progettista secondo Tab. 7.3.I e 7.3.II (`q = q_0·K_R`) e in funzione del comportamento strutturale dissipativo o non dissipativo e della regolarità in altezza.
- **Non esegue analisi non lineari** né analisi con storie temporali; **non esegue analisi di risposta sismica locale** né amplificazioni 2D/3D: le amplificazioni sono quelle convenzionali `S_S`·`S_T` delle NTC.
- **Non verifica la stabilità dei pendii**: fornisce i coefficienti `k_h`, `k_v` da usare in un'analisi pseudostatica o alla Newmark.
- **Liquefazione**: applica **solo** i criteri di esclusione 1 (`a_max` < 0,1 g) e 2 (falda > 15 m) del §7.11.3.4.2. I criteri 3 ((N₁)₆₀ > 30, q_c1N > 180) e 4 (granulometria, Fig. 7.11.1) richiedono indagini dirette e **non** sono verificati. Il coefficiente di sicurezza `F_S` non è calcolato.
- **Disaggregazione**: non fa parte della pericolosità sismica di base e **non è presente** in SismaSite (rimossa nella v1.6.0). Serve a valle, dove si usa la magnitudo (es. fattore di scala nella verifica a liquefazione), e sarà gestita nell'app che la utilizza. Fonte di riferimento: INGV, applicazione esse1-gis (modello MPS04-S1; Spallarossa e Barani 2007, Progetto DPC-INGV S1, Deliverable D14), il cui report del nodo si allega alla relazione.
- **Classificazione sismica**: ha solo valore programmatorio e amministrativo e non entra nel calcolo. Il comune è individuato con i confini ISTAT generalizzati (scala non certificabile uniformemente): entro 200 m dal confine l'app chiede conferma.
- **Eventi strumentali, faglie capaci**: dati interrogati in tempo reale dai servizi INGV e ISPRA; se un servizio non risponde la sezione lo segnala. Le avvertenze delle fonti (completezza del catalogo, carattere non definitivo di ITHACA) sono riportate nell'app.
- **Storia sismica**: l'assenza di un terremoto nella storia di una località non significa che non sia stato risentito.
- **Copertura geografica**: il reticolo copre il territorio nazionale (maglia ≤ 10 km) **esclusi** Sardegna e isole minori, gestite dalla Tabella 2. Per punti esterni alla copertura (estero, mare aperto, isole non riconosciute) l'app **segnala** che i valori sono estrapolati e non utilizzabili a fini normativi; l'attribuzione di un punto a un'isola è comunque una semplificazione geografica da verificare a cura dell'utente.
- **Datum**: inserire le coordinate in **WGS84** (GPS, mappe web): l'app le converte in ED50, il datum del reticolo. Lo scarto ED50–WGS84 in Italia è di circa 100–150 m; senza conversione l'effetto su `a_g` sarebbe in genere < 0,2 %, con punte del 2–3 % in zone a forte gradiente. Coordinate già in ED50 (ad es. lette da Spettri-NTC) vanno prima riportate in WGS84.
- **Punti in mare**: se il punto non ricade in alcun comune né entro 2 km da un comune, l'app segnala che i valori (reticolo o Tabella 2) non rappresentano un sito di progetto.

I risultati riportano sempre la **fonte** utilizzata (reticolo o Tabella 2) e gli **ID dei nodi** interpolati, così il calcolo è tracciabile e ripercorribile.

## Struttura del progetto

```
index.html                  applicazione completa (HTML + CSS + JS vanilla)
assets/                     icone e immagine di anteprima per la condivisione

grid-data.json              reticolo di riferimento in forma colonnare (10.751 nodi × 9 TR)
classificazione-data.json   classificazione sismica dei comuni (DPC, maggio 2025)
comuni-data.json            confini comunali ISTAT 2026 (generalizzati, semplificati)
storica-data.json           CPTI15 v4.0 + DBMI15 v4.0 (sismicità storica)

convert_grid.py             rigenera grid-data.json da XLS/XLSX/CSV/TXT ufficiali
convert_classificazione.py  rigenera classificazione-data.json
convert_comuni.py           rigenera comuni-data.json
convert_storica.py          rigenera storica-data.json

verifica_dati.py            controlli sui file dati (Abruzzo = Allegato B Decreto 4/2024; Ortona = 24 eventi INGV)
verifica_allegato_b.py      confronto di reticolo e isole con il PDF ufficiale dell'Allegato B (opzionale)
verifica_indipendente.py    ricalcolo indipendente in Python e confronto con l'app (opzionale)
verifica_numeri.py          non regressione sui valori di riferimento (opzionale)

.github/ISSUE_TEMPLATE/     modelli per segnalare discrepanze di calcolo e proporre funzioni
README.md · CHANGELOG.md · LICENSE · NOTICE
```

Formato di `grid-data.json` (colonnare, nessuna chiave ripetuta per nodo):

```json
{ "meta": { "source": "...", "datum": "...", "trValues": [30, 50, 72, 101, 140, 201, 475, 975, 2475], "count": 10751 },
  "id": [ ... ], "lat": [ ... ], "lon": [ ... ],
  "ag": [ [10751 valori per TR=30], ... 9 array ],
  "F0": [ ... ], "Tc": [ ... ] }
```

## Tecnologie

HTML5, CSS3, JavaScript (vanilla, nessun framework) · [Leaflet](https://leafletjs.com/) per la mappa · [Chart.js](https://www.chartjs.org/) per i grafici · Python (`pandas`/`csv`) per la conversione dei dati.

Le librerie Leaflet e Chart.js sono caricate da CDN: senza connessione la mappa e i grafici non sono disponibili, mentre il calcolo numerico e le tabelle continuano a funzionare.

## Licenza e citazione

Copyright © 2026 Fabio Duronio. Distribuito con licenza **GNU AGPL-3.0** con termini aggiuntivi (testo della licenza in [LICENSE](LICENSE), copyright e termini aggiuntivi in [NOTICE](NOTICE)). In sintesi:

- **Uso libero**, anche professionale: puoi usare l'app per relazioni, progetti e studi senza alcun costo.
- **Chi modifica o ridistribuisce** il codice, anche solo pubblicandolo come servizio web, deve rilasciarlo con la stessa licenza e rendere disponibile il codice sorgente.
- **Attribuzione obbligatoria**: le versioni derivate devono riportare nell'interfaccia "Basato su SismaSite di Fabio Duronio, geologo" con il link a questo repository.
- **Nomi**: "SismaSite" e "GeoHub" non sono concessi in licenza; le versioni modificate devono usare un nome diverso.
- **Licenze commerciali** diverse dalla AGPL (ad esempio per integrare il codice in software non open source) sono disponibili su richiesta.

Le versioni fino alla 1.3.1 sono state pubblicate con licenza MIT.

I dati di pericolosità sismica derivano dagli Open Data del Ministero delle Infrastrutture e dei Trasporti (Allegato B al D.M. 14/01/2008): citare la fonte originale in ogni utilizzo.

Fonti e licenze dei dati dell'inquadramento sismico (dettagli in [NOTICE](NOTICE)): Dipartimento della Protezione Civile (classificazione, CC BY 4.0); ISTAT (confini comunali, CC BY 4.0); INGV (servizio FDSN, CC BY 4.0; CPTI15 e DBMI15 v4.0, CC BY-SA 4.0 come indicato nei file); ISPRA (ITHACA, CC BY 4.0).

Se usi lo strumento in un lavoro professionale o scientifico, cita: *Duronio F., SismaSite (GeoHub-SismaSite), parametri sismici del sito secondo NTC 2018, versione X.Y.Z, https://github.com/fabio-duronio/geohub-sismasite*.
