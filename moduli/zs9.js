/* ==========================================================================
   zs9.js — modulo ZS9 v1.0.0 (GeoHub)
   Magnitudo di riferimento Mw dalla zonazione sismogenetica ZS9, secondo la
   procedura dell'App. A1 delle Linee guida LQ v1.0.

   Modulo autonomo: solo dati e calcolo, nessun codice di interfaccia, nessun
   accesso alla rete. Funziona nel browser (oggetto globale ZS9) e in Node.js
   (require). Pensato per essere copiato senza modifiche in altre app GeoHub.

   Uso:
     const esito = ZS9.valuta(lat, lon, dati);
       lat, lon  coordinate del sito in gradi decimali, WGS84
       dati      contenuto di dati/zs9-data.json (formato geohub-zs9/1)

   Fonti
   - Poligoni: Meletti C., Galadini F., Valensise G., Stucchi M., Basili R.,
     Barba S., Vannucci G., Boschi E. (2004). Zonazione sismogenetica ZS9
     [Data set]. INGV, https://doi.org/10.13127/sh/zs9 — CC BY 4.0.
     File ZS9.ZIP del 06/05/2004 (zonesismiche.mi.ingv.it), convertito con
     strumenti/convert_zs9.py.
   - Mw,max per zona: Commissione tecnica per la microzonazione sismica
     (2018). Microzonazione sismica. Linee guida per la gestione del
     territorio in aree interessate da liquefazioni (LQ), v1.0, Tab. A1.1,
     pag. 31 — CC BY 4.0. Non si usa la Tab. 3.1 del volume CNR-CentroMS
     (2024), che omette la riga delle zone 923 e 927 (Mw,max 7,06).
   - Siti interni: Mw = Mw,max della zona (Linee guida LQ, pag. 30).
   - Siti esterni (Linee guida LQ, pag. 30): distanze minime R_i dalle zone,
     Ms_i = 1 + 3·log10(R_i); se per almeno una zona Ms_i < M_i si assume
     la Mw più alta fra le zone; altrimenti disaggregazione. Le Linee guida
     non definiscono le «zone circostanti»: il modulo applica
     l'interpretazione decisa il 12/11/2026 (tutte le 36 zone; Mw = massima
     M_i fra le zone con Ms_i < M_i), dichiarata nei testi.

   Calcoli
   - Appartenenza a una zona: regola pari-dispari sugli anelli in gradi
     lon/lat (i lati del poligono sono segmenti in lon/lat, come nel file).
     Un punto sul bordo (entro 1 m) è considerato interno alla zona.
   - Distanza dal bordo: per ogni lato, minimo della distanza geodetica sul
     ellissoide WGS84 (formula inversa di Vincenty, 1975) dai punti del lato;
     il minimo lungo il lato si cerca con un campionamento a 17 punti e un
     raffinamento a sezione aurea (precisione < 1 mm).
   - Il file ZS9 non dichiara il datum (manca il .prj): le coordinate WGS84
     del sito si confrontano direttamente con quelle del file. Lo scarto
     atteso è dell'ordine di 100 m, trascurabile alla scala delle zone ma
     rilevante per i siti a meno di 0,5 km da un bordo (avviso).
   ========================================================================== */
