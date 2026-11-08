#!/usr/bin/env python3
"""
convert_comuni.py — SismaSite (GeoHub)

Converte i confini comunali ISTAT (versione generalizzata, shapefile WGS84
UTM32N) in un file JSON compatto per individuare il comune del sito.
Solo libreria standard Python (lettura .shp/.dbf, proiezione inversa UTM,
semplificazione Douglas-Peucker).

Uso:
    python3 strumenti/convert_comuni.py <Com01012026_g_WGS84.shp> [comuni-data.json] [tolleranza_m]

Fonte: ISTAT, "Confini delle unità amministrative a fini statistici al 1°
gennaio 2026", versione generalizzata —
https://www.istat.it/notizia/confini-delle-unita-amministrative-a-fini-statistici-al-1-gennaio-2018-2/
Licenza CC BY 4.0 (note legali ISTAT). ISTAT avverte che la scala "non è
certificabile uniformemente": vicino ai confini l'app chiede conferma.

Formato di uscita: per ogni comune [PRO_COM_T, nome, bbox, anelli]; ogni anello
è una lista piatta di interi = coordinate in 1e-5 gradi, prima coppia assoluta
e successive come differenze (delta encoding).
"""
import json
import os
import math
import struct
import sys
from datetime import date

# ---------- proiezione inversa UTM (WGS84, fuso 32N) ----------
A = 6378137.0
F = 1 / 298.257223563
K0 = 0.9996
E2 = F * (2 - F)
EP2 = E2 / (1 - E2)
LON0 = math.radians(9.0)
E1 = (1 - math.sqrt(1 - E2)) / (1 + math.sqrt(1 - E2))


def utm_to_ll(x, y):
    x -= 500000.0
    m = y / K0
    mu = m / (A * (1 - E2 / 4 - 3 * E2**2 / 64 - 5 * E2**3 / 256))
    p = (mu + (3 * E1 / 2 - 27 * E1**3 / 32) * math.sin(2 * mu)
         + (21 * E1**2 / 16 - 55 * E1**4 / 32) * math.sin(4 * mu)
         + (151 * E1**3 / 96) * math.sin(6 * mu)
         + (1097 * E1**4 / 512) * math.sin(8 * mu))
    s, c, t = math.sin(p), math.cos(p), math.tan(p)
    n = A / math.sqrt(1 - E2 * s * s)
    r = A * (1 - E2) / (1 - E2 * s * s) ** 1.5
    d = x / (n * K0)
    tt, cc = t * t, EP2 * c * c
    lat = p - (n * t / r) * (d**2 / 2 - (5 + 3 * tt + 10 * cc - 4 * cc * cc - 9 * EP2) * d**4 / 24
                             + (61 + 90 * tt + 298 * cc + 45 * tt * tt - 252 * EP2 - 3 * cc * cc) * d**6 / 720)
    lon = LON0 + (d - (1 + 2 * tt + cc) * d**3 / 6
                  + (5 - 2 * cc + 28 * tt - 3 * cc * cc + 8 * EP2 + 24 * tt * tt) * d**5 / 120) / c
    return math.degrees(lat), math.degrees(lon)


# ---------- lettura shapefile / dbf ----------
def leggi_dbf(path):
    with open(path, 'rb') as f:
        hdr = f.read(32)
        nrec, hlen, rlen = struct.unpack('<IHH', hdr[4:12])
        campi = []
        while True:
            d = f.read(32)
            if d[0] == 0x0D:
                break
            nome = d[:11].split(b'\0')[0].decode()
            campi.append((nome, d[16]))
        f.seek(hlen)
        out = []
        for _ in range(nrec):
            rec = f.read(rlen)
            pos, row = 1, {}
            for nome, ln in campi:
                row[nome] = rec[pos:pos + ln].decode('utf-8', 'replace').strip()
                pos += ln
            out.append(row)
    return out


def leggi_shp(path):
    with open(path, 'rb') as f:
        f.seek(100)
        geoms = []
        while True:
            h = f.read(8)
            if len(h) < 8:
                break
            _, clen = struct.unpack('>ii', h)
            data = f.read(clen * 2)
            tipo = struct.unpack('<i', data[:4])[0]
            if tipo == 0:
                geoms.append([])
                continue
            if tipo != 5:
                sys.exit(f'tipo di geometria non gestito: {tipo}')
            nparts, npts = struct.unpack('<ii', data[36:44])
            parts = list(struct.unpack(f'<{nparts}i', data[44:44 + 4 * nparts]))
            off = 44 + 4 * nparts
            pts = struct.unpack(f'<{2 * npts}d', data[off:off + 16 * npts])
            xy = list(zip(pts[0::2], pts[1::2]))
            parts.append(npts)
            geoms.append([xy[parts[i]:parts[i + 1]] for i in range(nparts)])
    return geoms


