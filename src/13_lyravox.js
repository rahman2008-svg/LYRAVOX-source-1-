/* ============================================================
   LYRAVOX — studio integration for the editor
   - autosaves the open project (and its song) into the Studio library (IndexedDB, this browser only)
   - logs every export to the Studio's export history
   - header links back to the Studio, credits block in the rights dialog, Bangla option in the lyric-language list
   - removes the loading screen once the editor has started
   ============================================================ */
(() => {
'use strict';
if (!J.ui || !window.LVStore) return;           // engine test pages load the sources without the editor
const S = J.ui, A = J.uiApi;
const L = (document.documentElement.lang || 'en').slice(0, 2) === 'bn' ? 'bn' : 'en';
const T = {
  en: { studio: 'Studio', studioTip: 'Back to the LYRAVOX Studio (your projects are saved automatically)', saved: 'Saved to Studio', saving: 'Saving…', failed: 'Not saved (browser storage unavailable)',
        creditH: 'LYRAVOX', credit: 'Developed by Prince AR Abdur Rahman and published by NexVora Lab’s Ofc (Bangladesh). Based on the open-source JIZURA by hakoniwa (MIT License).',
        about: 'About', credits: 'Credits & licenses', privacy: 'Privacy', terms: 'Terms', contact: 'Contact' },
  bn: { studio: 'স্টুডিও', studioTip: 'LYRAVOX স্টুডিওতে ফিরুন (আপনার প্রজেক্ট নিজে থেকেই সেভ হয়)', saved: 'স্টুডিওতে সেভ হয়েছে', saving: 'সেভ হচ্ছে…', failed: 'সেভ হয়নি (ব্রাউজার স্টোরেজ পাওয়া যাচ্ছে না)',
        creditH: 'LYRAVOX', credit: 'ডেভেলপার প্রিন্স এআর আব্দুর রহমান, প্রকাশক NexVora Lab’s Ofc (বাংলাদেশ)। ওপেন সোর্স JIZURA (hakoniwa, MIT লাইসেন্স)-এর উপর ভিত্তি করে তৈরি।',
        about: 'পরিচিতি', credits: 'ক্রেডিট ও লাইসেন্স', privacy: 'গোপনীয়তা', terms: 'শর্তাবলি', contact: 'যোগাযোগ' },
}[L];
const $ = id => document.getElementById(id);
const root = location.pathname.replace(/editor\/(?:[a-z-]+\/)?$/, '');          // "/" on Vercel, a sub-path elsewhere

/* ---- header: Studio link, brand link, saved badge ---- */
const brand = document.querySelector('.bar .brand');
if (brand) {
  const a = document.createElement('a');
  a.className = brand.className; a.href = root + 'studio/'; a.title = T.studioTip;
  a.innerHTML = brand.innerHTML; brand.replaceWith(a);
}
const acts = document.querySelector('.bar .acts');
if (acts) {
  const st = document.createElement('a');
  st.className = 'lv-studio-link'; st.href = root + 'studio/'; st.textContent = T.studio; st.title = T.studioTip;
  acts.prepend(st);
}
const badge = document.createElement('span');
badge.className = 'lv-saved mono'; badge.setAttribute('role', 'status'); badge.setAttribute('aria-live', 'polite');
const projBox = document.querySelector('.bar .proj');
if (projBox) projBox.appendChild(badge);

/* ---- Bangla in the lyric-language list ---- */
const ll = $('lyricLang');
if (ll && !ll.querySelector('option[value="bn"]')) {
  const o = document.createElement('option'); o.value = 'bn'; o.textContent = 'বাংলা';
  const en = ll.querySelector('option[value="en"]'); if (en && en.nextSibling) ll.insertBefore(o, en.nextSibling); else ll.appendChild(o);
}

/* ---- credits in the rights dialog ---- */
const termsNote = document.querySelector('#termsDlg .terms-note');
if (termsNote) {
  const d = document.createElement('div'); d.className = 'lv-credit';
  d.innerHTML = `<h3>${T.creditH}</h3><p>${T.credit}</p><p class="lv-credit-links"><a href="${root}about/">${T.about}</a> · <a href="${root}credits/">${T.credits}</a> · <a href="${root}privacy/">${T.privacy}</a> · <a href="${root}terms/">${T.terms}</a> · <a href="${root}contact/">${T.contact}</a></p>`;
  termsNote.after(d);
}

/* ---- library autosave ---- */
const LV = window.LVStore;
let curId = null; try { curId = localStorage.getItem(LV.CUR_KEY); } catch (e) {}
let lastJson = '', lastThumb = 0, audioSynced = '', busy = false, dirty = false;
const setBadge = (m) => { badge.textContent = m; };

function thumb() {
  try {
    const v = $('view'); if (!v || !v.width) return '';
    const c = document.createElement('canvas'); const w = 320, h = Math.round(320 * v.height / v.width);
    c.width = w; c.height = h; c.getContext('2d').drawImage(v, 0, 0, w, h);
    return c.toDataURL('image/jpeg', 0.72);
  } catch (e) { return ''; }
}
const hashId = (s) => { let h = 5381; for (let i = 0; i < s.length; i++) h = ((h << 5) + h + s.charCodeAt(i)) >>> 0; return 'a_' + h.toString(36); };

async function syncAudio(rec) {
  const name = S.project.audioName || '';
  if (!name) { rec.audioId = ''; audioSynced = ''; return; }
  if (audioSynced === name && rec.audioId) return;
  const f = J.loadSong ? await J.loadSong() : null;                        // the editor's own copy of the current song
  if (!f || f.name !== name) return;                                       // not stored yet — try again on the next tick
  const id = hashId(f.name + '|' + f.size);
  const have = await LV.audio.get(id);
  if (!have) await LV.audio.put({ id, name: f.name, type: f.type || '', size: f.size, duration: S.audio ? S.audio.duration : 0, bpm: S.audio ? S.audio.bpm : 0, added: Date.now(), data: f });
  rec.audioId = id; audioSynced = name;
}
async function save(force) {
  if (busy || !S.project) return;
  const json = JSON.stringify(S.project);
  if (!force && json === lastJson && !dirty) return;
  busy = true; setBadge(T.saving);
  try {
    if (!curId) { curId = LV.uid(); localStorage.setItem(LV.CUR_KEY, curId); }
    const project = JSON.parse(json);
    let rec = await LV.projects.get(curId);
    if (!rec) rec = LV.makeRecord(project, { id: curId });
    rec.project = project; rec.updated = Date.now();
    const first = String(project.lyrics || '').split('\n').map(x => x.replace(/\[[^\]]*\]/g, '').trim()).find(x => x && !/^(#|\/\/)/.test(x)) || '';
    rec.title = project.title || first.slice(0, 40); rec.artist = project.artist || '';
    rec.lines = LV.countLines(project.lyrics); rec.lang = J.resolveLang ? J.resolveLang(project) : (project.lang || 'auto');
    rec.duration = S.plan ? S.plan.duration : 0; rec.aspect = project.aspect || '16:9';
    if (!rec.thumb || Date.now() - lastThumb > 20000) { const t = thumb(); if (t) { rec.thumb = t; lastThumb = Date.now(); } }
    await syncAudio(rec);
    await LV.projects.put(rec);
    lastJson = json; dirty = false; setBadge(T.saved);
  } catch (e) { setBadge(T.failed); console.warn('LYRAVOX library save failed', e); }
  busy = false;
}
setInterval(() => save(false), 2500);
document.addEventListener('visibilitychange', () => { if (document.visibilityState === 'hidden') { A.flushSave(); save(true); } });
window.addEventListener('pagehide', () => { save(true); });

/* ---- export history ---- */
J.logExport = (e) => {
  const p = S.project || {}, pl = S.plan || {};
  return LV.logExport(Object.assign({ projectId: curId || '', title: p.title || '', aspect: p.aspect || '', res: p.res || 1080, fps: p.fps || 24, quality: p.quality || '', lang: pl.lang || '' }, e)).catch(() => null);
};
const baseSave = J.saveFile;
J.saveFile = async (name, data) => {
  const r = await baseSave(name, data);
  try {
    if (/\.lrc$/i.test(name)) J.logExport({ format: 'lrc', name, size: data && data.size != null ? data.size : 0 });
    else if (/_ae\.json$/i.test(name)) J.logExport({ format: 'ae-json', name, size: data && data.size != null ? data.size : String(data).length });
  } catch (e) {}
  return r;
};

/* ---- AI Generate Lyrics ---- */
if (window.LVAI) {
  const audioRow = $('audioFile') && $('audioFile').closest('.row');
  const ai = document.createElement('button');
  ai.type = 'button'; ai.id = 'btnAIGen'; ai.className = 'ghost lv-ai-btn'; ai.textContent = '✨ ' + LVAI.t('btn');
  if (audioRow) audioRow.appendChild(ai);
  const host = {
    title: '', closeOnSend: false,
    toast: (m) => A.toast(m),
    hasLyrics: () => { const v = String(S.project.lyrics || '').trim(); return !!v && v !== String(J.SAMPLE_LYRICS || '').trim(); },
    apply: async ({ mode, text }) => {
      if (S.tap || S.exporting) { A.toast(LVAI.t('needAudio')); return false; }
      if (mode === 'replace') { A.loadLrc(text); return true; }
      return A.appendLyrics(text);
    },
  };
  ai.addEventListener('click', async () => {
    const f = J.loadSong ? await J.loadSong() : null;                 // the editor's own copy of the song that is loaded now
    if (!f) { A.toast(LVAI.t('needAudio')); return; }
    host.title = S.project.title || f.name.replace(/\.[^.]+$/, '');
    LVAI.open({ file: f, host });
  });
}

/* ---- loading screen ---- */
const splash = $('lvSplash');
const hide = () => { if (!splash) return; splash.classList.add('done'); setTimeout(() => splash.remove(), 600); };
requestAnimationFrame(() => setTimeout(hide, 350));
if (document.fonts && document.fonts.ready) document.fonts.ready.then(() => setTimeout(hide, 200)).catch(hide);
setTimeout(hide, 5000);
setTimeout(() => save(true), 1500);
})();
