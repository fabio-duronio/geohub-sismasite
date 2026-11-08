#!/usr/bin/env python3
"""
convert_storica.py — SismaSite (GeoHub)

Converte i cataloghi ufficiali INGV CPTI15 v4.0 e DBMI15 v4.0 (file xlsx) in un
file JSON compatto per i moduli di sismicità storica:
  - storia sismica della località (osservazioni macrosismiche DBMI15);
  - terremoti storici con epicentro entro un raggio dal sito (CPTI15).

Uso:
    python3 strumenti/convert_storica.py <CPTI15_v4.0.xlsx> <DBMI15_v4.0.xlsx> [storica-data.json]

File scaricabili (previa accettazione dei termini d'uso) da:
    https://emidius.mi.ingv.it/CPTI15-DBMI15/

Scelte:
- solo località italiane con identificativo (MDPplaceID) — le osservazioni senza
  identificativo (territori, località non identificate) non sono assegnabili a
  un punto e sono escluse;
- intensità riportata come nel catalogo (es. "6-7", "F", "NF"), più il valore
  numerico INGV usato solo per ordinare;
- formato colonnare (array paralleli), come grid-data.json.

Licenza dei dati: i fogli "about" dei due file indicano CC BY-SA 4.0 (le pagine
di download indicano CC BY 4.0): si adotta la più restrittiva, CC BY-SA 4.0.
Citazioni obbligatorie in meta.citazioni.
"""
import json
import os
import sys
from datetime import date

import openpyxl


def righe(path, foglio):
    ws = openpyxl.load_workbook(path, read_only=True)[foglio]
    it = ws.iter_rows(values_only=True)
    h = next(it)
    ix = {k: i for i, k in enumerate(h)}
    for r in it:
        yield ix, r


def num(v):
    return None if v in (None, '') else v


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    cpti, dbmi = sys.argv[1], sys.argv[2]
    dst = sys.argv[3] if len(sys.argv) > 3 else os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'dati', 'storica-data.json')

    # ---- CPTI15: terremoti ----
    eq_keys = ['id', 'y', 'mo', 'd', 'h', 'mi', 'area', 'lat', 'lon', 'io', 'mw', 'sect']
    eq = {k: [] for k in eq_keys}
    eq_index = {}
    for ix, r in righe(cpti, 'catalogue'):
        if r[ix['N']] is None:
            continue
        eid = r[ix['EqID']]
        if eid in eq_index:
            sys.exit(f'EqID duplicato in CPTI15: {eid}')
        eq_index[eid] = len(eq['id'])
        eq['id'].append(eid)
        eq['y'].append(r[ix['Year']])
        eq['mo'].append(num(r[ix['Mo']]))
        eq['d'].append(num(r[ix['Da']]))
        eq['h'].append(num(r[ix['Ho']]))
        eq['mi'].append(num(r[ix['Mi']]))
        eq['area'].append(r[ix['EpicentralArea']])
        eq['lat'].append(num(r[ix['LatDef']]))
        eq['lon'].append(num(r[ix['LonDef']]))
        eq['io'].append(num(r[ix['IoDef']]))
        eq['mw'].append(num(r[ix['MwDef']]))
        eq['sect'].append(r[ix['Sect']])

    # ---- DBMI15: osservazioni per località ----
    pl_keys = ['id', 'nome', 'lat', 'lon', 'istat2015', 'prov']
    pl = {k: [] for k in pl_keys}
    pl_index = {}
    ints, int_num = [], {}
    obs_pl, obs_eq, obs_int = [], [], []
    scartate_senza_id = scartate_estere = 0
    eq_mancanti = set()
    for ix, r in righe(dbmi, 'DBMI15 v4'):
        pid = r[ix['MDPplaceID']]
        if not pid:
            scartate_senza_id += 1
            continue
        if r[ix['MDPcountry']] != 'IT':
            scartate_estere += 1
            continue
        eid = r[ix['EqID']]
        if eid not in eq_index:
            eq_mancanti.add(eid)
            continue
        if pid not in pl_index:
            pl_index[pid] = len(pl['id'])
            pl['id'].append(pid)
            pl['nome'].append(r[ix['MDPplaceName']])
            pl['lat'].append(r[ix['MDPlat']])
            pl['lon'].append(r[ix['MDPlon']])
            pl['istat2015'].append(r[ix['MDPistat2015']])
            pl['prov'].append(r[ix['MDPprovince']])
        s = str(r[ix['MDPint']]).strip()
        if s not in int_num:
            int_num[s] = r[ix['MDPintNum']]
            ints.append(s)
        obs_pl.append(pl_index[pid])
        obs_eq.append(eq_index[eid])
        obs_int.append(ints.index(s))

    if eq_mancanti:
        sys.exit(f'{len(eq_mancanti)} EqID di DBMI15 assenti in CPTI15: {sorted(eq_mancanti)[:5]}…')

    out = {
        'meta': {
            'cataloghi': ['CPTI15 v4.0', 'DBMI15 v4.0'],
            'fonte': 'Istituto Nazionale di Geofisica e Vulcanologia (INGV)',
            'url': 'https://emidius.mi.ingv.it/CPTI15-DBMI15/',
            'licenza': 'CC BY-SA 4.0 (come indicato nei file; pagine di download: CC BY 4.0)',
            'citazioni': [
                'Rovida A., Locati M., Camassi R., Lolli B., Gasperini P., Antonucci A. (eds), 2022. Italian Parametric Earthquake Catalogue (CPTI15), version 4.0. Istituto Nazionale di Geofisica e Vulcanologia (INGV). https://doi.org/10.13127/CPTI/CPTI15.4',
                'Locati M., Camassi R., Rovida A., Ercolani E., Bernardini F., Castelli V., Caracciolo C.H., Tertulliani A., Rossi A., Azzaro R., D\'Amico S., Conte S., Rocchetti E., Antonucci A. (2022). Database Macrosismico Italiano (DBMI15), versione 4.0. Istituto Nazionale di Geofisica e Vulcanologia (INGV). https://doi.org/10.13127/DBMI/DBMI15.4',
            ],
            'scala': 'MCS (intensità come riportate nel catalogo)',
            'avviso': "L'assenza di un terremoto nella storia di una località non significa che non sia stato risentito: dipende dai dati disponibili in DBMI15.",
            'escluse_senza_identificativo': scartate_senza_id,
            'escluse_estero': scartate_estere,
            'generato': date.today().isoformat(),
            'n_terremoti': len(eq['id']),
            'n_localita': len(pl['id']),
            'n_osservazioni': len(obs_pl),
        },
        'eq': eq,
        'pl': pl,
        'int': {'codici': ints, 'valore_ordinamento': [int_num[s] for s in ints]},
        'obs': {'pl': obs_pl, 'eq': obs_eq, 'int': obs_int},
    }
    with open(dst, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, separators=(',', ':'))
    m = out['meta']
    print(f"{dst}: {m['n_terremoti']} terremoti, {m['n_localita']} località, "
          f"{m['n_osservazioni']} osservazioni (escluse: {scartate_senza_id} senza ID, {scartate_estere} estere)")


if __name__ == '__main__':
    main()
