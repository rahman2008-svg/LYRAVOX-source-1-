/* ============================================================
   LYRAVOX — Bangla (বাংলা) support
   1. language: detection, Bengali faces (Noto Sans / Serif Bengali, Hind Siliguri, Baloo Da 2, Tiro Bangla, Galada, Atma, Mina),
      random-character pools
   2. grapheme clusters: Bangla conjuncts and vowel signs (ক্ষ, স্ত্র, কি, ো …) must never be cut apart. The engine splits text
      with [...text] (code points) in hundreds of places, so the planner packs every multi-code-point cluster into ONE private-use
      character (U+E000…) and the canvas text calls turn it back into the real cluster at draw / measure time. Everything between
      (layouts, chunking, per-character animation) therefore sees one character per cluster, exactly like Japanese.
   ============================================================ */
(() => {
'use strict';

/* ---------- 2. cluster packing ---------- */
const MARK = c => (c >= 0x981 && c <= 0x983) || c === 0x9bc || (c >= 0x9be && c <= 0x9cc) || c === 0x9d7 || c === 0x9e2 || c === 0x9e3 || c === 0x9fe;
const VIR = 0x9cd;
const ZW = c => c === 0x200c || c === 0x200d;
const CONS = c => (c >= 0x995 && c <= 0x9b9) || c === 0x9dc || c === 0x9dd || c === 0x9df || c === 0x9f0 || c === 0x9f1 || c === 0x9ce;
const ANYMARK = /\p{M}/u;
const NEEDS = /[\u0980-\u09ff\u200c\u200d\u0300-\u036f]|\p{M}/u;
const C2P = new Map(), P2C = [];
let packed = false;
const PUA0 = 0xe000, PUAN = 0x1900;     // U+E000 … U+F8FF

/* split text into clusters (Bangla: base + signs + hasanta-joined consonants; other scripts: base + any combining mark) */
J.clusters = (s) => {
  const cps = [...String(s)], out = [];
  for (let i = 0; i < cps.length; i++) {
    let cl = cps[i];
    const first = cl.codePointAt(0), bn = first >= 0x980 && first <= 0x9ff;
    while (i + 1 < cps.length) {
      const n = cps[i + 1], c = n.codePointAt(0);
      if (bn || (c >= 0x980 && c <= 0x9ff)) {
        if (MARK(c)) { cl += n; i++; continue; }
        if (c === VIR) {
          cl += n; i++;
          if (i + 1 < cps.length && ZW(cps[i + 1].codePointAt(0))) { cl += cps[i + 1]; i++; }
          if (i + 1 < cps.length && CONS(cps[i + 1].codePointAt(0))) { cl += cps[i + 1]; i++; continue; }
          break;
        }
        if (ZW(c) && cl.codePointAt(cl.length - 1) === VIR) { cl += n; i++; continue; }
      }
      if (ANYMARK.test(n) || ZW(c) && /\p{L}$/u.test(cl) && i + 2 < cps.length && ANYMARK.test(cps[i + 2])) { cl += n; i++; continue; }
      break;
    }
    out.push(cl);
  }
  return out;
};
J.packText = (s) => {
  s = s == null ? '' : String(s);
  if (!NEEDS.test(s)) return s;
  let out = '';
  for (const cl of J.clusters(s)) {
    if (cl.length === 1 || [...cl].length === 1) { out += cl; continue; }
    let p = C2P.get(cl);
    if (p === undefined) {
      if (P2C.length >= PUAN) { out += cl; continue; }          // table full: leave unpacked (still readable, just splittable)
      p = String.fromCharCode(PUA0 + P2C.length); P2C.push(cl); C2P.set(cl, p);
    }
    packed = true; out += p;
  }
  return out;
};
const PUA_RE = /[\ue000-\uf8ff]/g;
J.unpackText = (s) => (typeof s === 'string' && packed ? s.replace(PUA_RE, c => P2C[c.charCodeAt(0) - PUA0] || c) : s);
J.unpackJSON = (obj, space) => JSON.stringify(obj, (k, v) => (typeof v === 'string' ? J.unpackText(v) : v), space);

/* canvas text calls: unpack just before the browser shapes the text */
const hasPua = s => { for (let i = 0; i < s.length; i++) { const c = s.charCodeAt(i); if (c >= 0xe000 && c <= 0xf8ff) return true; } return false; };
for (const Ctx of [window.CanvasRenderingContext2D, window.OffscreenCanvasRenderingContext2D]) {
  if (!Ctx) continue;
  for (const m of ['fillText', 'strokeText', 'measureText']) {
    const orig = Ctx.prototype[m];
    if (typeof orig !== 'function') continue;
    Ctx.prototype[m] = function (t, ...rest) { return orig.call(this, packed && typeof t === 'string' && hasPua(t) ? J.unpackText(t) : t, ...rest); };
  }
}

/* ---------- 1. language ---------- */
J.LANGS.push('bn');
J.LANG_LABEL.bn = 'বাংলা';
const BN_LET = /[\u0985-\u09b9\u09bc-\u09cd\u09ce\u09dc-\u09e3\u09f0\u09f1]/;
const baseDetect = J.detectLang;
J.detectLang = (text) => {
  let bn = 0, other = 0;
  for (const c of String(text || '')) {
    const u = c.codePointAt(0);
    if (u >= 0x980 && u <= 0x9ff) { if (BN_LET.test(c)) bn++; }
    else if ((u >= 0x41 && u <= 0x5a) || (u >= 0x61 && u <= 0x7a) || (u >= 0x3040 && u <= 0x30ff) || (u >= 0x4e00 && u <= 0x9fff) || (u >= 0xac00 && u <= 0xd7a3)) other++;
  }
  if (bn >= 2 && bn >= other * 0.5) return 'bn';
  return baseDetect(text);
};
const F = (family, weight, gf) => ({ family, weight, gf });
const NSB = 'Noto+Sans+Bengali:wght@300;500;700;900', NSRB = 'Noto+Serif+Bengali:wght@300;500;700;800;900';
const HS = (w) => F('Hind Siliguri', w, 'Hind+Siliguri:wght@' + w), BD = (w) => F('Baloo Da 2', w, 'Baloo+Da+2:wght@' + w);
J.LANG_FACES.bn = {
  sans: F('Noto Sans Bengali', 500, NSB), serif: F('Noto Serif Bengali', 500, NSRB),
  fbSans: '"Noto Sans Bengali","Hind Siliguri","Noto Sans Bangla","Nirmala UI","Vrinda","Bangla Sangam MN","Kohinoor Bangla","Lohit Bengali","FreeSans"',
  fbSerif: '"Noto Serif Bengali","Tiro Bangla","Noto Sans Bengali","Nirmala UI","Bangla MN","Kohinoor Bangla","Lohit Bengali","FreeSerif"',
  map: {
    gothic_black: F('Noto Sans Bengali', 900, NSB), gothic_bold: F('Noto Sans Bengali', 700, NSB), gothic_med: F('Noto Sans Bengali', 500, NSB),
    gothic_light: F('Noto Sans Bengali', 300, NSB), zenkaku: HS(700), sansui: HS(500),
    mincho_black: F('Noto Serif Bengali', 900, NSRB), mincho_bold: F('Noto Serif Bengali', 700, NSRB), mincho: F('Noto Serif Bengali', 500, NSRB),
    mincho_light: F('Noto Serif Bengali', 300, NSRB), tokumin: F('Noto Serif Bengali', 800, NSRB), shippori: F('Noto Serif Bengali', 800, NSRB),
    dela: F('Atma', 700, 'Atma:wght@700'), round: BD(700), pop: BD(800), kiwi: F('Mina', 400, 'Mina'),
    klee: F('Tiro Bangla', 400, 'Tiro+Bangla'), brush: F('Galada', 400, 'Galada'),
    reggae: F('Atma', 700, 'Atma:wght@700'), rampart: F('Atma', 700, 'Atma:wght@700'), potta: F('Galada', 400, 'Galada'),
  },
};
const BN_CH = 'অআইঈউঊঋএঐওঔকখগঘঙচছজঝঞটঠডঢণতথদধনপফবভমযরলশষসহ', BN_DIG = '০১২৩৪৫৬৭৮৯';
J.POOLS.bn = { kana: BN_CH, hira: BN_CH, half: BN_DIG + BN_CH.slice(0, 12), reel: BN_CH.slice(0, 30) + BN_DIG, scramble: BN_CH + BN_DIG, signs: BN_CH.slice(0, 40) + '01' };
const baseSeg = J.segLocale;
J.segLocale = () => (J.lang === 'bn' ? 'en' : baseSeg());
})();
