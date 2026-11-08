#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
convert_grid.py
----------------
Converte il reticolo di riferimento ufficiale (Allegato B al D.M. 14/01/2008,
recepito dalle NTC 2018 - 10.751 nodi, Open Data MIT/INGV) nel formato JSON
"colonnare" leggero usato da SismaSite (grid-data.json).

Accetta come input, senza bisogno di indicazioni aggiuntive:
  - Excel .xls / .xlsx  (letto con pandas, motore xlrd o openpyxl)
  - TXT / CSV grezzo (spazio/tab/virgola/punto e virgola come delimitatore)

Per l'Excel, lo script individua automaticamente:
  - il foglio giusto tra quelli presenti nel file (alcuni fogli possono
    essere vuoti o contenere note, non solo il reticolo)
  - la riga di intestazione (spesso preceduta da una riga di "raggruppamento"
    tipo "TR = 2475" che copre 3 colonne, non l'intestazione vera e propria)
  - le colonne ID, LON, LAT (per nome, case-insensitive; in loro assenza,
    tramite il range di valori tipico dell'Italia)
  - le terne ag/F0/Tc* per ciascun periodo di ritorno, riconoscendo pattern
    di intestazione come "T475ag", "T475_ag", "ag_475", "T475 Fo", ecc.
  - l'unità di misura di ag: le distribuzioni del reticolo derivate dall'Allegato B
    esprimono tradizionalmente ag in decimi di g (g/10), non in g pieno né in m/s².
    Lo script rileva questa convenzione dal valore massimo osservato (un ag oltre
    ~1.5 non è fisicamente plausibile se già in g per l'Italia) e converte
    dividendo per 10.
    ATTENZIONE - correzione rispetto a una versione precedente di questo script:
    una prima versione assumeva erroneamente che l'unità fosse m/s² (dividendo
    quindi per 9.80665). Verificato puntualmente sul nodo ufficiale più vicino
    a L'Aquila (id 26528, TR=475): valore grezzo 2.6099 -> ÷10 = 0.2610 g,
    contro il valore di ~0.26 g ampiamente documentato in letteratura tecnica
    per quell'area (es. Stucchi et al., studi di microzonazione post-2009);
    ÷9.80665 avrebbe dato invece 0.2661 g, sistematicamente troppo alto del
    ~2% su tutti i nodi. Confermato anche da fonti tecniche indipendenti che
    riportano esplicitamente "l'accelerazione al sito ag è espressa in g/10"
    per il reticolo di riferimento NTC.

Uso:
    python3 strumenti/convert_grid.py spettri2008.xls dati/grid-data.json
    python3 strumenti/convert_grid.py Grid.txt dati/grid-data.json --decimals-val 3
    python3 strumenti/convert_grid.py reticolo.xlsx dati/grid-data.json --sheet Foglio1 --header-row 1

Output: un unico grid-data.json in formato colonnare (nessuna chiave ripetuta
per nodo), pensato per restare nell'ordine di 2-3 MB anche con i 10.751 nodi
ufficiali:
    { "meta": {...}, "id":[N], "lat":[N], "lon":[N],
      "ag":[T array da N valori], "F0":[T array da N valori], "Tc":[T array da N valori] }

Note:
- Le coordinate ufficiali sono storicamente distribuite in datum ED50. Se ti
  serve precisione geodetica per l'uso con mappe WGS84 (Leaflet), converti
  con una libreria come pyproj prima di generare il JSON; lo scarto tipico
  ED50-WGS84 in Italia è dell'ordine di 1-3 arcosecondi (circa 20-100 m),
  trascurabile per l'individuazione del nodo più vicino.
- Lo script non convalida i valori nel merito: verifica sempre un campione
  di nodi (per ID o per coordinate) contro il servizio ufficiale INGV prima
  di un uso professionale.
"""
import os
import re
import json
import argparse

G = 10.0  # divisore per convertire ag da g/10 (convenzione del reticolo ufficiale) a g


def to_float(tok):
    """Converte un campo numerico tollerando virgola decimale e virgolette."""
    t = str(tok).strip().strip('"').strip()
    try:
        return float(t)
    except ValueError:
        return float(t.replace(",", "."))

LAT_RANGE = (34.0, 48.0)   # range plausibile per l'Italia (con margine)
LON_RANGE = (5.0, 20.0)
AG_PLAUSIBLE_MAX_G = 1.5   # oltre questa soglia, ag non può essere già in g

# Pattern per intestazioni tipo: T475ag, T475_ag, T475Fo, ag_475, Tc475, T2475Tc ...
HAZARD_COL_RE = re.compile(
    r"^T?_?(?P<tr>\d{2,4})_?(?P<param>ag|f0|fo|tc)$|^(?P<param2>ag|f0|fo|tc)_?T?(?P<tr2>\d{2,4})$",
    re.IGNORECASE,
)


# --------------------------------------------------------------------------
# Lettura Excel (.xls / .xlsx)
# --------------------------------------------------------------------------
def read_excel_grid(path, sheet=None, header_row=None):
    import pandas as pd

    xls = pd.ExcelFile(path)  # pandas sceglie da sé il motore (xlrd/openpyxl) in base al file
    sheet_names = [sheet] if sheet else xls.sheet_names

    for sh in sheet_names:
        raw = pd.read_excel(xls, sheet_name=sh, header=None, nrows=15)
        if raw.empty:
            continue

        hdr_idx = header_row if header_row is not None else _detect_header_row(raw)
        if hdr_idx is None:
            continue

        df = pd.read_excel(xls, sheet_name=sh, header=hdr_idx)
        df.columns = [str(c).strip() for c in df.columns]
        mapping = _map_columns(df.columns)
        if mapping is None:
            continue

        print(f"Foglio usato: '{sh}' (intestazione alla riga {hdr_idx + 1} del foglio Excel)")
        return _extract_nodes(df, mapping)

    raise ValueError(
        "Nessun foglio del file Excel sembra contenere il reticolo atteso "
        "(colonne ID/LAT/LON + terne ag/F0/Tc* per periodo di ritorno). "
        "Puoi forzare foglio e riga di intestazione con --sheet e --header-row."
    )


def _detect_header_row(raw_df, max_rows=10):
    """Cerca tra le prime righe quella che, se usata come intestazione,
    produce almeno una colonna ID/LAT/LON e una colonna hazard riconoscibile."""
    for i in range(min(max_rows, len(raw_df))):
        row_vals = [str(v).strip() for v in raw_df.iloc[i].tolist()]
        cols = row_vals
        if _map_columns(cols) is not None:
            return i
    return None


def _map_columns(columns):
    """Data una lista di intestazioni di colonna, prova a identificare
    ID, LAT, LON e le terne ag/F0/Tc* per ciascun TR. Ritorna un dict oppure
    None se la lista di colonne non sembra quella giusta."""
    id_idx = lat_idx = lon_idx = None
    hazard = {}  # tr (int) -> {'ag':idx,'F0':idx,'Tc':idx}

    for idx, raw_name in enumerate(columns):
        name = str(raw_name).strip()
        low = name.lower()

        if low in ("id", "id_punto", "point_id", "nodeid"):
            id_idx = idx
        elif low in ("lat", "latitude", "latitudine"):
            lat_idx = idx
        elif low in ("lon", "long", "longitude", "longitudine"):
            lon_idx = idx
        else:
            m = HAZARD_COL_RE.match(low.replace(" ", "").replace("*", ""))
            if m:
                tr = int(m.group("tr") or m.group("tr2"))
                param = (m.group("param") or m.group("param2")).lower()
                param = {"fo": "F0", "f0": "F0", "ag": "ag", "tc": "Tc"}[param]
                hazard.setdefault(tr, {})[param] = idx

    # servono almeno LAT, LON e un TR completo (ag+F0+Tc) per considerare valido il mapping
    complete_tr = {tr: cols for tr, cols in hazard.items() if len(cols) == 3}
    if lat_idx is None or lon_idx is None or not complete_tr:
        return None

    return {"id": id_idx, "lat": lat_idx, "lon": lon_idx, "hazard": complete_tr}


def _extract_nodes(df, mapping):
    n = len(df)
    tr_values = sorted(mapping["hazard"].keys())

    ids = (df.iloc[:, mapping["id"]].astype(float).astype(int).tolist()
           if mapping["id"] is not None else list(range(1, n + 1)))
    lats = df.iloc[:, mapping["lat"]].astype(float).tolist()
    lons = df.iloc[:, mapping["lon"]].astype(float).tolist()

    ag_cols, f0_cols, tc_cols = {}, {}, {}
    for tr in tr_values:
        cols = mapping["hazard"][tr]
        ag_cols[tr] = df.iloc[:, cols["ag"]].astype(float).tolist()
        f0_cols[tr] = df.iloc[:, cols["F0"]].astype(float).tolist()
        tc_cols[tr] = df.iloc[:, cols["Tc"]].astype(float).tolist()

    return {
        "n": n, "tr_values": tr_values,
        "ids": ids, "lats": lats, "lons": lons,
        "ag": ag_cols, "F0": f0_cols, "Tc": tc_cols,
    }


# --------------------------------------------------------------------------
# Lettura TXT / CSV grezzo (formato a colonne fisse, un TR via via crescente)
# --------------------------------------------------------------------------
def read_text_grid(path):
    """Legge un CSV/TXT con una riga per nodo e, per ogni nodo, la sequenza
    ID, LON, LAT (eventualmente preceduta da OBJECTID) seguita dalle 27 triple
    ag/F0/Tc* nell'ordine dei 9 TR.

    Gestisce, oltre al formato a colonne fisse separate da spazi:
      - CSV con campi fra virgolette (formato ufficiale dati.mit.gov.it,
        colonne "OBJECTID","ID","LON","LAT","T30ag",...),
      - intestazioni su una o due righe ("TR = 30" come riga di raggruppamento),
      - separatore ',' ';' o tab, con virgola come separatore decimale quando
        il delimitatore di campo è ';'.
    """
    import csv

    tr_ref = [30, 50, 72, 101, 140, 201, 475, 975, 2475]
    n_haz = len(tr_ref) * 3

    with open(path, "r", encoding="utf-8-sig", errors="ignore", newline="") as f:
        text = f.read()
    raw_lines = [l for l in text.splitlines() if l.strip()]
    if not raw_lines:
        raise ValueError("File vuoto")

    # --- rilevamento del delimitatore -------------------------------------
    # Si prova a leggere il file con ciascun delimitatore e si sceglie quello
    # che produce, per la maggior parte delle righe, almeno n_haz+3 campi.
    def try_parse(delim):
        rows, ok = [], 0
        for line in raw_lines:
            fields = next(csv.reader([line], delimiter=delim)) if delim else line.split()
            fields = [x.strip().strip('"').strip() for x in fields]
            if len(fields) >= n_haz + 3:
                try:
                    vals = [to_float(x) for x in fields]
                except ValueError:
                    continue
                rows.append(vals)
                ok += 1
        return rows, ok

    best = ([], 0, None)
    for delim in [";", ",", "\t", None]:
        rows, ok = try_parse(delim)
        if ok > best[1]:
            best = (rows, ok, delim)
    parsed_rows, n_ok, delim_used = best
    if n_ok == 0:
        raise ValueError(
            "Nessuna riga numerica valida trovata: attese almeno "
            f"{n_haz + 3} colonne (ID, LON, LAT + {n_haz} valori ag/F0/Tc*)."
        )
    print(f"Delimitatore rilevato: {repr(delim_used)} — righe valide: {n_ok}")

    # --- struttura delle colonne ------------------------------------------
    # n_lead = numero di colonne che precedono il blocco dei 27 valori:
    #   3 -> ID, LON, LAT
    #   4 -> OBJECTID, ID, LON, LAT  (formato ufficiale MIT)
    n_lead = len(parsed_rows[0]) - n_haz
    if n_lead not in (3, 4):
        raise ValueError(
            f"Struttura non riconosciuta: {len(parsed_rows[0])} colonne per riga "
            f"(attese {n_haz + 3} oppure {n_haz + 4})"
        )
    print(f"Colonne iniziali: {n_lead} "
          f"({'OBJECTID, ID, LON, LAT' if n_lead == 4 else 'ID, LON, LAT'})")

    sample = parsed_rows[:200]
    idx_id = 1 if n_lead == 4 else 0
    c_a, c_b = (2, 3) if n_lead == 4 else (1, 2)

    def fits(vals, rng):
        return all(rng[0] <= v <= rng[1] for v in vals)

    a_vals = [r[c_a] for r in sample]
    b_vals = [r[c_b] for r in sample]
    if fits(a_vals, LON_RANGE) and fits(b_vals, LAT_RANGE):
        order = "lon_lat"
    elif fits(a_vals, LAT_RANGE) and fits(b_vals, LON_RANGE):
        order = "lat_lon"
    else:
        raise ValueError(
            "Impossibile determinare l'ordine LAT/LON: i valori delle colonne "
            "geografiche non ricadono negli intervalli attesi per l'Italia. "
            "Verifica che ID/LON/LAT siano nelle posizioni previste."
        )
    print(f"Ordine colonne: colonna {c_a + 1}={order.split('_')[0].upper()}, "
          f"colonna {c_b + 1}={order.split('_')[1].upper()}")

    ids, lats, lons = [], [], []
    ag_cols = {tr: [] for tr in tr_ref}
    f0_cols = {tr: [] for tr in tr_ref}
    tc_cols = {tr: [] for tr in tr_ref}
    for r in parsed_rows:
        ids.append(int(round(r[idx_id])))
        if order == "lon_lat":
            lons.append(r[c_a]); lats.append(r[c_b])
        else:
            lats.append(r[c_a]); lons.append(r[c_b])
        block = r[n_lead:n_lead + n_haz]
        for t_i, tr in enumerate(tr_ref):
            ag_cols[tr].append(block[t_i * 3 + 0])
            f0_cols[tr].append(block[t_i * 3 + 1])
            tc_cols[tr].append(block[t_i * 3 + 2])

    # --- controlli minimi di coerenza -------------------------------------
    if len(set(ids)) != len(ids):
        dup = len(ids) - len(set(ids))
        print(f"ATTENZIONE: {dup} ID duplicati nel file di input.")
    for tr in tr_ref:
        if len(ag_cols[tr]) != len(ids):
            raise ValueError(f"Numero di valori incoerente per TR={tr}")
    if len(ids) != 10751:
        print(f"NOTA: il file contiene {len(ids)} nodi (il reticolo ufficiale ne ha 10751).")

    return {
        "n": len(ids), "tr_values": tr_ref,
        "ids": ids, "lats": lats, "lons": lons,
        "ag": ag_cols, "F0": f0_cols, "Tc": tc_cols,
    }


# --------------------------------------------------------------------------
# Costruzione del JSON colonnare finale
# --------------------------------------------------------------------------
def detect_ag_unit_and_fix(parsed):
    """Rileva se ag è espresso in g/10 (convenzione del reticolo ufficiale)
    e lo riporta in g. Un ag oltre la soglia plausibile se già in g implica
    che i valori vadano divisi per 10 (vedi nota nel docstring del modulo
    sulla verifica puntuale contro il nodo ufficiale più vicino a L'Aquila)."""
    max_tr = max(parsed["tr_values"])
    sample = parsed["ag"][max_tr]
    median_val = sorted(sample)[len(sample) // 2]
    if median_val > AG_PLAUSIBLE_MAX_G:
        print(f"Rilevato ag in unità g/10 (mediana a TR={max_tr}: {median_val:.3f}) -> conversione in g (÷{G:.0f}).")
        for tr in parsed["tr_values"]:
            parsed["ag"][tr] = [v / G for v in parsed["ag"][tr]]
    else:
        print(f"ag già in g (mediana a TR={max_tr}: {median_val:.3f}), nessuna conversione applicata.")
    return parsed


def build_columnar(parsed, decimals_coord=4, decimals_val=4, source_label="reticolo importato"):
    n = parsed["n"]
    tr_values = parsed["tr_values"]

    lats = [round(v, decimals_coord) for v in parsed["lats"]]
    lons = [round(v, decimals_coord) for v in parsed["lons"]]
    ag = [[round(v, decimals_val) for v in parsed["ag"][tr]] for tr in tr_values]
    f0 = [[round(v, decimals_val) for v in parsed["F0"][tr]] for tr in tr_values]
    tc = [[round(v, decimals_val) for v in parsed["Tc"][tr]] for tr in tr_values]

    return {
        "meta": {
            "source": source_label,
            "datum": "ED50",
            "trValues": tr_values,
            "count": n,
        },
        "id": parsed["ids"], "lat": lats, "lon": lons,
        "ag": ag, "F0": f0, "Tc": tc,
    }


def main():
    ap = argparse.ArgumentParser(description="Converte il reticolo ufficiale NTC (Excel o TXT/CSV) in grid-data.json colonnare.")
    ap.add_argument("input", help="File sorgente: .xls, .xlsx, .csv o .txt")
    ap.add_argument("output", help="File JSON di destinazione (es. grid-data.json)")
    ap.add_argument("--sheet", default=None, help="Nome del foglio Excel da usare (default: auto-rilevato)")
    ap.add_argument("--header-row", type=int, default=None, help="Indice (0-based) della riga di intestazione nel foglio Excel (default: auto-rilevato)")
    ap.add_argument("--decimals-coord", type=int, default=4, help="Decimali per lat/lon (default 4, ~11 m)")
    ap.add_argument("--decimals-val", type=int, default=4, help="Decimali per ag/F0/Tc* (default 4, come la fonte ufficiale)")
    ap.add_argument("--force-ag-unit", choices=["g", "g10"], default=None, help="Forza l'unità di ag invece di rilevarla automaticamente ('g10' = valori espressi come g/10)")
    args = ap.parse_args()

    ext = os.path.splitext(args.input)[1].lower()
    if ext in (".xls", ".xlsx", ".xlsm"):
        parsed = read_excel_grid(args.input, sheet=args.sheet, header_row=args.header_row)
        source_label = f"Allegato B al D.M. 14/01/2008, reticolo di riferimento (Open Data MIT, dataset Parametri Spettrali Sismici; file {os.path.basename(args.input)}, a_g convertito in g)"
    else:
        parsed = read_text_grid(args.input)
        source_label = f"Allegato B al D.M. 14/01/2008, reticolo di riferimento (Open Data MIT, dataset Parametri Spettrali Sismici; file {os.path.basename(args.input)}, a_g convertito in g)"

    if args.force_ag_unit == "g10":
        for tr in parsed["tr_values"]:
            parsed["ag"][tr] = [v / G for v in parsed["ag"][tr]]
        print("Conversione ag g/10 -> g forzata da --force-ag-unit.")
    elif args.force_ag_unit == "g":
        print("Unità ag forzata a 'già in g', nessuna conversione applicata.")
    else:
        parsed = detect_ag_unit_and_fix(parsed)

    grid = build_columnar(parsed, args.decimals_coord, args.decimals_val, source_label)

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(grid, f, ensure_ascii=False, separators=(",", ":"))

    size_mb = os.path.getsize(args.output) / (1024 * 1024)
    print(f"\nConvertiti {parsed['n']} nodi, {len(parsed['tr_values'])} periodi di ritorno {parsed['tr_values']} -> {args.output} ({size_mb:.2f} MB)")
    if parsed["n"] >= 10000 and size_mb > 3.2:
        print("Suggerimento: il file supera i ~3 MB. Riduci --decimals-val a 2 e/o "
              "--decimals-coord a 3 per un file più leggero.")


if __name__ == "__main__":
    main()
