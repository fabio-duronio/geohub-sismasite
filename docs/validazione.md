# Validazione

Come sono controllati i dati e i calcoli di SismaSite.

[← Torna al README](../README.md)

La validazione si articola su tre livelli, distinti:

- **Dati**: `dati/grid-data.json` è generato da `strumenti/convert_grid.py` a partire dal file ufficiale MIT (`spettri2008.xls`), con controllo di cardinalità (10.751 nodi), ID, coordinate, unità di `a_g` (g/10 → g) e valori estremi (`a_g` 0,009–0,625 g; `F_0` 2,20–3,25; `T*_C` 0,095–0,601 s).
- **Testo ufficiale** (`verifiche/verifica_allegato_b.py`): confronto con le Tabelle 1 e 2 dell'Allegato B lette dal PDF del D.M. 14/01/2008 (G.U. 4/2/2008, S.O. n. 30). Esito: 10.751 nodi su 10.751 con ID identici, scarti entro l'arrotondamento della stampa (≤ 0,005 su `a_g` in g/10, `F_0`, `T*_C`; ≤ 0,0005° sulle coordinate); Tabella 2 delle isole identica nei 5 gruppi.
- **Verifica indipendente** (`verifiche/verifica_indipendente.py`): ricalcola in Python puro, senza riusare codice dell'app, l'intera catena (datum, maglia, interpolazione, `S_S`, `C_C`, `S_T`, `T_B`, `T_C`, `T_D`, `a_max`, `β_s`, `k_h`) su 20 città e 40 siti casuali con categorie di sottosuolo, topografia e `V_R` diversi, e la confronta con l'app nel browser (tolleranza 0,01 %). Controlla inoltre lo spettro SLO, lo spettro elastico verticale [3.2.8] su più periodi, il `T*_C` minimo del reticolo, l'avviso per i punti in mare e l'assenza di overflow su mobile.
- **Non regressione** (`verifiche/verifica_numeri.py`): confronta l'app con la tabella di riferimento qui sotto (comprese le isole, Tabella 2).

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

Spettro di progetto di riferimento (**L'Aquila, SLV, cat. B, T1, q = 1,5**): `S_d(0)` = 0,3007 g · plateau `S_d` = 0,4738 g · `S_d(1,0 s)` = 0,2233 g · `S_dv` plateau = 0,2831 g · `S_dv(0)` = 0,1797 g · minimo `0,2·a_g` = 0,0521 g. Con SLO e SLC il fattore `q` è forzato a 1,0 per entrambe le componenti.

`T_R` attesi: SLO 30 · SLD 50 · SLV 475 · SLC 975 anni (con `V_R` = 50 anni).

## Eseguire le verifiche

Richiedono Python 3 e Playwright (facoltativo per l'uso dell'app):

```bash
pip install playwright && python3 -m playwright install chromium
python3 verifiche/verifica_dati.py            # file dati (classificazione, storia sismica)
python3 verifiche/verifica_numeri.py          # non regressione
python3 verifiche/verifica_indipendente.py    # calcolo indipendente
python3 verifiche/verifica_allegato_b.py Decreto_14-01-2008.pdf   # confronto con il PDF ufficiale
```

`verifiche/verifica_numeri.py` controlla i parametri di pericolosità per 7 località (compresa un'isola), il criterio di selezione dei nodi (vertici della maglia), lo spettro di progetto `S_d`, il comportamento di SLO, SLD (limite `q ≤ 1,5`) e SLC (spettro elastico), il `q` verticale con `q = 1,0`, il `T_R` limitato mostrato in tabella e l'assenza del minimo di `V_R`, ed esce con codice diverso da zero se qualcosa non torna: è utilizzabile come test di non regressione in CI.
