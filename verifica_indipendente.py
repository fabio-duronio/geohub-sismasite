#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
verifica_indipendente.py — verifica INDIPENDENTE dei calcoli di SismaSite.

A differenza di verifica_numeri.py (test di non regressione su valori fissi),
questo script ricalcola da zero, in Python puro e a partire da grid-data.json,
la catena completa NTC 2018 e la confronta con l'output dell'app nel browser:

  1. conversione di datum WGS84 -> ED50 (Molodensky ridotta, EPSG:1133);
  2. selezione dei 4 vertici della maglia che contiene il sito (Allegato A);
  3. interpolazione log-log in T_R su ciascun vertice, poi media pesata con
     l'inverso della distanza (Allegato A, eq. [2] e [3]);
  4. S_S, C_C (Tab. 3.2.IV), S_T (Tab. 3.2.V), T_B, T_C, T_D, a_max;
  5. beta_s (Tab. 7.11.I), k_h, k_v (§7.11.3.5.2);
  6. spettro di progetto: SLO = elastico, minimo 0,2·a_g solo con q > 1.

Più alcuni controlli puntuali sui casi limite segnalati nella revisione v1.5.1
(T*_C minimo del reticolo, punto in mare, overflow su mobile).

Il codice NON riusa funzioni dell'app: le formule sono scritte qui a partire
dai testi normativi. Siti delle isole (Tabella 2) esclusi dal confronto
indipendente: sono già verificati in verifica_numeri.py (Cagliari).

