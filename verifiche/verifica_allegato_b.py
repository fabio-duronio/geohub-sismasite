#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
verifica_allegato_b.py — confronto dei dati di SismaSite con il testo ufficiale
dell'Allegato B al D.M. 14/01/2008 (G.U. 4/2/2008, S.O. n. 30).

Legge il PDF del decreto (con allegati), estrae:
  - Tabella 1: reticolo di riferimento (10.751 nodi, a_g in g/10, F_0, T*_C per 9 T_R);
  - Tabella 2: valori costanti per le isole;
e li confronta rispettivamente con grid-data.json e con ISLAND_TABLE in index.html.

Il PDF stampa a_g (g/10) con 3 decimali e F_0, T*_C con 2: lo scarto ammesso è
mezza unità dell'ultima cifra stampata (0,005).

Requisiti: pdftotext (poppler-utils).
Uso:       python3 verifiche/verifica_allegato_b.py Decreto_14-01-2008.pdf
"""
import json
import os
import re
import subprocess
import sys

QUI = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # radice del repository
TOLL = 0.005 + 1e-9

def testo_pdf(path):
    return subprocess.run(["pdftotext", "-layout", path, "-"], capture_output=True,
                          text=True, check=True).stdout.splitlines()

def tabella1(righe):
    num = r"\d+(?:\.\d+)?"
    pat = re.compile(rf"^\s*(\d{{1,5}})\s+({num})\s+({num})((?:\s+{num}){{27}})\s*$")
    tab = {}
    for l in righe:
        m = pat.match(l)
        if m:
            tab[int(m.group(1))] = (float(m.group(2)), float(m.group(3)), [float(x) for x in m.group(4).split()])
    return tab

def tabella2(righe):
    i = next(k for k, l in enumerate(righe) if l.startswith("TABELLA 2"))
    out = []
    for l in righe[i:i + 40]:
        v = re.findall(r"\d,\d{2,3}", l)
        if len(v) >= 27:
            out.append([float(x.replace(",", ".")) for x in v[-27:]])
    return out

def main():
    if len(sys.argv) != 2:
        print(__doc__); return 2
    righe = testo_pdf(sys.argv[1])
    fall = []

    # --- Tabella 1 vs grid-data.json
    t1 = tabella1(righe)
    g = json.load(open(os.path.join(QUI, "dati", "grid-data.json"), encoding="utf-8"))
    pos = {v: i for i, v in enumerate(g["id"])}
    if len(t1) != 10751 or set(t1) != set(pos):
        fall.append(f"Tabella 1: {len(t1)} nodi letti dal PDF, {len(set(t1) ^ set(pos))} ID non comuni con grid-data.json")
    mx = dict(coord=0.0, ag=0.0, F0=0.0, Tc=0.0)
    for k, (lo, la, v) in t1.items():
        if k not in pos:
            continue
        i = pos[k]
        mx["coord"] = max(mx["coord"], abs(g["lon"][i] - lo), abs(g["lat"][i] - la))
        for t in range(9):
            for nome, off, scala in (("ag", 0, 10), ("F0", 1, 1), ("Tc", 2, 1)):
                e = abs(g[nome][t][i] * scala - v[3 * t + off])
                mx[nome] = max(mx[nome], e)
                if e > TOLL:
                    fall.append(f"nodo {k}, TR={g['meta']['trValues'][t]}: {nome} JSON={g[nome][t][i]} PDF={v[3*t+off]}")
    if mx["coord"] > 0.0005 + 1e-9:
        fall.append(f"Tabella 1: scarto massimo sulle coordinate {mx['coord']:.5f}°")
    print(f"[1] Tabella 1: {len(t1)} nodi; scarti massimi a_g {mx['ag']:.4f} g/10, F_0 {mx['F0']:.4f}, "
          f"T*_C {mx['Tc']:.4f} s, coordinate {mx['coord']:.4f}°")

    # --- Tabella 2 vs ISLAND_TABLE
    t2 = tabella2(righe)
    js = open(os.path.join(QUI, "index.html"), encoding="utf-8").read()
    blk = js[js.index("const ISLAND_TABLE"):js.index("const ISLAND_SITES")]
    grp = re.findall(r"(\w):\{name:'([^']+)',\s*ag:\[([^\]]+)\],\s*F0:\[([^\]]+)\],\s*Tc:\[([^\]]+)\]", blk)
    if len(t2) != 5 or len(grp) != 5:
        fall.append(f"Tabella 2: {len(t2)} righe nel PDF, {len(grp)} gruppi nell'app (attesi 5)")
    for (k, nome, ag, f0, tc), o in zip(grp, t2):
        app = [[float(x) for x in s.split(",")] for s in (ag, f0, tc)]
        for j in range(9):
            for q, (val, uff) in enumerate(((app[0][j], o[3 * j] / 10), (app[1][j], o[3 * j + 1]), (app[2][j], o[3 * j + 2]))):
                if abs(val - uff) > 1e-9:
                    fall.append(f"Tabella 2, gruppo {k} ({nome}), TR n.{j+1}: {['ag','F0','Tc'][q]} app={val} uff.={uff}")
        print(f"[2] Tabella 2, gruppo {k}: {nome} — {'OK' if not any(f'gruppo {k} ' in f for f in fall) else 'DIFFERENZE'}")

    print()
    if fall:
        print(f"VERIFICA ALLEGATO B FALLITA — {len(fall)} differenze:")
        for f in fall[:30]:
            print("  -", f)
        return 1
    print("VERIFICA ALLEGATO B SUPERATA — reticolo e isole coincidono con il testo ufficiale")
    return 0


if __name__ == "__main__":
    sys.exit(main())