# ---------- semplificazione Douglas-Peucker (in metri, su UTM) ----------
def dp(pts, tol):
    if len(pts) < 5:
        return pts
    if pts[0] == pts[-1]:
        # anello chiuso: si divide nel vertice più lontano dal primo, così la
        # corda di riferimento non è degenere
        x0, y0 = pts[0]
        k = max(range(1, len(pts) - 1), key=lambda i: (pts[i][0] - x0) ** 2 + (pts[i][1] - y0) ** 2)
        a, b = dp_aperto(pts[:k + 1], tol), dp_aperto(pts[k:], tol)
        out = a + b[1:]
        return out if len(out) >= 4 else pts
    return dp_aperto(pts, tol)


def dp_aperto(pts, tol):
    if len(pts) < 3:
        return pts
    keep = [False] * len(pts)
    keep[0] = keep[-1] = True
    stack = [(0, len(pts) - 1)]
    while stack:
        i, j = stack.pop()
        (x1, y1), (x2, y2) = pts[i], pts[j]
        dx, dy = x2 - x1, y2 - y1
        L = math.hypot(dx, dy) or 1e-9
        dmax, k = -1, -1
        for m in range(i + 1, j):
            x, y = pts[m]
            dist = abs(dy * (x - x1) - dx * (y - y1)) / L
            if dist > dmax:
                dmax, k = dist, m
        if dmax > tol:
            keep[k] = True
            stack += [(i, k), (k, j)]
    return [p for p, kk in zip(pts, keep) if kk]


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    shp = sys.argv[1]
    dst = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'dati', 'comuni-data.json')
    tol = float(sys.argv[3]) if len(sys.argv) > 3 else 20.0
    attr = leggi_dbf(shp[:-4] + '.dbf')
    geoms = leggi_shp(shp)
    if len(attr) != len(geoms):
        sys.exit('numero di record .shp e .dbf diverso')
    comuni, npt_in, npt_out = [], 0, 0
    for a, g in zip(attr, geoms):
        anelli, minla, minlo, maxla, maxlo = [], 90, 180, -90, -180
        for ring in g:
            npt_in += len(ring)
            r = dp(ring, tol)
            npt_out += len(r)
            flat, px, py = [], None, None
            for x, y in r:
                la, lo = utm_to_ll(x, y)
                minla, maxla = min(minla, la), max(maxla, la)
                minlo, maxlo = min(minlo, lo), max(maxlo, lo)
                qy, qx = round(la * 1e5), round(lo * 1e5)
                if px is None:
                    flat += [qx, qy]
                else:
                    flat += [qx - px, qy - py]
                px, py = qx, qy
            anelli.append(flat)
        comuni.append([a['PRO_COM_T'], a['COMUNE'],
                       [round(minlo, 5), round(minla, 5), round(maxlo, 5), round(maxla, 5)], anelli])
    out = {
        'meta': {
            'fonte': "ISTAT - Confini delle unità amministrative a fini statistici al 1° gennaio 2026 (versione generalizzata)",
            'url': 'https://www.istat.it/notizia/confini-delle-unita-amministrative-a-fini-statistici-al-1-gennaio-2018-2/',
            'licenza': 'CC BY 4.0',
            'modifiche': f'proiettato da UTM32N a WGS84 geografiche; semplificato (Douglas-Peucker, {tol:g} m); coordinate a 1e-5 gradi con codifica a differenze',
            'avviso': "Scala non certificabile uniformemente (ISTAT): vicino ai confini comunali verificare il comune.",
            'campi': ['PRO_COM_T', 'COMUNE', 'bbox [lonmin, latmin, lonmax, latmax]', 'anelli'],
            'generato': date.today().isoformat(),
            'n_comuni': len(comuni),
            'punti_originali': npt_in,
            'punti_semplificati': npt_out,
        },
        'comuni': comuni,
    }
    with open(dst, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, separators=(',', ':'))
    print(f'{dst}: {len(comuni)} comuni, punti {npt_in} -> {npt_out} (tolleranza {tol:g} m)')


if __name__ == '__main__':
    main()