Requisiti: pip install playwright && python3 -m playwright install chromium
Uso:       python3 verifica_indipendente.py [--n 40] [--verbose]
"""
import argparse
import json
import math
import os
import random
import sys

from verifica_numeri import free_port, serve

QUI = os.path.dirname(os.path.abspath(__file__))
TOLL_REL = 1e-4   # 0,01 %: le due implementazioni devono coincidere numericamente

# ---------------------------------------------------------------- datum
def wgs84_to_ed50(lat, lon):
    a, f = 6378137.0, 1 / 298.257223563
    aT, fT = 6378388.0, 1 / 297.0
    dX, dY, dZ = 87.0, 98.0, 121.0
    da, df = aT - a, fT - f
    p, l = math.radians(lat), math.radians(lon)
    e2 = 2 * f - f * f
    Rn = a / math.sqrt(1 - e2 * math.sin(p) ** 2)
    Rm = a * (1 - e2) / (1 - e2 * math.sin(p) ** 2) ** 1.5
    dp = (-dX * math.sin(p) * math.cos(l) - dY * math.sin(p) * math.sin(l) + dZ * math.cos(p)
          + (a * df + f * da) * math.sin(2 * p)) / Rm
    dl = (-dX * math.sin(l) + dY * math.cos(l)) / (Rn * math.cos(p))
    return lat + math.degrees(dp), lon + math.degrees(dl)

# ---------------------------------------------------------------- reticolo
class Reticolo:
    def __init__(self, path):
        d = json.load(open(path, encoding="utf-8"))
        self.id, self.lat, self.lon = d["id"], d["lat"], d["lon"]
        self.ag, self.F0, self.Tc = d["ag"], d["F0"], d["Tc"]
        self.TR = d["meta"]["trValues"]
        self.pos = {v: i for i, v in enumerate(self.id)}
        self.passo = 222   # passo di riga del reticolo ufficiale (verificato in verifica_numeri.py)

    @staticmethod
    def dist(la1, lo1, la2, lo2):
        r = math.radians
        a = math.sin(r(la2 - la1) / 2) ** 2 + math.cos(r(la1)) * math.cos(r(la2)) * math.sin(r(lo2 - lo1) / 2) ** 2
        return 2 * 6371 * math.asin(math.sqrt(a))

    @staticmethod
    def dentro(x, y, poly):
        c = False
        for k in range(len(poly)):
            (xa, ya), (xb, yb) = poly[k], poly[k - 1]
            if (ya > y) != (yb > y) and x < (xb - xa) * (y - ya) / (yb - ya) + xa:
                c = not c
        return c

    def vertici(self, la, lo):
        d = [self.dist(la, lo, self.lat[i], self.lon[i]) for i in range(len(self.id))]
        vicini = sorted(range(len(d)), key=d.__getitem__)[:4]
        if d[vicini[0]] < 0.05:
            return [vicini[0]], d, "nodo"
        P = self.passo
        for n in vicini:
            for b in (self.id[n], self.id[n] - 1, self.id[n] - P, self.id[n] - P - 1):
                v = [b, b + 1, b + P + 1, b + P]
                if all(x in self.pos for x in v):
                    ix = [self.pos[x] for x in v]
                    if self.dentro(lo, la, [(self.lon[i], self.lat[i]) for i in ix]):
                        return ix, d, "maglia"
        return vicini, d, "vicini"

    def pericolosita(self, la, lo, TR):
        TR = min(max(TR, self.TR[0]), self.TR[-1])
        k = 0
        while k < len(self.TR) - 2 and self.TR[k + 1] < TR:
            k += 1
        T1, T2 = self.TR[k], self.TR[k + 1]
        ix, d, metodo = self.vertici(la, lo)

        def interp_tempo(v1, v2):
            return v1 * (v2 / v1) ** (math.log(TR / T1) / math.log(T2 / T1))

        out = {}
        for nome, A in (("ag", self.ag), ("F0", self.F0), ("Tc0", self.Tc)):
            w = [1 / max(d[i], 0.05) for i in ix]
            out[nome] = sum(wi * interp_tempo(A[k][i], A[k + 1][i]) for wi, i in zip(w, ix)) / sum(w)
        out["metodo"] = metodo
        return out

# ---------------------------------------------------------------- NTC 2018
PVR = {"SLO": 0.81, "SLD": 0.63, "SLV": 0.10, "SLC": 0.05}
SS = {"A": (1.00, 0.00, 1.00, 1.00), "B": (1.40, 0.40, 1.00, 1.20), "C": (1.70, 0.60, 1.00, 1.50),
      "D": (2.40, 1.50, 0.90, 1.80), "E": (2.00, 1.10, 1.00, 1.60)}
CC = {"A": (1.00, 0.00), "B": (1.10, -0.20), "C": (1.05, -0.33), "D": (1.25, -0.50), "E": (1.15, -0.40)}
ST = {"T1": 1.0, "T2": 1.2, "T3": 1.2, "T4": 1.4}

def ntc(ret, lat_wgs, lon_wgs, cat, topo, VN, CU):
    la, lo = wgs84_to_ed50(lat_wgs, lon_wgs)
    VR = VN * CU
    res = {}
    for sl, p in PVR.items():
        TR = -VR / math.log(1 - p)
        h = ret.pericolosita(la, lo, TR)
        ag, F0, Tc0 = h["ag"], h["F0"], h["Tc0"]
        c0, c1, lo_s, hi_s = SS[cat]
        Ss = 1.0 if cat == "A" else min(hi_s, max(lo_s, c0 - c1 * F0 * ag))
        Cc = CC[cat][0] * Tc0 ** CC[cat][1]
        St = ST[topo]
        amax = Ss * St * ag
        if ag <= 0.1:
            beta = 0.20
        elif ag <= 0.2:
            beta = 0.27 if cat == "A" else 0.24
        elif ag <= 0.4:
            beta = 0.30 if cat == "A" else 0.28
        else:
            beta = None   # Tab. 7.11.I non definita oltre 0,4 g
        kh = beta * amax if beta is not None else None
        res[sl] = dict(TR=TR, ag=ag, F0=F0, Tc0=Tc0, Ss=Ss, Cc=Cc, Tc=Cc * Tc0, Tb=Cc * Tc0 / 3,
                       Td=4 * ag + 1.6, amax=amax, kh=kh, metodo=h["metodo"])
    return res

# ---------------------------------------------------------------- siti
CITTA = [("L'Aquila", 42.3499, 13.3995), ("Milano", 45.4642, 9.1900), ("Roma", 41.9028, 12.4964),
         ("Napoli", 40.8518, 14.2681), ("Catania", 37.5079, 15.0830), ("Cosenza", 39.2983, 16.2539),
         ("Torino", 45.0703, 7.6869), ("Firenze", 43.7696, 11.2558), ("Bologna", 44.4949, 11.3426),
         ("Ancona", 43.6158, 13.5189), ("Pescara", 42.4618, 14.2161), ("Chieti", 42.3510, 14.1675),
         ("Ortona", 42.3557, 14.4035), ("Potenza", 40.6404, 15.8056), ("Reggio Calabria", 38.1113, 15.6473),
         ("Messina", 38.1938, 15.5540), ("Palermo", 38.1157, 13.3615), ("Bari", 41.1171, 16.8719),
         ("Udine", 46.0711, 13.2346), ("Bolzano", 46.4983, 11.3548)]

def siti_casuali(ret, n, seed=20261104):
    rnd = random.Random(seed)
    out = []
    while len(out) < n:
        i = rnd.randrange(len(ret.id))
        la, lo = ret.lat[i] + rnd.uniform(0.005, 0.045), ret.lon[i] + rnd.uniform(0.005, 0.045)
        if 36.6 < la < 47.1 and 6.6 < lo < 18.5 and not (38.8 < la < 41.4 and lo < 9.9):   # esclusa Sardegna
            out.append((f"casuale {len(out)+1}", round(la, 5), round(lo, 5)))
    return out

COMBINAZIONI = [("A", "T1", 50, 1.0), ("B", "T2", 100, 1.5), ("C", "T1", 50, 2.0),
                ("D", "T4", 75, 1.0), ("E", "T3", 35, 0.7)]

# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=40, help="numero di siti casuali (default 40)")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Playwright non installato: pip install playwright && python3 -m playwright install chromium")
        return 2

    ret = Reticolo(os.path.join(QUI, "grid-data.json"))
    siti = CITTA + siti_casuali(ret, args.n)
    port = free_port()
    httpd = serve(QUI, port)
    fall, n_conf, scarto_max = [], 0, 0.0
    try:
        with sync_playwright() as p:
            br = p.chromium.launch()
            page = br.new_page(viewport={"width": 1500, "height": 1000})
            errori = []
            page.on("pageerror", lambda e: errori.append(str(e)))
            page.goto(f"http://127.0.0.1:{port}/index.html", wait_until="load")
            page.wait_for_function("typeof GRID !== 'undefined' && GRID && GRID.count > 1000", timeout=60000)

            # --- 1. confronto indipendente sull'intera catena di calcolo
            for k, (nome, la, lo) in enumerate(siti):
                cat, topo, VN, CU = COMBINAZIONI[k % len(COMBINAZIONI)]
                page.fill("#lat", str(la)); page.fill("#lon", str(lo))
                page.select_option("#soilCat", cat); page.select_option("#topoCat", topo)
                page.fill("#vn", str(VN)); page.select_option("#cu", str(CU))
                page.evaluate("() => runCalculation()")
                app = page.evaluate("() => lastResults.byLS")
                if "Tabella 2" in (app["SLV"].get("fonte") or ""):
                    continue
                ind = ntc(ret, la, lo, cat, topo, VN, CU)
                for sl in PVR:
                    a, b = app[sl], ind[sl]
                    for q in ("TR", "ag", "F0", "Tc0", "Ss", "Cc", "Tc", "Tb", "Td", "amax", "kh"):
                        va, vb = a.get(q), b[q]
                        if vb is None:
                            if va is not None and isinstance(va, (int, float)) and not math.isnan(va):
                                fall.append(f"{nome} {sl}: {q} atteso non calcolato (a_g > 0,4 g), app = {va}")
                            continue
                        rel = abs(va / vb - 1)
                        scarto_max = max(scarto_max, rel)
                        if rel > TOLL_REL:
                            fall.append(f"{nome} {sl} {cat}/{topo}: {q} app={va:.5f} indip={vb:.5f} ({rel*100:.3f} %)")
                    if (a.get("metodoNodi") or "") != b["metodo"]:
                        fall.append(f"{nome} {sl}: criterio nodi app={a.get('metodoNodi')} indip={b['metodo']}")
                n_conf += 1
                if args.verbose:
                    s = ind["SLV"]
                    print(f"  {nome:16s} {cat}/{topo} VR={VN*CU:5.1f}  ag={s['ag']:.4f} F0={s['F0']:.3f} Tc*={s['Tc0']:.4f}")
            print(f"[1] Catena NTC: {n_conf} siti x 4 stati limite, scarto massimo app/indipendente = {scarto_max*100:.5f} %")

            # --- 2. spettro di progetto SLO = elastico (nessun minimo 0,2·a_g)
            page.fill("#lat", "42.3499"); page.fill("#lon", "13.3995")
            page.select_option("#soilCat", "B"); page.select_option("#topoCat", "T1")
            page.fill("#vn", "50"); page.select_option("#cu", "1.0")
            page.evaluate("() => runCalculation()")
            d = page.evaluate("""() => { const r = lastResults.byLS.SLO, out = [];
                for(const T of [0, 0.5, 1, 2, 3, 4]) out.push([seDesignHorizontal(T, r, 1.0),
                     seHorizontal(T, r.ag, r.S, r.F0, r.Tb, r.Tc, r.Td, r.eta), 0.2*r.ag]);
                return out; }""")
            if any(abs(x - y) > 1e-12 for x, y, _ in d):
                fall.append("SLO: lo spettro di progetto non coincide con l'elastico")
            elif not any(y < m for _, y, m in d):
                fall.append("SLO: test non significativo (spettro elastico mai sotto 0,2·a_g)")
            else:
                print("[2] SLO: S_d = S_e anche dove S_e < 0,2·a_g (minimo non applicato)")

            # --- 2b. spettro elastico verticale, formula [3.2.8] NTC 2018 (F_0 a denominatore nel primo tratto)
            def sve_py(T, ag, F0, eta, St):
                Fv = 1.35 * F0 * ag ** 0.5
                TB, TC, TD = 0.05, 0.15, 1.0
                if T < TB:
                    return ag * St * eta * Fv * (T / TB + 1 / (eta * F0) * (1 - T / TB))
                if T < TC:
                    return ag * St * eta * Fv
                if T < TD:
                    return ag * St * eta * Fv * TC / T
                return ag * St * eta * Fv * TC * TD / T ** 2
            casi = [(0.261, 2.364, 1.0, 1.0), (0.12, 2.5, 0.8819, 1.2), (0.05, 2.6, 1.0, 1.4), (0.35, 2.4, 1 / 1.5, 1.0)]
            Tv = [0.0, 0.025, 0.05, 0.10, 0.15, 0.50, 1.0, 2.0, 4.0]
            sc_v = 0.0
            for ag, F0, eta, St in casi:
                app = page.evaluate(f"() => {Tv}.map(T => seVertical(T, {ag}, {F0}, {eta}, {St}))")
                for T, va in zip(Tv, app):
                    vb = sve_py(T, ag, F0, eta, St)
                    sc_v = max(sc_v, abs(va - vb))
                    if abs(va - vb) > 1e-12:
                        fall.append(f"S_ve(T={T}) ag={ag}: app={va:.6f} indip={vb:.6f}")
            print(f"[2b] Spettro verticale [3.2.8]: {len(casi)} casi x {len(Tv)} periodi, scarto massimo {sc_v:.1e} g")

            # --- 3. T*_C minimo del reticolo non alterato dal clamp
            i_min = min(range(len(ret.id)), key=lambda i: ret.Tc[0][i])
            tc_app = page.evaluate(f"() => hazardAtTR({ret.lat[i_min]}, {ret.lon[i_min]}, 30).Tc0")
            if abs(tc_app - ret.Tc[0][i_min]) > 1e-9:
                fall.append(f"T*_C nodo {ret.id[i_min]} a TR=30: app {tc_app}, dato ufficiale {ret.Tc[0][i_min]}")
            else:
                print(f"[3] T*_C minimo ufficiale ({ret.Tc[0][i_min]:.3f} s, nodo {ret.id[i_min]}) non alterato")

            # --- 4. punto in mare nel box della Sardegna: avviso presente
            page.fill("#lat", "39.5"); page.fill("#lon", "8.2")
            page.evaluate("() => runCalculation()")
            page.wait_for_function("() => document.getElementById('warnBox').innerText.includes('in mare')", timeout=30000)
            print("[4] Punto in mare (39,5 N; 8,2 E): avviso presente")

            # --- 5. nessun overflow orizzontale su mobile
            m = br.new_page(viewport={"width": 390, "height": 844}, is_mobile=True, device_scale_factor=2)
            m.goto(f"http://127.0.0.1:{port}/index.html", wait_until="load")
            m.wait_for_function("typeof GRID !== 'undefined' && GRID && GRID.count > 1000", timeout=60000)
            m.wait_for_timeout(1500)
            sw = m.evaluate("() => document.documentElement.scrollWidth")
            if sw > 390:
                fall.append(f"mobile 390 px: scrollWidth = {sw} px (overflow orizzontale)")
            else:
                print(f"[5] Mobile 390 px: nessun overflow (scrollWidth = {sw} px)")

            if errori:
                fall.append(f"errori JavaScript: {errori[:3]}")
            br.close()
    finally:
        httpd.shutdown()

    print()
    if fall:
        print(f"VERIFICA INDIPENDENTE FALLITA — {len(fall)} scostamenti:")
        for f in fall[:40]:
            print("  -", f)
        return 1
    print("VERIFICA INDIPENDENTE SUPERATA")
    return 0


if __name__ == "__main__":
    sys.exit(main())
