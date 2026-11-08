#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
verifica_numeri.py — verifica automatica dei valori di riferimento di SismaSite.

Apre l'applicazione in un browser headless (Playwright), esegue il calcolo per
un insieme di località note e confronta i risultati con la tabella di
riferimento riportata nel README (SLV, categoria B, topografia T1, V_N=50, C_U=1.0).

Serve come test di non regressione: se si modifica l'interpolazione o il
dataset, questo script deve continuare a passare.

Requisiti:
    pip install playwright && python3 -m playwright install chromium

Uso:
    python3 verifiche/verifica_numeri.py            # esce con codice 0 se tutto passa
    python3 verifiche/verifica_numeri.py --verbose
"""
import argparse
import functools
import http.server
import os
import socket
import socketserver
import sys
import threading

# (località, lat, lon, ag, F0, Tc*, Ss, amax, kh) — SLV, cat. B, T1, VN=50, CU=1.0
RIFERIMENTI = [
    ("L'Aquila", 42.3499, 13.3995, 0.261, 2.36, 0.347, 1.154, 0.301, 0.0842),
    ("Milano",   45.4642,  9.1900, 0.050, 2.66, 0.280, 1.200, 0.060, 0.0120),
    ("Roma",     41.9028, 12.4964, 0.120, 2.62, 0.297, 1.200, 0.144, 0.0346),
    ("Napoli",   40.8518, 14.2681, 0.168, 2.37, 0.338, 1.200, 0.201, 0.0483),
    ("Catania",  37.5079, 15.0830, 0.206, 2.46, 0.357, 1.197, 0.247, 0.0691),
    ("Cosenza",  39.2983, 16.2539, 0.271, 2.43, 0.372, 1.137, 0.308, 0.0861),  # v1.3.0: vertici della maglia (prima 4 nodi più vicini)
    ("Cagliari", 39.2238,  9.1217, 0.050, 2.88, 0.340, 1.200, 0.060, 0.0120),  # Tabella 2 (isole)
]
# tolleranze: i valori sono confrontati sugli arrotondamenti mostrati in tabella
TOL = {"ag": 0.0015, "F0": 0.011, "Tc0": 0.0015, "Ss": 0.0015, "amax": 0.0015, "kh": 0.0006}

TR_ATTESI = {"SLO": 30, "SLD": 50, "SLV": 475, "SLC": 975}

# Spettro di progetto S_d (NTC §3.2.3.5): L'Aquila, SLV, cat. B, T1, q = 1,5
# (orizzontale) e q = 1,5 (verticale). Valori calcolati a mano con le formule
# [3.2.2] e [3.2.8] sostituendo eta con 1/q.
RIFERIMENTI_SD = {
    "sd0": 0.3007,        # S_d(T=0)
    "plateau": 0.4738,    # a_g*S*F0/q
    "sd1": 0.2233,        # S_d(1,0 s)
    "sdv_plateau": 0.2831,
    "sdv0": 0.1797,       # S_dv(T=0) = a_g*S_T*F_v/F_0, formula [3.2.8] (F_0 a denominatore)
    "minimo": 0.05214,    # 0,2*a_g
}


def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class _SilentHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args, **kwargs):
        pass


def serve(directory, port):
    handler = functools.partial(_SilentHandler, directory=directory)
    httpd = socketserver.TCPServer(("127.0.0.1", port), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd


def main():
    ap = argparse.ArgumentParser(description="Verifica i valori di riferimento dell'applicazione.")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Playwright non installato. Esegui:\n  pip install playwright\n  python3 -m playwright install chromium")
        return 2

    qui = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # radice del repository
    port = free_port()
    httpd = serve(qui, port)
    url = f"http://127.0.0.1:{port}/index.html"
    fallimenti = []

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": 1500, "height": 1000})
            errori_js = []
            page.on("pageerror", lambda e: errori_js.append(str(e)))
            print(f"Carico {url} ...")
            page.goto(url, wait_until="load")
            page.wait_for_function(
                "typeof GRID !== 'undefined' && GRID && GRID.count > 1000", timeout=60000
            )
            n_nodi = page.evaluate("GRID.count")
            passo = page.evaluate("GRID.rowStride")
            if passo != 222:
                fallimenti.append(f"passo di riga del reticolo = {passo}, atteso 222")
            print(f"Reticolo caricato: {n_nodi} nodi")
            if n_nodi != 10751:
                fallimenti.append(f"reticolo con {n_nodi} nodi invece di 10751")

            for nome, lat, lon, ag, f0, tc, ss, amax, kh in RIFERIMENTI:
                page.fill("#lat", str(lat))
                page.fill("#lon", str(lon))
                page.select_option("#soilCat", "B")
                page.select_option("#topoCat", "T1")
                page.fill("#vn", "50")
                page.select_option("#cu", "1.0")
                page.click("#btnCalc")
                page.wait_for_timeout(250)
                r = page.evaluate(
                    """() => { const s = lastResults.byLS.SLV;
                        return {ag:s.ag, F0:s.F0, Tc0:s.Tc0, Ss:s.Ss, amax:s.amax, kh:s.kh, metodo:s.metodoNodi||'tab2',
                                TR: Object.fromEntries(Object.entries(lastResults.byLS).map(([k,v])=>[k,v.TR]))}; }"""
                )
                attesi = {"ag": ag, "F0": f0, "Tc0": tc, "Ss": ss, "amax": amax, "kh": kh}
                esiti = []
                for chiave, atteso in attesi.items():
                    delta = abs(r[chiave] - atteso)
                    ok = delta <= TOL[chiave]
                    esiti.append((chiave, r[chiave], atteso, delta, ok))
                    if not ok:
                        fallimenti.append(f"{nome}: {chiave} = {r[chiave]:.4f}, atteso {atteso} (Δ {delta:.4f})")
                for sl, tr_atteso in TR_ATTESI.items():
                    if abs(r["TR"][sl] - tr_atteso) > 0.5:
                        fallimenti.append(f"{nome}: T_R({sl}) = {r['TR'][sl]:.1f}, atteso {tr_atteso}")
                if nome != "Cagliari" and r["metodo"] != "maglia":
                    fallimenti.append(f"{nome}: nodi selezionati con criterio '{r['metodo']}', atteso 'maglia' (Allegato A)")
                stato = "OK " if all(e[4] for e in esiti) else "FAIL"
                print(f"  [{stato}] {nome:10s} ag={r['ag']:.3f} F0={r['F0']:.2f} Tc*={r['Tc0']:.3f} "
                      f"Ss={r['Ss']:.3f} amax={r['amax']:.3f} kh={r['kh']:.4f}")
                if args.verbose and stato == "FAIL":
                    for chiave, val, atteso, delta, ok in esiti:
                        print(f"        {chiave:5s} app={val:.4f} atteso={atteso} Δ={delta:.4f} {'ok' if ok else 'KO'}")

            # ---- spettro di progetto S_d ----
            print()
            page.fill("#lat", "42.3499"); page.fill("#lon", "13.3995")
            page.select_option("#soilCat", "B"); page.select_option("#topoCat", "T1")
            page.fill("#vn", "50"); page.select_option("#cu", "1.0")
            page.select_option("#lsSelect", "SLV"); page.fill("#qFactor", "1.5")
            page.click("#btnCalc"); page.wait_for_timeout(300)
            sd = page.evaluate(
                "() => { const r = lastResults.byLS.SLV, q = 1.5;"
                " return {sd0: seDesignHorizontal(1e-9, r, q),"
                "         plateau: seDesignHorizontal(r.Tb + 1e-6, r, q),"
                "         sd1: seDesignHorizontal(1.0, r, q),"
                "         sdv_plateau: seDesignVertical(0.10, r, 1.5),"
                "         sdv0: seDesignVertical(1e-9, r, 1.5),"
                "         minimo: 0.2 * r.ag}; }"
            )
            print("Spettro di progetto S_d (L'Aquila, SLV, q=1,5):")
            for chiave, atteso in RIFERIMENTI_SD.items():
                delta = abs(sd[chiave] - atteso)
                ok = delta <= 0.0015
                print(f"  [{'OK ' if ok else 'FAIL'}] {chiave:12s} app={sd[chiave]:.4f} atteso={atteso:.4f}")
                if not ok:
                    fallimenti.append(f"S_d {chiave} = {sd[chiave]:.4f}, atteso {atteso:.4f}")
            # SLO: q deve essere forzato a 1,0 per entrambe le componenti
            page.select_option("#lsSelect", "SLO")
            page.fill("#qFactor", "3.0")
            page.wait_for_timeout(300)
            q_slo = page.evaluate("() => document.getElementById('designQLabel').textContent")
            if q_slo.strip() != "1,0":
                fallimenti.append(f"SLO: q mostrato = {q_slo!r}, atteso 1,0")
            else:
                print("  [OK ] SLO impone q = 1,0 (entrambe le componenti)")

            # SLD: q limitato a 1,5 anche se l'utente inserisce un q da SLV
            page.fill("#qFactor", "3.9")
            page.select_option("#lsSelect", "SLD")
            page.wait_for_timeout(300)
            page.evaluate("() => renderDesignPanel()")
            q_sld = page.evaluate("() => document.getElementById('designQLabel').textContent").strip()
            nota_sld = page.evaluate("() => document.getElementById('designNote').innerText")
            if q_sld != "1,5" or "limitato a 1,5" not in nota_sld:
                fallimenti.append(f"SLD: q mostrato = {q_sld!r} (atteso 1,5 con avviso)")
            else:
                print("  [OK ] SLD limita q a 1,5 e lo segnala (q inserito 3,9)")
            # SLC: analisi lineare con q non prevista (Tab. 7.3.I) -> spettro elastico
            page.select_option("#lsSelect", "SLC")
            page.wait_for_timeout(300)
            page.evaluate("() => renderDesignPanel()")
            q_slc = page.evaluate("() => document.getElementById('designQLabel').textContent").strip()
            nota_slc = page.evaluate("() => document.getElementById('designNote').innerText")
            if q_slc != "1,0" or "Tab. 7.3.I" not in nota_slc:
                fallimenti.append(f"SLC: q mostrato = {q_slc!r} (atteso 1,0 con richiamo alla Tab. 7.3.I)")
            else:
                print("  [OK ] SLC restituisce lo spettro elastico, q = 1,0 (q inserito 3,9)")

            # SLV con q = 1,0: anche la componente verticale non è ridotta
            page.fill("#qFactor", "1.0")
            page.select_option("#lsSelect", "SLV")
            page.wait_for_timeout(300)
            page.evaluate("() => renderDesignPanel()")
            qv_slv = page.evaluate("() => document.querySelector('#designTableBody tr td:nth-child(3)').textContent").strip()
            if qv_slv != "1,0":
                fallimenti.append(f"SLV con q = 1,0: q verticale = {qv_slv!r}, atteso 1,0")
            else:
                print("  [OK ] SLV con q = 1,0: q verticale = 1,0")
            page.fill("#qFactor", "1.5")

            # V_R: nessun minimo di 35 anni (NTC 2018). V_N = 10, C_U = 0,7 -> V_R = 7, T_R(SLV) = 66,4 anni
            page.fill("#vn", "10"); page.select_option("#cu", "0.7")
            page.click("#btnCalc"); page.wait_for_timeout(300)
            tr_slv = page.evaluate("() => lastResults.byLS.SLV.TR")
            avviso = page.evaluate("() => document.getElementById('warnBox').innerText")
            if abs(tr_slv - 66.4) > 0.2 or "35 anni" not in avviso:
                fallimenti.append(f"V_R = 7 anni: T_R(SLV) = {tr_slv:.1f} (atteso 66,4, nessun minimo) o avviso mancante")
            else:
                print("  [OK ] V_R senza minimo di 35 anni (NTC 2018), con nota esplicativa")
            tr_slo_tab = page.evaluate("() => document.querySelector('#hazardTableBody tr td:nth-child(3)').textContent").strip()
            if not tr_slo_tab.startswith("30"):
                fallimenti.append(f"V_R = 7 anni: T_R(SLO) in tabella = {tr_slo_tab!r}, atteso il valore adottato 30")
            else:
                print(f"  [OK ] T_R(SLO) limitato mostrato in tabella: {tr_slo_tab}")

            if errori_js:
                fallimenti.append(f"errori JavaScript: {errori_js[:3]}")
            browser.close()
    finally:
        httpd.shutdown()

    print()
    if fallimenti:
        print(f"VERIFICA FALLITA — {len(fallimenti)} problema/i:")
        for f in fallimenti:
            print("  -", f)
        return 1
    print(f"VERIFICA SUPERATA — {len(RIFERIMENTI)} località conformi ai valori di riferimento.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