(function (radice, fabbrica) {
  'use strict';
  if (typeof module === 'object' && module.exports) module.exports = fabbrica();
  else radice.ZS9 = fabbrica();
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  const VERSIONE = '1.0.0';
  const FORMATO_DATI = 'geohub-zs9/1';

  /* Tab. A1.1 delle Linee guida LQ v1.0, pag. 31: Mw,max per zona ZS9 */
  const TAB_A1_1 = [
    { mw: 5.45, area: 'Colli Albani, Etna', zone: [922, 936] },
    { mw: 5.91, area: 'Ischia-Vesuvio', zone: [928] },
    { mw: 6.14, area: 'Altre zone', zone: [901, 902, 903, 904, 907, 908, 909, 911, 912, 913, 914, 916, 917, 920, 921, 926, 932, 933, 934] },
    { mw: 6.37, area: 'Medio-Marchigiana/Abruzzese, Appennino Umbro, Nizza Sanremo', zone: [918, 919, 910] },
    { mw: 6.60, area: 'Friuli-Veneto orientale, Garda-Veronese, Garfagnana-Mugello, Calabria ionica', zone: [905, 906, 915, 930] },
    { mw: 6.83, area: 'Molise-Gargano, Ofanto, Canale d\'Otranto', zone: [924, 925, 931] },
    { mw: 7.06, area: 'Appennino Abruzzese, Sannio–Irpinia-Basilicata', zone: [923, 927] },
    { mw: 7.29, area: 'Calabria tirrenica, Iblei', zone: [929, 935] }
  ];
  const MW_MAX = {}, AREA = {};
  TAB_A1_1.forEach(r => r.zone.forEach(z => { MW_MAX[z] = r.mw; AREA[z] = r.area; }));

  /* Soglie del modulo (scelte dichiarate, non normative) */
  const SOGLIA_BORDO_KM = 0.5;    // avviso: sito vicino a un bordo di zona
  const TOLL_BORDO_KM = 0.001;    // 1 m: punto sul bordo = interno alla zona
  /* Dominio: riquadro che contiene il territorio italiano e tutte le zone */
  const DOMINIO = { latMin: 35.0, latMax: 48.0, lonMin: 6.0, lonMax: 19.5 };

  const FONTI = {
    zs9: 'Meletti C., Galadini F., Valensise G., Stucchi M., Basili R., Barba S., Vannucci G., Boschi E. (2004). Zonazione sismogenetica ZS9 [Data set]. Istituto Nazionale di Geofisica e Vulcanologia (INGV). https://doi.org/10.13127/sh/zs9 – CC BY 4.0.',
    linee_guida: 'Commissione tecnica per la microzonazione sismica (2018). Microzonazione sismica. Linee guida per la gestione del territorio in aree interessate da liquefazioni (LQ), versione 1.0. Dipartimento della Protezione Civile, Roma – CC BY 4.0. Tab. A1.1 (pag. 31); procedura ZS9 (pag. 30); criticità (pag. 31–32).'
  };
  const TESTI = {
    dato: 'Poligoni ZS9 dal file ufficiale INGV ZS9.ZIP del 06/05/2004 (shapefile senza file .prj: datum non dichiarato). Le coordinate WGS84 del sito sono confrontate direttamente con quelle del file: lo scarto atteso è dell\'ordine di 100 m, trascurabile alla scala delle zone.',
    dentro: 'Sito interno a una zona ZS9: Mw = Mw,max della zona (Linee guida LQ, pag. 30; Tab. A1.1, pag. 31).',
    fuori: 'Sito esterno alle zone ZS9: per ciascuna delle 36 zone distanza minima R_i del sito dal bordo, calcolata sull\'ellissoide WGS84 (Vincenty), e Ms_i = 1 + 3·log10(R_i) con R_i in km. Una zona conta se Ms_i < M_i (M_i = Mw,max della zona, Tab. A1.1); Mw proposta = massima M_i fra le zone che contano; se nessuna conta, si ricorre alla disaggregazione. Criterio: interpretazione della regola delle Linee guida LQ, pag. 30, che non definisce le «zone circostanti».',
    criticita: 'Criticità dichiarate dalle Linee guida LQ (pag. 31–32): le zone ZS9 sono molto estese e in alcuni settori la Mw può essere sovrastimata; per i siti esterni alle zone (es. aree costiere) la disaggregazione può comportare una sottostima.'
  };

  /* ---------------- Geodesia: ellissoide WGS84 ---------------- */
  const A = 6378137.0, F = 1 / 298.257223563, B = A * (1 - F);
  const RAD = Math.PI / 180;

  /* Formula inversa di Vincenty (1975): distanza geodetica in metri.
     Vincenty T. (1975). Direct and inverse solutions of geodesics on the
     ellipsoid with application of nested equations. Survey Review 23(176),
     88–93. Converge per tutti i punti non quasi antipodali (sempre, alla
     scala dell'Italia). */
  function distanzaGeodetica(lat1, lon1, lat2, lon2) {
    const L = (lon2 - lon1) * RAD;
    const U1 = Math.atan((1 - F) * Math.tan(lat1 * RAD));
    const U2 = Math.atan((1 - F) * Math.tan(lat2 * RAD));
    const sinU1 = Math.sin(U1), cosU1 = Math.cos(U1), sinU2 = Math.sin(U2), cosU2 = Math.cos(U2);
    let lambda = L, iter = 0, sinSigma, cosSigma, sigma, cos2Alpha, cos2SigmaM;
    for (;;) {
      const sinL = Math.sin(lambda), cosL = Math.cos(lambda);
      sinSigma = Math.sqrt((cosU2 * sinL) ** 2 + (cosU1 * sinU2 - sinU1 * cosU2 * cosL) ** 2);
      if (sinSigma === 0) return 0;
      cosSigma = sinU1 * sinU2 + cosU1 * cosU2 * cosL;
      sigma = Math.atan2(sinSigma, cosSigma);
      const sinAlpha = cosU1 * cosU2 * sinL / sinSigma;
      cos2Alpha = 1 - sinAlpha * sinAlpha;
      cos2SigmaM = cos2Alpha !== 0 ? cosSigma - 2 * sinU1 * sinU2 / cos2Alpha : 0;
      const C = F / 16 * cos2Alpha * (4 + F * (4 - 3 * cos2Alpha));
      const prec = lambda;
      lambda = L + (1 - C) * F * sinAlpha *
        (sigma + C * sinSigma * (cos2SigmaM + C * cosSigma * (-1 + 2 * cos2SigmaM * cos2SigmaM)));
      if (Math.abs(lambda - prec) < 1e-12) break;
      if (++iter > 200) throw new Error('Vincenty: nessuna convergenza');
    }
    const u2 = cos2Alpha * (A * A - B * B) / (B * B);
    const AA = 1 + u2 / 16384 * (4096 + u2 * (-768 + u2 * (320 - 175 * u2)));
    const BB = u2 / 1024 * (256 + u2 * (-128 + u2 * (74 - 47 * u2)));
    const dSigma = BB * sinSigma * (cos2SigmaM + BB / 4 * (cosSigma * (-1 + 2 * cos2SigmaM * cos2SigmaM) -
      BB / 6 * cos2SigmaM * (-3 + 4 * sinSigma * sinSigma) * (-3 + 4 * cos2SigmaM * cos2SigmaM)));
    return B * AA * (sigma - dSigma);
  }

  /* Distanza minima in km dal punto al lato A-B (segmento in lon/lat) */
  const PHI = (Math.sqrt(5) - 1) / 2;
  function distanzaLatoKm(lat, lon, lo1, la1, lo2, la2) {
    const d = t => distanzaGeodetica(lat, lon, la1 + t * (la2 - la1), lo1 + t * (lo2 - lo1));
    const N = 16;
    let kMin = 0, dMin = Infinity;
    for (let k = 0; k <= N; k++) { const v = d(k / N); if (v < dMin) { dMin = v; kMin = k; } }
    let a = Math.max(0, (kMin - 1) / N), b = Math.min(1, (kMin + 1) / N);
    let c = b - PHI * (b - a), e = a + PHI * (b - a), fc = d(c), fe = d(e);
    for (let i = 0; i < 60 && (b - a) > 1e-12; i++) {
      if (fc < fe) { b = e; e = c; fe = fc; c = b - PHI * (b - a); fc = d(c); }
      else { a = c; c = e; fc = fe; e = a + PHI * (b - a); fe = d(e); }
    }
    return Math.min(dMin, fc, fe, d(0), d(1)) / 1000;
  }

  function distanzaBordoKm(lat, lon, zona) {
    let m = Infinity;
    for (const r of zona.anelli)
      for (let i = 2; i < r.length; i += 2)
        m = Math.min(m, distanzaLatoKm(lat, lon, r[i - 2], r[i - 1], r[i], r[i + 1]));
    return m;
  }

  /* Regola pari-dispari su un anello piatto [lon, lat, ...] */
  function dentroAnello(lat, lon, r) {
    let dentro = false;
    for (let i = 0, j = r.length - 2; i < r.length; j = i, i += 2) {
      const xi = r[i], yi = r[i + 1], xj = r[j], yj = r[j + 1];
      if ((yi > lat) !== (yj > lat) && lon < (xj - xi) * (lat - yi) / (yj - yi) + xi) dentro = !dentro;
    }
    return dentro;
  }
  function dentroZona(lat, lon, zona) {
    let n = 0;
    for (const r of zona.anelli) if (dentroAnello(lat, lon, r)) n++;
    return n % 2 === 1;
  }

  /* ---------------- Dati ---------------- */
  const _pronti = typeof WeakMap === 'function' ? new WeakMap() : null;
  function prepara(dati) {
    if (_pronti && _pronti.has(dati)) return _pronti.get(dati);
    if (!dati || !dati.meta || dati.meta.formato !== FORMATO_DATI || !Array.isArray(dati.zone))
      throw new Error('dati ZS9 non validi: atteso il formato ' + FORMATO_DATI);
    const zone = dati.zone.map(z => {
      const id = Number(z.id);
      if (!(id in MW_MAX)) throw new Error('dati ZS9 non validi: zona ' + z.id + ' assente dalla Tab. A1.1');
      if (!Array.isArray(z.anelli) || !z.anelli.length) throw new Error('dati ZS9 non validi: zona ' + id + ' senza geometria');
      z.anelli.forEach(r => {
        if (!Array.isArray(r) || r.length < 8 || r.length % 2 || !r.every(Number.isFinite))
          throw new Error('dati ZS9 non validi: anello della zona ' + id);
      });
      return { id, anelli: z.anelli };
    });
    const ids = zone.map(z => z.id);
    if (zone.length !== 36 || new Set(ids).size !== 36)
      throw new Error('dati ZS9 non validi: attese 36 zone distinte');
    const p = { zone };
    if (_pronti) _pronti.set(dati, p);
    return p;
  }

  /* ---------------- Funzione principale ---------------- */
  function valuta(lat, lon, dati) {
    const r = {
      modulo: 'zs9', versione: VERSIONE,
      ingresso: { lat, lon },
      esito: null,              // 'dentro_zona' | 'fuori_zona' | 'disaggregazione_richiesta' | 'fuori_dominio' | 'dati_non_validi'
      dentro: false,
      zona: null,               // zona che contiene il sito (o con Mw più alta, se il sito è sul bordo comune)
      zone_contenenti: [],
      mw: null,                 // Mw proposta, numero o null
      zone_mw: [],              // zone da cui deriva la Mw proposta
      area_mw: null,            // area della Tab. A1.1
      distanza_bordo_km: null,  // dentro: distanza dal bordo della zona; fuori: R minima
      tabella: null,            // solo fuori zona: [{zona, r_km, ms, m, conta}], per R crescente
      avvisi: [],               // [{codice, testo}]
      testi: TESTI, fonti: FONTI
    };
    const avviso = (codice, testo) => r.avvisi.push({ codice, testo });

    if (typeof lat !== 'number' || typeof lon !== 'number' || !Number.isFinite(lat) || !Number.isFinite(lon) ||
        Math.abs(lat) > 90 || Math.abs(lon) > 180) {
      r.esito = 'dati_non_validi';
      avviso('coordinate_non_valide', 'Coordinate non valide: servono latitudine e longitudine in gradi decimali (WGS84).');
      return r;
    }
    const nelDominio = (la, lo) => la >= DOMINIO.latMin && la <= DOMINIO.latMax && lo >= DOMINIO.lonMin && lo <= DOMINIO.lonMax;
    if (!nelDominio(lat, lon)) {
      r.esito = 'fuori_dominio';
      avviso('fuori_dominio', 'Il punto è fuori dal territorio coperto dalla zonazione ZS9 (Italia): la magnitudo non è valutata.');
      if (nelDominio(lon, lat)) avviso('coordinate_invertite', 'Latitudine e longitudine sembrano invertite: scambiandole il punto cadrebbe in Italia.');
      return r;
    }
    const P = prepara(dati);

    /* Sito interno */
    for (const z of P.zone) if (dentroZona(lat, lon, z)) r.zone_contenenti.push(z.id);
    /* Sito sul bordo (entro 1 m) di una zona che la regola pari-dispari non conta */
    const vicine = P.zone.filter(z => r.zone_contenenti.indexOf(z.id) < 0)
      .map(z => ({ z, d: distanzaBordoKm(lat, lon, z) }));
    vicine.filter(v => v.d <= TOLL_BORDO_KM).forEach(v => r.zone_contenenti.push(v.z.id));

    if (r.zone_contenenti.length) {
      r.zone_contenenti.sort((a, b) => MW_MAX[b] - MW_MAX[a] || a - b);
      r.esito = 'dentro_zona';
      r.dentro = true;
      r.zona = r.zone_contenenti[0];
      r.mw = MW_MAX[r.zona];
      r.zone_mw = [r.zona];
      r.area_mw = AREA[r.zona];
      const z = P.zone.find(q => q.id === r.zona);
      r.distanza_bordo_km = distanzaBordoKm(lat, lon, z);
      if (r.zone_contenenti.length > 1)
        avviso('bordo_comune', 'Il sito è sul bordo comune delle zone ' + r.zone_contenenti.join(' e ') +
          ': si adotta la Mw,max più alta (zona ' + r.zona + ').');
      else if (r.distanza_bordo_km < SOGLIA_BORDO_KM)
        avviso('vicino_bordo', 'Il sito dista meno di 0,5 km dal bordo della zona ' + r.zona +
          ': l\'attribuzione risente del datum non dichiarato del file ZS9 (scarto atteso circa 100 m) e va verificata.');
      return r;
    }

    /* Sito esterno: tabella completa delle 36 zone */
    r.tabella = vicine.map(v => {
      const m = MW_MAX[v.z.id], ms = 1 + 3 * Math.log10(v.d);
      return { zona: v.z.id, r_km: v.d, ms, m, conta: ms < m };
    }).sort((a, b) => a.r_km - b.r_km || a.zona - b.zona);
    r.distanza_bordo_km = r.tabella[0].r_km;
    if (r.distanza_bordo_km < SOGLIA_BORDO_KM)
      avviso('vicino_bordo', 'Il sito dista meno di 0,5 km dal bordo della zona ' + r.tabella[0].zona +
        ': l\'attribuzione al di fuori delle zone risente del datum non dichiarato del file ZS9 (scarto atteso circa 100 m) e va verificata.');
    const contano = r.tabella.filter(t => t.conta);
    if (!contano.length) {
      r.esito = 'disaggregazione_richiesta';
      avviso('disaggregazione', 'Nessuna zona soddisfa Ms_i < M_i: le Linee guida LQ (pag. 30) rinviano alla disaggregazione della pericolosità, non calcolata da questo modulo.');
      return r;
    }
    const mMax = Math.max(...contano.map(t => t.m));
    r.esito = 'fuori_zona';
    r.mw = mMax;
    r.zone_mw = contano.filter(t => t.m === mMax).map(t => t.zona);
    r.area_mw = AREA[r.zone_mw[0]];
    return r;
  }

  return {
    VERSIONE, FORMATO_DATI, TAB_A1_1, MW_MAX, FONTI, TESTI, SOGLIA_BORDO_KM, DOMINIO,
    valuta,
    /* esposte per le verifiche */
    distanzaGeodetica, distanzaBordoKm, dentroZona
  };
});
