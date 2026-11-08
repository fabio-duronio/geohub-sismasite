#!/usr/bin/env python3
"""
convert_classificazione.py — SismaSite (GeoHub)

Converte l'elenco nazionale della classificazione sismica dei comuni pubblicato
dal Dipartimento della Protezione Civile ("Classificazione sismica aggiornata a
maggio 2025", CSV separato da ';') in un file JSON compatto per l'app.

Uso:
    python3 strumenti/convert_classificazione.py <file.csv> [classificazione-data.json] [comuni-data.json]

Se si indica comuni-data.json (confini ISTAT, vedi convert_comuni.py), le chiavi
vengono allineate ai codici ISTAT dei confini: i comuni il cui codice DPC non
esiste più nei confini (es. Sardegna dopo il riordino delle province) sono
abbinati per nome esatto, solo se l'abbinamento è univoco; il codice DPC
originale resta nel quinto campo. Qualunque comune non abbinato interrompe la
conversione.

Il file CSV va scaricato dalla pagina ufficiale:
    https://rischi.protezionecivile.gov.it/it/sismico/attivita/classificazione-sismica/

Regole (decisioni GeoHub, 02/11/2026):
- il codice di zona è riportato ESATTAMENTE come nel file DPC (es. 2B, 3S, 1a,
  2A-3A-3B): nessuna conversione;
- la "zona principale" è ricavata dalle cifre del codice (2B -> 2; 1-2A -> 1, 2);
- nessun valore di ag: la classificazione ha solo valore programmatorio e
  amministrativo e non entra nel calcolo NTC 2018.

Fonte: Dipartimento della Protezione Civile - Presidenza del Consiglio dei
Ministri, licenza CC BY 4.0 (note legali www.protezionecivile.gov.it).
"""
import csv
import json
import os
import re
import sys
from datetime import date

ATTESI = ['REGIONE', 'PROV_CITTA_METROPOLITANA', 'SIGLA_PROV', 'COMUNE',
          'COD_ISTAT_COMUNE', 'ZONA_SISMICA']
CODICE_VALIDO = re.compile(r'^[1-4][A-Za-z]?(-[1-4][A-Za-z]?)*$')


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    src = sys.argv[1]
    dst = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'dati', 'classificazione-data.json')

    with open(src, encoding='utf-8-sig', newline='') as f:
        rd = csv.DictReader(f, delimiter=';')
        if rd.fieldnames != ATTESI:
            sys.exit(f'Intestazione inattesa: {rd.fieldnames}')
        righe = list(rd)

    regioni, comuni, anomalie = [], {}, []
    for r in righe:
        codice = r['ZONA_SISMICA'].strip()
        istat = r['COD_ISTAT_COMUNE'].strip()
        if not CODICE_VALIDO.match(codice):
            anomalie.append(f'codice zona non riconosciuto: {r}')
            continue
        if not istat.isdigit():
            anomalie.append(f'codice ISTAT non numerico: {r}')
            continue
        istat6 = istat.zfill(6)
        if istat6 in comuni:
            anomalie.append(f'codice ISTAT duplicato: {istat6}')
            continue
        reg = r['REGIONE'].strip()
        if reg not in regioni:
            regioni.append(reg)
        comuni[istat6] = [r['COMUNE'].strip(), r['SIGLA_PROV'].strip(),
                          regioni.index(reg), codice]

    if anomalie:
        print('\n'.join(anomalie))
        sys.exit(f'{len(anomalie)} anomalie: conversione interrotta')

    riallineati = 0
    if len(sys.argv) > 3:
        istat = {c[0]: c[1] for c in json.load(open(sys.argv[3], encoding='utf-8'))['comuni']}
        liberi = {}
        for k, nome in istat.items():
            if k not in comuni:
                liberi.setdefault(nome, []).append(k)
        nuovi = {}
        for k, v in comuni.items():
            if k in istat:
                nuovi[k] = v + [k]
                continue
            cand = liberi.get(v[0], [])
            if len(cand) != 1:
                sys.exit(f'comune DPC {k} {v[0]} non abbinabile ai confini ISTAT (candidati: {cand})')
            nuovi[cand[0]] = v + [k]
            riallineati += 1
        if len(nuovi) != len(istat):
            sys.exit(f'abbinamento incompleto: {len(nuovi)} su {len(istat)} comuni ISTAT')
        comuni = nuovi

    out = {
        'meta': {
            'titolo': 'Classificazione sismica aggiornata a maggio 2025',
            'fonte': "Dipartimento della Protezione Civile - Presidenza del Consiglio dei Ministri",
            'url': 'https://rischi.protezionecivile.gov.it/it/sismico/attivita/classificazione-sismica/',
            'atti_regionali': 'https://rischi.protezionecivile.gov.it/static/4f996d4ed8621daef1191b6955ff5c1b/normativa-regionale-di-classificazione-sismica-maggio-2025.pdf',
            'licenza': 'CC BY 4.0',
            'avviso': 'Solo fini programmatori e amministrativi: non usare per la progettazione (NTC 2018).',
            'campi': ['comune', 'sigla_provincia', 'indice_regione', 'codice_zona_DPC', 'codice_ISTAT_nel_file_DPC'],
            'chiavi': 'codici ISTAT dei confini comunali (comuni-data.json)' if len(sys.argv) > 3 else 'codici ISTAT del file DPC',
            'generato': date.today().isoformat(),
            'n_comuni': len(comuni),
            'riallineati_per_nome': riallineati,
        },
        'regioni': regioni,
        'comuni': comuni,
    }
    with open(dst, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, separators=(',', ':'))
    print(f'{dst}: {len(comuni)} comuni, {len(regioni)} regioni, {riallineati} riallineati per nome')


if __name__ == '__main__':
    main()
