# SismaSite

**Parametri sismici del sito secondo le NTC 2018**, direttamente nel browser.

**[Apri l'app →](https://fabio-duronio.github.io/geohub-sismasite/)**

![SismaSite](assets/og-image.png)

Applicazione web per geologi e ingegneri: dato un punto sulla mappa restituisce la pericolosità sismica di base, gli spettri di risposta e un inquadramento sismico del sito, secondo il **D.M. 17/01/2018 (NTC 2018)**, la **Circolare n. 7/2019** e gli **Allegati A e B al D.M. 14/01/2008**. Non richiede installazione né registrazione; i calcoli avvengono nel browser.

## Cosa fa

- **Pericolosità di base**: `a_g`, `F_0`, `T*_C` per SLO, SLD, SLV, SLC dal reticolo ufficiale a 10.751 nodi (Allegato B; Tabella 2 per le isole), con conversione automatica delle coordinate WGS84 → ED50 e indicazione dei nodi usati.
- **Amplificazione e spettri**: `S_S`, `C_C`, `S_T`, `T_B`, `T_C`, `T_D`; spettri elastici orizzontale e verticale, anche per i 4 stati limite a confronto; spettri di progetto con fattore `q` scelto dal progettista; spettri per i 9 periodi di ritorno del reticolo.
- **Coefficienti sismici** `k_h`, `k_v` per le verifiche pseudostatiche dei pendii e **screening di liquefazione** (criteri di esclusione 1 e 2).
- **Inquadramento sismico**: comune e classificazione (ISTAT, DPC), eventi strumentali INGV, storia sismica (DBMI15) e terremoti storici (CPTI15), faglie capaci (ISPRA ITHACA).
- **Mappa** con la carta di pericolosità INGV MPS04.
- **Stampa A4 come allegato alla relazione**, con intestazione, numerazione delle pagine, note metodologiche e fonti.
- **Esportazione CSV** dei parametri e dei punti degli spettri, per Excel o per il software di calcolo strutturale.

## Come si usa

1. Clicca sulla mappa o inserisci le coordinate (WGS84).
2. Imposta vita nominale, classe d'uso, categoria di sottosuolo e topografica, smorzamento e `q`.
3. Premi **Calcola parametri sismici** e consulta le schede Parametri, Spettri, Inquadramento sismico.
4. Per allegare i risultati alla relazione usa **Stampa / Salva PDF** (consigliati Chrome o Edge).

## Esempio di controllo

Per verificare subito i risultati: L'Aquila, lat **42,3499**, lon **13,3995** (WGS84), `V_N` = 50 anni, classe d'uso II, categoria **B**, topografia **T1**, ξ = 5 %, `q` = 1,5. Allo **SLV** (`T_R` = 475 anni) l'app restituisce:

| a_g (g) | F_0 | T*_C (s) | S_S | a_max (g) | k_h | S_d plateau (g) | S_dv(0) (g) |
|---|---|---|---|---|---|---|---|
| 0,261 | 2,36 | 0,347 | 1,154 | 0,301 | 0,0842 | 0,4738 | 0,1797 |

Gli stessi valori, con altre località, sono la base dei controlli automatici: vedi [Validazione](docs/validazione.md).

## Perimetro d'uso

È uno strumento di supporto per il professionista: **non** sostituisce la relazione geologica e geotecnica, non esegue analisi di risposta sismica locale e non sceglie il fattore `q`. Le scelte di progetto e l'impiego dei risultati restano a carico del professionista. Dettagli in [Metodo e limiti](docs/metodo.md#limiti-e-perimetro-duso).

## Documentazione

- [Metodo di calcolo e limiti](docs/metodo.md)
- [Validazione](docs/validazione.md): confronto con il testo ufficiale, calcolo indipendente, valori di riferimento
- [Sviluppo e dati](docs/sviluppo.md): struttura del repository, avvio in locale, rigenerazione dei dati
- [Novità delle versioni](CHANGELOG.md)
- Segnala una discrepanza di calcolo o proponi una funzione dalla scheda [Issues](https://github.com/fabio-duronio/geohub-sismasite/issues/new/choose)

## Licenza e citazione

Copyright © 2026 Fabio Duronio, geologo. Licenza **GNU AGPL-3.0** con termini aggiuntivi ([LICENSE](LICENSE), [NOTICE](NOTICE)):

- **Uso libero**, anche professionale, per relazioni, progetti e studi.
- **Chi modifica o ridistribuisce** il codice, anche come servizio web, deve rilasciarlo con la stessa licenza e renderne disponibile il sorgente.
- **Attribuzione obbligatoria**: le versioni derivate riportano nell'interfaccia "Basato su SismaSite di Fabio Duronio, geologo" con il link a questo repository.
- **Nomi**: "SismaSite" e "GeoHub" non sono concessi in licenza; le versioni modificate usano un nome diverso.
- **Licenze commerciali** diverse dalla AGPL sono disponibili su richiesta.

Le versioni fino alla 1.3.1 sono state pubblicate con licenza MIT.

Dati: Ministero delle Infrastrutture e dei Trasporti (Allegato B al D.M. 14/01/2008); Dipartimento della Protezione Civile e ISTAT (CC BY 4.0); INGV (FDSN e MPS04, CC BY 4.0; CPTI15 e DBMI15 v4.0, CC BY-SA 4.0); ISPRA (ITHACA, CC BY 4.0). Citazioni complete in [NOTICE](NOTICE).

Per citare lo strumento: *Duronio F., SismaSite (GeoHub-SismaSite), parametri sismici del sito secondo NTC 2018, versione X.Y.Z, https://github.com/fabio-duronio/geohub-sismasite*.
