#!/usr/bin/env python3
"""
verifica_dati.py — SismaSite (GeoHub)

Controlli sui file dati generati da convert_classificazione.py e
convert_storica.py, con valori di riferimento verificati su fonti ufficiali:
- classificazione: confronto Abruzzo con l'Allegato B del Decreto PGR Abruzzo
  n. 4/2024 (verificato il 02/11/2026: 305 comuni coincidenti);
- storia sismica di Ortona (IT_57933): 24 eventi, confrontati da Fabio Duronio
  con la pagina INGV https://emidius.mi.ingv.it/CPTI15-DBMI15/place/IT_57933
  il 02/11/2026.

Uso:
    python3 verifiche/verifica_dati.py [classificazione-data.json] [storica-data.json]
Esce con codice 1 se un controllo fallisce.
"""
import json
import os
import sys

errori = []


def check(cond, msg):
    print(('OK   ' if cond else 'ERR  ') + msg)
    if not cond:
        errori.append(msg)


def main():
    DATI = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'dati')
    fc = sys.argv[1] if len(sys.argv) > 1 else os.path.join(DATI, 'classificazione-data.json')
    fs = sys.argv[2] if len(sys.argv) > 2 else os.path.join(DATI, 'storica-data.json')

    # ---------------- Classificazione ----------------
    C = json.load(open(fc, encoding='utf-8'))
    com = C['comuni']
    check(C['meta']['n_comuni'] == len(com) == 7896, 'classificazione: 7.896 comuni')
    check(len(C['regioni']) == 20, 'classificazione: 20 regioni')
    abr = C['regioni'].index('Abruzzo')
    ab = [v for v in com.values() if v[2] == abr]
    check(len(ab) == 305, 'Abruzzo: 305 comuni')
    zone = {}
    for v in ab:
        zone[v[3]] = zone.get(v[3], 0) + 1
    check(zone == {'1': 153, '2': 125, '3': 27},
          f'Abruzzo: distribuzione zone = Allegato B Decreto 4/2024 (1:153, 2:125, 3:27) -> {zone}')
    attesi = {  # comune -> codice DPC
        ('Ortona', 'CH'): '3', ('Francavilla al Mare', 'CH'): '2', ('Arielli', 'CH'): '2',
        ('Popoli Terme', 'PE'): '1', ("L'Aquila", 'AQ'): '1', ('Roma', 'RM'): '2A-3A-3B',
        ('Agliè', 'TO'): '3',
    }
    idx = {(v[0], v[1]): v[3] for v in com.values()}
    for k, z in attesi.items():
        check(idx.get(k) == z, f'zona {k[0]} ({k[1]}) = {z} -> {idx.get(k)}')

    # ---------------- Storia sismica ----------------
    S = json.load(open(fs, encoding='utf-8'))
    m = S['meta']
    check(m['n_terremoti'] == 4894, 'CPTI15 v4.0: 4.894 terremoti (descrizione INGV)')
    n = len(S['obs']['pl'])
    check(len(S['obs']['eq']) == len(S['obs']['int']) == n, 'osservazioni: array paralleli coerenti')
    pid = S['pl']['id'].index('IT_57933')
    check(S['pl']['nome'][pid] == 'Ortona', 'IT_57933 = Ortona')
    eq, codes = S['eq'], S['int']['codici']
    storia = sorted(
        [(eq['y'][e], eq['mo'][e] or 0, eq['d'][e] or 0, codes[i])
         for p, e, i in zip(S['obs']['pl'], S['obs']['eq'], S['obs']['int']) if p == pid])
    rif = [(1627, 7, 30, '7'), (1694, 9, 8, '3'), (1873, 3, 12, '4'), (1881, 9, 10, '6-7'),
           (1882, 2, 12, '7'), (1895, 8, 9, '5-6'), (1901, 10, 15, 'NF'), (1905, 8, 18, 'F'),
           (1907, 1, 23, '3-4'), (1915, 1, 13, '5'), (1930, 7, 23, '4'), (1937, 7, 17, '3'),
           (1979, 9, 19, '4'), (1980, 11, 23, '4-5'), (1984, 4, 29, 'NF'), (1984, 5, 7, '5-6'),
           (1984, 5, 11, '5'), (1992, 2, 18, '4-5'), (1992, 7, 16, '5'), (1997, 9, 26, '3'),
           (2002, 11, 1, '4-5'), (2003, 3, 29, '2'), (2004, 11, 25, '3-4'), (2004, 12, 9, 'NF')]
    check(storia == rif, f'Ortona: 24 eventi identici al riferimento INGV ({len(storia)} trovati)')

    print()
    if errori:
        print(f'{len(errori)} controlli FALLITI')
        sys.exit(1)
    print('Tutti i controlli superati.')


if __name__ == '__main__':
    main()
