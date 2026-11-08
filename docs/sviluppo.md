# Sviluppo e dati

Struttura del repository, avvio in locale e rigenerazione dei file dati.

[← Torna al README](../README.md)

## Struttura del repository

```
index.html          applicazione completa (HTML + CSS + JavaScript, nessuna dipendenza da compilare)
assets/             logo, icone e immagine di anteprima per la condivisione
dati/               file dati letti dall'app
  grid-data.json              reticolo di riferimento (10.751 nodi × 9 T_R), forma colonnare
  classificazione-data.json   classificazione sismica dei comuni (DPC, maggio 2025)
  comuni-data.json            confini comunali ISTAT 2026 (generalizzati, semplificati)
  storica-data.json           CPTI15 v4.0 + DBMI15 v4.0 (sismicità storica)
strumenti/          script che rigenerano i file in dati/ dalle fonti ufficiali
  convert_grid.py · convert_classificazione.py · convert_comuni.py · convert_storica.py
verifiche/          script di controllo (vedi docs/validazione.md)
  verifica_dati.py · verifica_numeri.py · verifica_indipendente.py · verifica_allegato_b.py
docs/               metodo di calcolo, validazione, sviluppo
.github/            modelli per segnalare discrepanze di calcolo e proporre funzioni
README.md · CHANGELOG.md · LICENSE · NOTICE
```

## Avvio in locale

- Un browser moderno (Chrome, Firefox, Edge, Safari).
- Python 3 per servire la cartella in locale durante lo sviluppo (necessario: i browser bloccano `fetch()` di `dati/grid-data.json` se la pagina è aperta come `file://`).

```bash
git clone https://github.com/fabio-duronio/geohub-sismasite.git
cd geohub-sismasite
python3 -m http.server 8000
```

Apri <http://localhost:8000/>. Non serve alcuna build né installazione di dipendenze: l'applicazione è HTML/CSS/JavaScript puro, eseguita interamente nel browser.

**Deploy**: la cartella è già pubblicabile così com'è su GitHub Pages (branch `main`, root). Non ci sono passaggi di compilazione.

## Rigenerare `dati/grid-data.json`

Il file `dati/grid-data.json` già presente nel repository è **verificato** e corrisponde ai dati ufficiali (vedi [Validazione](validazione.md)). Va rigenerato solo se si cambia la fonte dati.

```bash
pip install pandas xlrd openpyxl

# sorgente ufficiale in Excel
python3 strumenti/convert_grid.py spettri2008.xls dati/grid-data.json

# oppure sorgente ufficiale in CSV (stesso risultato)
python3 strumenti/convert_grid.py spettri2008.csv dati/grid-data.json
```

Lo script rileva automaticamente foglio, riga di intestazione, colonne `ID/LON/LAT` (anche in presenza della colonna `OBJECTID` anteposta), delimitatori `,`/`;`/tab, virgola decimale e **unità di misura di `ag`** (il reticolo ufficiale esprime `a_g` in **g/10**: lo script lo riconosce e converte in g). Al termine stampa un riepilogo e avvisa se il numero di nodi non è 10.751.

Opzioni utili: `--sheet`, `--header-row`, `--decimals-val` (default 4), `--decimals-coord` (default 4), `--force-ag-unit g|g10`.

**Fonte dei dati**: Open Data del Ministero delle Infrastrutture e dei Trasporti, dataset *Parametri Spettrali Sismici* — <https://dati.mit.gov.it/catalog/dataset/parametri-spettrali> (Allegato B al D.M. 14/01/2008, G.U.R.I. 4 febbraio 2008, S.O. n. 30).

Requisiti: Python 3.10+, `pandas`, `xlrd` (file `.xls`) e/o `openpyxl` (file `.xlsx`). Il ramo CSV/TXT usa solo la libreria standard.

Gli altri file in `dati/` si rigenerano con gli script omonimi in `strumenti/` (le istruzioni sono in testa a ciascuno script).

## Formato di `grid-data.json`

```json
{ "meta": { "source": "...", "datum": "...", "trValues": [30, 50, 72, 101, 140, 201, 475, 975, 2475], "count": 10751 },
  "id": [ ... ], "lat": [ ... ], "lon": [ ... ],
  "ag": [ [10751 valori per TR=30], ... 9 array ],
  "F0": [ ... ], "Tc": [ ... ] }
```

## Tecnologie

HTML5, CSS3, JavaScript (vanilla, nessun framework) · [Leaflet](https://leafletjs.com/) per la mappa · [Chart.js](https://www.chartjs.org/) per i grafici · Python (`pandas`/`csv`) per la conversione dei dati.

Le librerie Leaflet e Chart.js sono caricate da CDN: senza connessione la mappa e i grafici non sono disponibili, mentre il calcolo numerico e le tabelle continuano a funzionare.
