/* LYRAVOX — AI Generate Lyrics (client).
   Talks to the separate LYRAVOX AI backend (REST: POST /api/transcribe, GET/DELETE /api/transcribe/{id}, GET /api/health).
   Used by the Studio (audio library) and by the editor. Nothing here fakes recognition: every line comes from the server's response.
   Public API:  LVAI.open({ file, host })  host = { title, hasLyrics(), apply({mode:'replace'|'append', text, lines}), extra? }  */
(function (root) {
'use strict';
const L = {};
const DICT = {
 en: {
  btn: 'AI Generate Lyrics', title: 'AI Generate Lyrics', file: 'Audio file', size: 'Size', duration: 'Duration', language: 'Language', auto: 'Auto-detect',
  langs: { bn: 'বাংলা (Bangla)', en: 'English', hi: 'हिन्दी (Hindi)' }, vocal: 'Separate vocals first (Demucs)', vocalHelp: 'Better on loud music, but much slower. Falls back to the original audio if it fails.',
  vocalNA: 'Not available on this server', advanced: 'Section & server', section: 'Only this section (seconds)', from: 'from', to: 'to', server: 'AI server address',
  save: 'Save', generate: 'Generate Lyrics', cancel: 'Cancel', close: 'Close', retry: 'Try again', checking: 'Checking the AI server…', ready: 'AI server ready',
  down: 'Cannot reach the AI server', downHelp: 'The AI feature needs the LYRAVOX AI backend. Start it (see backend/README.md) or enter its address below.', noServer: 'No AI server is configured.',
  uploading: 'Uploading', queued: 'Waiting in the queue…', preparing: 'Preparing audio…', separating: 'Separating vocals…', analyzing: 'Analysing the audio…', detecting_language: 'Detecting the language…',
  transcribing: 'Transcribing…', aligning: 'Building lyric lines…', completed: 'Done', failed: 'Failed', cancelled: 'Cancelled', cancelling: 'Cancelling…', elapsed: 'Elapsed',
  detected: 'Detected language', warnings: 'Notes', tooBig: 'This file is larger than the server limit', tooLong: 'This audio is longer than the server limit', useSection: 'Use the section option to process part of it.',
  badFile: 'Choose an audio file (mp3, wav, m4a, aac or ogg).', lines: 'lines', start: 'Start', end: 'End', text: 'Lyric text', conf: 'Confidence', play: 'Play this line', split: 'Split at the cursor', merge: 'Merge with the next line',
  del: 'Delete line', add: 'Add a line below', toEditor: 'Send this line to the editor', sel: 'Select', regen: 'Regenerate selected lines', regenHelp: 'Select one or more lines first', playAll: 'Play', pause: 'Pause',
  reset: 'Reset to detected', sendAll: 'Send all to the editor', sendSel: 'Send selected', timestamps: 'Keep timestamps', interludes: 'Add instrumental breaks', copy: 'Copy', lrc: 'Download .lrc', studio: 'Open in Lyrics Studio',
  copied: 'Copied', sent: 'Lyrics sent to the editor', lineSent: 'Line added to the editor', noLines: 'No lyric lines yet', confirmReplace: 'Replace the lyrics in the editor with these lines? (You can undo this in the editor.)',
  lowConf: 'Low confidence, please check', approx: 'Timing estimated', model: 'Model', nothing: 'No words were detected. The audio may be instrumental, or the vocals too quiet. You can still add lines by hand.',
  regenDone: 'Section regenerated', mockEngine: 'TEST ENGINE: these lines are placeholders, not real lyrics', applyHint: 'Edit text and times, then send the lyrics to the editor.', netErr: 'Network error while talking to the AI server',
  needAudio: 'Load a song first.', noMem: 'The server answered, but not in the expected format.', ago: 's', pct: '%'
 },
 bn: {
  btn: 'AI দিয়ে লিরিক্স বানান', title: 'AI দিয়ে লিরিক্স বানান', file: 'অডিও ফাইল', size: 'আকার', duration: 'দৈর্ঘ্য', language: 'ভাষা', auto: 'স্বয়ংক্রিয় শনাক্ত',
  langs: { bn: 'বাংলা', en: 'English (ইংরেজি)', hi: 'हिन्दी (হিন্দি)' }, vocal: 'আগে কণ্ঠ আলাদা করুন (Demucs)', vocalHelp: 'জোরালো মিউজিকে ভালো ফল দেয়, কিন্তু অনেক ধীর। ব্যর্থ হলে মূল অডিও ব্যবহার হবে।',
  vocalNA: 'এই সার্ভারে পাওয়া যাচ্ছে না', advanced: 'অংশ ও সার্ভার', section: 'শুধু এই অংশ (সেকেন্ডে)', from: 'শুরু', to: 'শেষ', server: 'AI সার্ভারের ঠিকানা',
  save: 'সেভ', generate: 'লিরিক্স তৈরি করুন', cancel: 'বাতিল', close: 'বন্ধ', retry: 'আবার চেষ্টা', checking: 'AI সার্ভার যাচাই হচ্ছে…', ready: 'AI সার্ভার প্রস্তুত',
  down: 'AI সার্ভারে পৌঁছানো যাচ্ছে না', downHelp: 'এই ফিচারের জন্য LYRAVOX AI ব্যাকএন্ড লাগে। সেটি চালু করুন (backend/README.md দেখুন) অথবা নিচে তার ঠিকানা দিন।', noServer: 'কোনো AI সার্ভার সেট করা নেই।',
  uploading: 'আপলোড হচ্ছে', queued: 'সারিতে অপেক্ষা করছে…', preparing: 'অডিও প্রস্তুত হচ্ছে…', separating: 'কণ্ঠ আলাদা হচ্ছে…', analyzing: 'অডিও বিশ্লেষণ চলছে…', detecting_language: 'ভাষা শনাক্ত হচ্ছে…',
  transcribing: 'লেখা বের করা হচ্ছে…', aligning: 'লিরিক্সের লাইন সাজানো হচ্ছে…', completed: 'সম্পন্ন', failed: 'ব্যর্থ', cancelled: 'বাতিল হয়েছে', cancelling: 'বাতিল হচ্ছে…', elapsed: 'সময় গেছে',
  detected: 'শনাক্ত ভাষা', warnings: 'নোট', tooBig: 'ফাইলটি সার্ভারের সীমার চেয়ে বড়', tooLong: 'অডিওটি সার্ভারের সীমার চেয়ে লম্বা', useSection: 'কিছু অংশ প্রসেস করতে “অংশ” অপশন ব্যবহার করুন।',
  badFile: 'একটি অডিও ফাইল বাছুন (mp3, wav, m4a, aac বা ogg)।', lines: 'লাইন', start: 'শুরু', end: 'শেষ', text: 'লিরিক্স', conf: 'নির্ভরযোগ্যতা', play: 'এই লাইন চালান', split: 'কার্সরের জায়গায় ভাগ করুন', merge: 'পরের লাইনের সাথে জুড়ুন',
  del: 'লাইন মুছুন', add: 'নিচে লাইন যোগ করুন', toEditor: 'এই লাইন এডিটরে পাঠান', sel: 'বাছুন', regen: 'বাছা লাইনগুলো আবার তৈরি করুন', regenHelp: 'আগে এক বা একাধিক লাইন বাছুন', playAll: 'চালান', pause: 'থামান',
  reset: 'শনাক্ত করা অবস্থায় ফিরুন', sendAll: 'সব এডিটরে পাঠান', sendSel: 'বাছাগুলো পাঠান', timestamps: 'টাইমস্ট্যাম্প রাখুন', interludes: 'বাদ্যাংশ যোগ করুন', copy: 'কপি', lrc: '.lrc ডাউনলোড', studio: 'লিরিক্স স্টুডিওতে খুলুন',
  copied: 'কপি হয়েছে', sent: 'লিরিক্স এডিটরে পাঠানো হয়েছে', lineSent: 'লাইনটি এডিটরে যোগ হয়েছে', noLines: 'এখনও কোনো লাইন নেই', confirmReplace: 'এডিটরের লিরিক্স এই লাইনগুলো দিয়ে বদলাবেন? (এডিটরে আনডু করতে পারবেন।)',
  lowConf: 'নির্ভরযোগ্যতা কম, যাচাই করুন', approx: 'সময় আনুমানিক', model: 'মডেল', nothing: 'কোনো শব্দ শনাক্ত হয়নি। অডিওটি বাদ্য-নির্ভর হতে পারে, বা কণ্ঠ খুব নিচু। চাইলে হাতে লাইন যোগ করতে পারেন।',
  regenDone: 'অংশটি আবার তৈরি হয়েছে', mockEngine: 'টেস্ট ইঞ্জিন: এগুলো আসল লিরিক্স নয়, শুধু নমুনা', applyHint: 'লেখা ও সময় ঠিক করে লিরিক্স এডিটরে পাঠান।', netErr: 'AI সার্ভারের সাথে যোগাযোগে নেটওয়ার্ক সমস্যা',
  needAudio: 'আগে একটি গান লোড করুন।', noMem: 'সার্ভার সাড়া দিয়েছে, কিন্তু প্রত্যাশিত ফরম্যাটে নয়।', ago: 'সে.', pct: '%'
 }
};
const lang = () => ((document.documentElement.getAttribute('data-lang') || document.documentElement.lang || 'en').slice(0, 2) === 'bn' ? 'bn' : 'en');
const t = (k) => (DICT[lang()][k] != null ? DICT[lang()][k] : DICT.en[k] != null ? DICT.en[k] : k);
L.t = t; L.DICT = DICT;

/* ---------------- pure helpers (unit-tested in the browser) ---------------- */
const fmt = (s) => { s = Math.max(0, +s || 0); const m = Math.floor(s / 60); return m + ':' + (s - m * 60).toFixed(2).padStart(5, '0'); };
const parseT = (v) => { v = String(v).trim().replace(',', '.'); const m = v.match(/^(?:(\d+):)?(\d+(?:\.\d+)?)$/); return m ? (m[1] ? +m[1] * 60 : 0) + parseFloat(m[2]) : NaN; };
const ts = (s) => { s = Math.max(0, s); const m = Math.floor(s / 60); return '[' + String(m).padStart(2, '0') + ':' + (s - m * 60).toFixed(2).padStart(5, '0') + ']'; };
L.fmt = fmt; L.parseTime = parseT; L.tag = ts;
/* characters that mean something in the LYRAVOX lyric syntax: / cut, | note, * emphasis, trailing ! flash, leading # comment, leading [ tag */
L.sanitize = (s) => String(s).replace(/\//g, ' ').replace(/\|/g, ' ').replace(/\*/g, '').replace(/^[#\[\s]+/, '').replace(/!+$/, '').trim().replace(/\s{2,}/g, ' ');
L.instrumentals = (lines, duration, min) => {
  min = min || 6; const out = []; let pos = 0;
  [...lines].sort((a, b) => a.start - b.start).forEach(l => { if (l.start - pos >= min) out.push({ start: pos, end: l.start }); pos = Math.max(pos, l.end); });
  if (duration && duration - pos >= min) out.push({ start: pos, end: duration });
  return out;
};
L.toEditorText = (lines, o) => {
  o = o || {}; const rows = [];
  lines.forEach(l => { const x = L.sanitize(l.text); if (x) rows.push([l.start, (o.timestamps === false ? '' : ts(l.start)) + x]); });
  if (o.interludes !== false && o.timestamps !== false) L.instrumentals(lines, o.duration, o.minGap).forEach(g => rows.push([g.start, ts(g.start) + '[interlude ' + Math.max(1, Math.round(g.end - g.start)) + ']']));
  rows.sort((a, b) => a[0] - b[0]);
  return rows.map(r => r[1]).join('\n');
};
L.toLrc = (lines, title) => (title ? '[ti:' + title.replace(/[\r\n\]]/g, ' ') + ']\n' : '') + lines.map(l => ts(l.start) + String(l.text).replace(/[\r\n]+/g, ' ')).join('\n');
L.splitLine = (line, caret) => {
  const txt = line.text; caret = Math.max(0, Math.min(txt.length, caret));
  const a = txt.slice(0, caret).trim(), b = txt.slice(caret).trim();
  if (!a || !b) return null;
  let tm = null;
  if (line.words && line.words.length > 1) {                       // cut at the word boundary closest to the caret
    let acc = 0, best = null, bd = 1e9;
    for (let i = 0; i < line.words.length - 1; i++) { acc += line.words[i].text.length + 1; const d = Math.abs(acc - caret); if (d < bd) { bd = d; best = line.words[i + 1].start; } }
    tm = best;
  }
  if (tm == null || tm <= line.start || tm >= line.end) tm = line.start + (line.end - line.start) * (caret / Math.max(1, txt.length));
  tm = Math.round(tm * 100) / 100;
  return [Object.assign({}, line, { text: a, end: tm, words: (line.words || []).filter(w => w.start < tm) }), Object.assign({}, line, { text: b, start: tm, words: (line.words || []).filter(w => w.start >= tm) })];
};
L.mergeLines = (a, b) => Object.assign({}, a, { text: (a.text + ' ' + b.text).trim(), end: Math.max(a.end, b.end), confidence: (a.confidence == null || b.confidence == null) ? (a.confidence ?? b.confidence) : Math.min(a.confidence, b.confidence), words: (a.words || []).concat(b.words || []) });

/* ---------------- server settings ---------------- */
L.apiBase = () => {
  let v = ''; try { v = localStorage.getItem('lyravox.api') || ''; } catch (e) {}
  if (!v && window.LYRAVOX_CONFIG && window.LYRAVOX_CONFIG.apiUrl) v = window.LYRAVOX_CONFIG.apiUrl;
  if (!v) { const m = document.querySelector('meta[name="lyravox-api"]'); v = (m && m.content) || ''; }
  if (!v && /^(localhost|127\.0\.0\.1|\[::1\])$/.test(location.hostname)) v = 'http://localhost:8000';
  return v.replace(/\/+$/, '');
};
L.setApiBase = (v) => { try { v ? localStorage.setItem('lyravox.api', v.trim()) : localStorage.removeItem('lyravox.api'); } catch (e) {} };
const withTimeout = (ms) => { const c = new AbortController(); const id = setTimeout(() => c.abort(), ms); return { signal: c.signal, done: () => clearTimeout(id) }; };
L.health = async (base) => {
  if (!base) throw Object.assign(new Error('no server'), { code: 'no_server' });
  const to = withTimeout(8000);
  try { const r = await fetch(base + '/api/health', { signal: to.signal }); if (!r.ok) throw new Error('HTTP ' + r.status); return await r.json(); }
  finally { to.done(); }
};

/* ---------------- DOM helper ---------------- */
const h = (tag, attrs, ...kids) => {
  const e = document.createElement(tag);
  Object.entries(attrs || {}).forEach(([k, v]) => { if (v == null || v === false) return; if (k === 'class') e.className = v; else if (k.startsWith('on')) e.addEventListener(k.slice(2), v); else if (k === 'text') e.textContent = v; else e.setAttribute(k, v === true ? '' : v); });
  kids.flat().forEach(c => { if (c == null || c === false) return; e.appendChild(typeof c === 'string' ? document.createTextNode(c) : c); });
  return e;
};
const bytes = (n) => n < 1048576 ? (n / 1024).toFixed(0) + ' KB' : (n / 1048576).toFixed(1) + ' MB';
const audioDuration = (file) => new Promise((res) => { const a = new Audio(), u = URL.createObjectURL(file); a.preload = 'metadata'; a.onloadedmetadata = () => { URL.revokeObjectURL(u); res(isFinite(a.duration) ? a.duration : 0); }; a.onerror = () => { URL.revokeObjectURL(u); res(0); }; a.src = u; });
const LANGNAME = (c) => (DICT[lang()].langs[c] || c);

/* ---------------- the modal ---------------- */
L.open = function (opts) {
  const file = opts.file, host = opts.host || {};
  if (!file) { host.toast && host.toast(t('needAudio')); return null; }
  const st = { base: L.apiBase(), health: null, job: null, xhr: null, poll: null, running: false, cancelled: false, lines: [], orig: [], instr: [], result: null, duration: 0,
               sel: new Set(), active: -1, playUntil: null, objUrl: URL.createObjectURL(file) };
  const prevFocus = document.activeElement;
  const root = h('div', { class: 'lvai-overlay', role: 'dialog', 'aria-modal': 'true', 'aria-label': t('title') });
  const box = h('div', { class: 'lvai-box' });
  root.appendChild(box); document.body.appendChild(root); document.body.classList.add('lvai-lock');
  const audioEl = h('audio', { src: st.objUrl, preload: 'metadata' });

  const close = () => {
    if (st.running) return;
    audioEl.pause(); URL.revokeObjectURL(st.objUrl); root.remove(); document.body.classList.remove('lvai-lock'); document.removeEventListener('keydown', onKey, true);
    if (prevFocus && prevFocus.focus) try { prevFocus.focus(); } catch (e) {}
  };
  const onKey = (e) => { if (e.key === 'Escape') { e.stopPropagation(); if (!st.running) close(); } };
  document.addEventListener('keydown', onKey, true);

  /* ---------- setup view ---------- */
  const el = {};
  function viewSetup() {
    box.innerHTML = '';
    el.status = h('div', { class: 'lvai-pill', role: 'status' }, t('checking'));
    el.lang = h('select', { id: 'lvaiLang', 'aria-label': t('language') }, h('option', { value: 'auto' }, t('auto')));
    el.vocal = h('input', { type: 'checkbox', id: 'lvaiVocal' });
    el.from = h('input', { type: 'number', min: '0', step: '0.1', id: 'lvaiFrom', placeholder: '0', 'aria-label': t('from') });
    el.to = h('input', { type: 'number', min: '0', step: '0.1', id: 'lvaiTo', placeholder: '', 'aria-label': t('to') });
    el.api = h('input', { type: 'url', id: 'lvaiApi', placeholder: 'https://your-backend.onrender.com', value: st.base });
    el.err = h('div', { class: 'lvai-err', role: 'alert', hidden: true });
    el.go = h('button', { class: 'lvai-btn pri', id: 'lvaiGo', type: 'button', disabled: true, onclick: start }, '✨ ' + t('generate'));
    el.info = h('dl', { class: 'lvai-info' }, h('dt', {}, t('file')), h('dd', { title: file.name }, file.name), h('dt', {}, t('size')), h('dd', {}, bytes(file.size)), h('dt', {}, t('duration')), h('dd', { id: 'lvaiDur' }, st.duration ? fmt(st.duration) : '…'));
    box.append(
      h('header', {}, h('h2', {}, '✨ ' + t('title')), h('button', { class: 'lvai-x', type: 'button', 'aria-label': t('close'), onclick: close }, '×')),
      h('div', { class: 'lvai-body' }, el.info, el.status, el.err,
        h('label', { class: 'lvai-f' }, h('span', {}, t('language')), el.lang),
        h('label', { class: 'lvai-chk', title: t('vocalHelp') }, el.vocal, h('span', {}, t('vocal')), h('small', { id: 'lvaiVocalHelp' }, t('vocalHelp'))),
        h('details', { class: 'lvai-adv' }, h('summary', {}, t('advanced')),
          h('div', { class: 'lvai-row' }, h('span', {}, t('section')), h('label', {}, t('from'), el.from), h('label', {}, t('to'), el.to)),
          h('div', { class: 'lvai-row' }, h('label', { class: 'grow' }, t('server'), el.api), h('button', { class: 'lvai-btn', type: 'button', onclick: () => { L.setApiBase(el.api.value); st.base = L.apiBase(); checkServer(); } }, t('save'))))),
      h('footer', {}, h('button', { class: 'lvai-btn', type: 'button', onclick: close }, t('close')), el.go));
    (host.initialLanguage ? [host.initialLanguage] : []).forEach(v => { el.lang.value = v; });
    audioDuration(file).then(d => { st.duration = d; const x = document.getElementById('lvaiDur'); if (x) x.textContent = d ? fmt(d) : '—'; });
    checkServer();
  }
  async function checkServer() {
    el.status.className = 'lvai-pill'; el.status.textContent = t('checking'); el.go.disabled = true; el.err.hidden = true;
    st.base = L.apiBase();
    try {
      const j = await L.health(st.base); st.health = j;
      if (!j || !j.limits) throw new Error('bad health');
      el.status.className = 'lvai-pill ok';
      el.status.textContent = '● ' + t('ready') + ' · ' + t('model') + ': ' + (j.model || j.engine) + ' · ≤ ' + j.limits.max_upload_mb + ' MB · ≤ ' + Math.round(j.limits.max_duration_s / 60) + ' min';
      if (j.engine === 'fake-test-engine') el.status.textContent += ' · ' + t('mockEngine');
      el.lang.innerHTML = ''; el.lang.appendChild(h('option', { value: 'auto' }, t('auto')));
      (j.languages || []).forEach(c => el.lang.appendChild(h('option', { value: c }, LANGNAME(c))));
      el.vocal.disabled = !j.vocal_separation_available;
      const vh = document.getElementById('lvaiVocalHelp'); if (vh && !j.vocal_separation_available) vh.textContent = t('vocalNA');
      if (!j.engine_available) { fail(t('down') + ': AI engine (faster-whisper) is not installed on the server.'); return; }
      el.go.disabled = false;
    } catch (e) {
      el.status.className = 'lvai-pill bad';
      el.status.textContent = '● ' + (st.base ? t('down') + ' (' + st.base + ')' : t('noServer'));
      fail(t('downHelp'), true);
    }
  }
  function fail(msg, retry) {
    el.err.hidden = false; el.err.textContent = '';
    el.err.appendChild(h('span', {}, msg));
    if (retry) el.err.appendChild(h('button', { class: 'lvai-btn', type: 'button', onclick: checkServer }, t('retry')));
  }

  /* ---------- running view ---------- */
  function viewRunning(label) {
    box.innerHTML = '';
    el.bar = h('div', { class: 'lvai-bar' }, h('i', {})); el.stage = h('div', { class: 'lvai-stage', role: 'status', 'aria-live': 'polite' }, label || t('uploading'));
    el.det = h('div', { class: 'lvai-det' }); el.elapsed = h('small', {}, ''); el.cancel = h('button', { class: 'lvai-btn danger', id: 'lvaiCancel', type: 'button', onclick: cancel }, t('cancel'));
    el.err = h('div', { class: 'lvai-err', role: 'alert', hidden: true });
    box.append(h('header', {}, h('h2', {}, '✨ ' + t('title'))), h('div', { class: 'lvai-body' }, el.stage, el.bar, el.det, el.elapsed, el.err), h('footer', {}, el.cancel));
  }
  const setBar = (p) => { if (el.bar) el.bar.firstChild.style.width = Math.round(Math.max(0, Math.min(1, p)) * 100) + '%'; };
  let t0 = 0, tick = null;
  const startTimer = () => { t0 = Date.now(); clearInterval(tick); tick = setInterval(() => { if (el.elapsed) el.elapsed.textContent = t('elapsed') + ': ' + Math.round((Date.now() - t0) / 1000) + ' ' + t('ago'); }, 500); };

  /* the real job: upload with progress, then poll */
  function runJob(params, onProgress) {
    return new Promise((resolve, reject) => {
      const fd = new FormData();
      fd.append('file', file, file.name);
      Object.entries(params).forEach(([k, v]) => { if (v != null && v !== '') fd.append(k, String(v)); });
      const xhr = new XMLHttpRequest(); st.xhr = xhr;
      xhr.open('POST', st.base + '/api/transcribe');
      xhr.upload.onprogress = (e) => { if (e.lengthComputable) onProgress({ phase: 'upload', p: e.loaded / e.total }); };
      xhr.onerror = () => reject(Object.assign(new Error(t('netErr')), { net: true }));
      xhr.onabort = () => reject(Object.assign(new Error('aborted'), { aborted: true }));
      xhr.onload = () => {
        st.xhr = null;
        let j = null; try { j = JSON.parse(xhr.responseText); } catch (e) {}
        if (xhr.status !== 202 || !j || !j.job_id) return reject(Object.assign(new Error((j && j.error && j.error.message) || ('HTTP ' + xhr.status)), { api: j && j.error, status: xhr.status }));
        st.job = j.job_id;
        if (st.cancelled) { fetch(st.base + '/api/transcribe/' + st.job, { method: 'DELETE' }).catch(() => {}); return reject(Object.assign(new Error('aborted'), { aborted: true })); }
        pollLoop(onProgress).then(resolve, reject);
      };
      xhr.send(fd);
    });
  }
  async function pollLoop(onProgress) {
    let fails = 0, delay = 700;
    for (;;) {
      if (st.cancelled) throw Object.assign(new Error('aborted'), { aborted: true });
      await new Promise(r => setTimeout(r, delay)); delay = Math.min(1500, delay + 100);
      let j;
      try {
        const to = withTimeout(15000);
        const r = await fetch(st.base + '/api/transcribe/' + st.job, { signal: to.signal }); to.done();
        j = await r.json();
        if (!r.ok) throw Object.assign(new Error((j.error && j.error.message) || 'HTTP ' + r.status), { api: j.error, status: r.status });
        fails = 0;
      } catch (e) {
        if (e.api) throw e;
        if (++fails >= 5) throw Object.assign(new Error(t('netErr')), { net: true });
        continue;
      }
      onProgress({ phase: 'server', job: j });
      if (j.status === 'completed') return j;
      if (j.status === 'failed') throw Object.assign(new Error(j.error ? j.error.message : 'failed'), { api: j.error });
      if (j.status === 'cancelled') throw Object.assign(new Error('aborted'), { aborted: true });
    }
  }
  const progressUI = (ev) => {
    if (ev.phase === 'upload') { el.stage.textContent = t('uploading') + ' ' + Math.round(ev.p * 100) + t('pct'); setBar(ev.p * 0.15); return; }
    const j = ev.job; el.stage.textContent = t(j.stage) || j.stage; setBar(0.15 + 0.85 * (j.progress || 0));
    if (j.language) { el.det.textContent = t('detected') + ': ' + LANGNAME(j.language) + (j.language_probability != null ? ' (' + Math.round(j.language_probability * 100) + t('pct') + ')' : ''); }
  };
  const params = () => ({ language: el.lang.value, vocal_separation: el.vocal.checked ? 'true' : 'false', word_timestamps: 'true', clip_start: el.from.value, clip_end: el.to.value });

  async function start() {
    el.err.hidden = true;
    const lim = st.health && st.health.limits;
    if (lim && file.size > lim.max_upload_mb * 1048576) return fail(t('tooBig') + ' (' + lim.max_upload_mb + ' MB).');
    const cs = parseFloat(el.from.value), ce = parseFloat(el.to.value);
    const span = (isFinite(ce) ? ce : st.duration) - (isFinite(cs) ? cs : 0);
    if (lim && st.duration && span > lim.max_duration_s) return fail(t('tooLong') + ' (' + Math.round(lim.max_duration_s / 60) + ' min). ' + t('useSection'));
    const p = params(); st.cancelled = false; st.running = true; st.reqParams = p;
    viewRunning(t('uploading')); startTimer();
    try {
      const j = await runJob(p, progressUI);
      st.running = false; clearInterval(tick); st.result = j;
      st.lines = (j.segments || []).map(normLine); st.orig = JSON.parse(JSON.stringify(st.lines)); st.instr = j.instrumentals || [];
      st.duration = st.duration || j.duration; viewResult();
    } catch (e) {
      st.running = false; clearInterval(tick);
      if (e.aborted) { viewSetup(); return; }
      viewSetup(); await new Promise(r => setTimeout(r, 0));
      const net = e.net;
      if (net) { el.status.className = 'lvai-pill bad'; el.status.textContent = '● ' + t('down') + ' (' + st.base + ')'; }
      fail((e.api && e.api.message) || e.message || t('failed'), !!net);
    }
  }
  async function cancel() {
    st.cancelled = true; el.cancel.disabled = true; el.stage.textContent = t('cancelling');
    if (st.xhr) st.xhr.abort();
    if (st.job) { try { await fetch(st.base + '/api/transcribe/' + st.job, { method: 'DELETE' }); } catch (e) {} }
    // the poll loop notices st.cancelled and leaves the running view
  }

  /* ---------- result view / lyrics editor ---------- */
  const normLine = (s) => ({ start: s.start, end: s.end, text: s.text, confidence: s.confidence == null ? null : s.confidence, approx: !!s.approx_timing, words: s.words || [] });
  let tbody, playBtn;
  function viewResult() {
    box.innerHTML = ''; el.sendAll = h('button', { class: 'lvai-btn pri', id: 'lvaiSendAll', type: 'button', onclick: () => send('replace', st.lines) }, '↦ ' + t('sendAll'));
    const j = st.result;
    el.opt = { ts: h('input', { type: 'checkbox', checked: true, id: 'lvaiTs' }), inter: h('input', { type: 'checkbox', checked: true, id: 'lvaiInter' }) };
    playBtn = h('button', { class: 'lvai-btn', id: 'lvaiPlayAll', type: 'button', onclick: togglePlay }, '▶ ' + t('playAll'));
    el.regen = h('button', { class: 'lvai-btn', id: 'lvaiRegen', type: 'button', disabled: true, title: t('regenHelp'), onclick: regenerate }, '↻ ' + t('regen'));
    el.regenMsg = h('div', { class: 'lvai-stage small', hidden: true });
    tbody = h('tbody', {});
    const notes = [].concat(j.warnings || []);
    if (j.engine === 'fake-test-engine') notes.unshift(t('mockEngine'));
    box.append(
      h('header', {}, h('h2', {}, '✨ ' + t('title')), h('button', { class: 'lvai-x', type: 'button', 'aria-label': t('close'), onclick: close }, '×')),
      h('div', { class: 'lvai-body res' },
        h('div', { class: 'lvai-meta' }, h('span', { class: 'chip' }, t('detected') + ': ' + LANGNAME(j.language) + (j.language_probability != null ? ' ' + Math.round(j.language_probability * 100) + t('pct') : '')),
          h('span', { class: 'chip' }, t('model') + ': ' + j.model), j.vocal_separation && j.vocal_separation.used ? h('span', { class: 'chip' }, 'Demucs ✓') : null, h('span', { class: 'chip', id: 'lvaiCount' }, '')),
        notes.length ? h('ul', { class: 'lvai-notes', 'aria-label': t('warnings') }, notes.map(n => h('li', {}, n))) : null,
        h('p', { class: 'lvai-hint' }, t('applyHint')),
        h('div', { class: 'lvai-tools' }, playBtn, el.regen, h('button', { class: 'lvai-btn', type: 'button', onclick: () => { st.lines = JSON.parse(JSON.stringify(st.orig)); st.sel.clear(); renderRows(); } }, t('reset'))),
        el.regenMsg,
        h('div', { class: 'lvai-table', role: 'region', 'aria-label': t('lines') }, h('table', {}, h('thead', {}, h('tr', {}, h('th', {}, ''), h('th', {}, t('start')), h('th', {}, t('end')), h('th', {}, t('text')), h('th', {}, t('conf')), h('th', {}, ''))), tbody))),
      h('footer', { class: 'wrap' },
        h('label', { class: 'lvai-chk inline' }, el.opt.ts, h('span', {}, t('timestamps'))), h('label', { class: 'lvai-chk inline' }, el.opt.inter, h('span', {}, t('interludes'))),
        h('button', { class: 'lvai-btn', type: 'button', onclick: () => send('replace', st.lines.filter((_, i) => st.sel.has(i)), true) }, t('sendSel')),
        h('button', { class: 'lvai-btn', type: 'button', onclick: copy }, t('copy')), h('button', { class: 'lvai-btn', type: 'button', onclick: dl }, t('lrc')),
        host.studio ? h('button', { class: 'lvai-btn', id: 'lvaiStudio', type: 'button', onclick: () => { host.studio({ text: textOut(st.lines), title: host.title || '' }); close(); } }, t('studio')) : null,
        el.sendAll));
    box.appendChild(audioEl);
    audioEl.addEventListener('timeupdate', onTime); audioEl.addEventListener('play', () => { playBtn.textContent = '❚❚ ' + t('pause'); }); audioEl.addEventListener('pause', () => { playBtn.textContent = '▶ ' + t('playAll'); });
    renderRows();
  }
  const sorted = () => { st.lines.sort((a, b) => a.start - b.start); };
  function renderRows() {
    tbody.innerHTML = ''; st.active = -1;
    const c = document.getElementById('lvaiCount'); if (c) c.textContent = st.lines.length + ' ' + t('lines');
    if (!st.lines.length) {
      const td = h('td', { colspan: '6', class: 'empty' }, t('nothing'), h('div', {}, h('button', { class: 'lvai-btn', id: 'lvaiAddFirst', type: 'button', onclick: () => { st.lines.push({ start: 0, end: 2, text: '', confidence: null, approx: false, words: [] }); renderRows(); } }, '+ ' + t('add'))));
      tbody.appendChild(h('tr', {}, td));
    }
    st.lines.forEach((l, i) => {
      const confCls = l.confidence == null ? 'na' : l.confidence >= 0.7 ? 'hi' : l.confidence >= 0.4 ? 'mid' : 'lo';
      const inp = h('input', { type: 'text', class: 'tx', value: l.text, 'aria-label': t('text') + ' ' + (i + 1), lang: j2lang(), spellcheck: 'false' });
      inp.addEventListener('input', () => { l.text = inp.value; }); const caret = () => { l._caret = inp.selectionStart; }; ['keyup', 'click', 'select', 'focus', 'blur'].forEach(ev => inp.addEventListener(ev, caret));
      const tIn = (key) => { const x = h('input', { type: 'text', class: 'tm', value: fmt(l[key]), inputmode: 'decimal', 'aria-label': t(key === 'start' ? 'start' : 'end') + ' ' + (i + 1), 'data-key': key });
        x.addEventListener('change', () => { const v = parseT(x.value); if (isFinite(v)) { l[key] = Math.round(v * 100) / 100; if (key === 'start') sorted(); renderRows(); } else x.value = fmt(l[key]); });
        x.addEventListener('keydown', (e) => { if (e.key === 'ArrowUp' || e.key === 'ArrowDown') { e.preventDefault(); l[key] = Math.max(0, Math.round((l[key] + (e.key === 'ArrowUp' ? 0.1 : -0.1)) * 100) / 100); x.value = fmt(l[key]); } });
        return x; };
      const cb = h('input', { type: 'checkbox', 'aria-label': t('sel') + ' ' + (i + 1), checked: st.sel.has(i) });
      cb.addEventListener('change', () => { cb.checked ? st.sel.add(i) : st.sel.delete(i); el.regen.disabled = !st.sel.size; });
      const btn = (txt, title, fn, cls) => h('button', { class: 'lvai-ib ' + (cls || ''), type: 'button', title, 'aria-label': title, onclick: fn }, txt);
      const tr = h('tr', { 'data-i': i }, h('td', {}, cb), h('td', {}, tIn('start')), h('td', {}, tIn('end')), h('td', { class: 'txc' }, inp),
        h('td', {}, h('span', { class: 'cf ' + confCls, title: (l.confidence == null ? '—' : Math.round(l.confidence * 100) + '%') + (l.confidence != null && l.confidence < 0.4 ? ' · ' + t('lowConf') : '') + (l.approx ? ' · ' + t('approx') : '') }, l.confidence == null ? '—' : Math.round(l.confidence * 100) + '%' + (l.approx ? '≈' : ''))),
        h('td', { class: 'act' }, btn('▶', t('play'), () => playRow(i), 'play'), btn('✂', t('split'), () => doSplit(i)), btn('⤵', t('merge'), () => doMerge(i)), btn('+', t('add'), () => doAdd(i)), btn('→', t('toEditor'), () => send('append', [l], true), 'send'), btn('✕', t('del'), () => doDel(i), 'del')));
      tbody.appendChild(tr);
    });
    el.regen && (el.regen.disabled = !st.sel.size);
  }
  const j2lang = () => ({ bn: 'bn', en: 'en', hi: 'hi' }[st.result && st.result.language] || 'und');
  function doSplit(i) { const l = st.lines[i]; const r = L.splitLine(l, l._caret != null ? l._caret : Math.floor(l.text.length / 2)); if (!r) return; st.lines.splice(i, 1, r[0], r[1]); st.sel.clear(); renderRows(); }
  function doMerge(i) { if (i >= st.lines.length - 1) return; st.lines.splice(i, 2, L.mergeLines(st.lines[i], st.lines[i + 1])); st.sel.clear(); renderRows(); }
  function doDel(i) { st.lines.splice(i, 1); st.sel.clear(); renderRows(); }
  function doAdd(i) { const l = st.lines[i]; st.lines.splice(i + 1, 0, { start: l.end, end: l.end + 2, text: '', confidence: null, approx: false, words: [] }); st.sel.clear(); renderRows(); const r = tbody.querySelector('tr[data-i="' + (i + 1) + '"] input.tx'); r && r.focus(); }
  function playRow(i) { const l = st.lines[i]; st.playUntil = l.end; audioEl.currentTime = l.start; audioEl.play().catch(() => {}); }
  function togglePlay() { st.playUntil = null; audioEl.paused ? audioEl.play().catch(() => {}) : audioEl.pause(); }
  function onTime() {
    const now = audioEl.currentTime;
    if (st.playUntil != null && now >= st.playUntil) { audioEl.pause(); st.playUntil = null; }
    let a = -1; st.lines.forEach((l, i) => { if (now >= l.start && now < Math.max(l.end, l.start + 0.05)) a = i; });
    if (a !== st.active) {
      st.active = a;
      [...tbody.querySelectorAll('tr')].forEach(tr => tr.classList.toggle('on', +tr.dataset.i === a));
      const tr = tbody.querySelector('tr.on'); if (tr && !audioEl.paused) tr.scrollIntoView({ block: 'nearest' });
    }
  }
  const textOut = (lines) => L.toEditorText(lines, { timestamps: el.opt.ts.checked, interludes: el.opt.inter.checked, duration: st.duration });
  async function send(mode, lines, individual) {
    lines = lines.filter(l => String(l.text).trim());
    if (!lines.length) { host.toast && host.toast(t('noLines')); return; }
    const text = individual ? L.toEditorText(lines, { timestamps: el.opt.ts.checked, interludes: false }) : textOut(lines);
    if (mode === 'replace' && !individual && host.hasLyrics && host.hasLyrics() && !window.confirm(t('confirmReplace'))) return;
    const ok = await host.apply({ mode: individual ? 'append' : 'replace', text, lines, file, duration: st.duration, title: host.title });
    if (ok === false) return;
    host.toast && host.toast(individual ? (lines.length === 1 ? t('lineSent') : t('sent')) : t('sent'));
    if (!individual) close();
  }
  async function copy() { const text = textOut(st.lines); try { await navigator.clipboard.writeText(text); host.toast && host.toast(t('copied')); } catch (e) { window.prompt('', text); } }
  function dl() { const b = new Blob([L.toLrc(st.lines, host.title || file.name.replace(/\.[^.]+$/, ''))], { type: 'text/plain;charset=utf-8' }); const u = URL.createObjectURL(b); const a = h('a', { href: u, download: (file.name.replace(/\.[^.]+$/, '') || 'lyrics') + '.lrc' }); document.body.appendChild(a); a.click(); a.remove(); setTimeout(() => URL.revokeObjectURL(u), 15000); }

  /* regenerate only the selected section */
  async function regenerate() {
    const idx = [...st.sel].sort((a, b) => a - b); if (!idx.length) return;
    const cs = Math.max(0, st.lines[idx[0]].start - 0.3), ce = Math.min(st.duration || 1e9, st.lines[idx[idx.length - 1]].end + 0.3);
    const p = Object.assign({}, st.reqParams, { language: (st.result && st.result.language) || st.reqParams.language, clip_start: cs.toFixed(2), clip_end: ce.toFixed(2) });
    el.regen.disabled = true; el.regenMsg.hidden = false; el.regenMsg.className = 'lvai-stage small'; el.regenMsg.textContent = t('uploading'); st.running = true; st.cancelled = false;
    try {
      const j = await runJob(p, (ev) => { el.regenMsg.textContent = ev.phase === 'upload' ? t('uploading') + ' ' + Math.round(ev.p * 100) + '%' : (t(ev.job.stage) + ' ' + Math.round((ev.job.progress || 0) * 100) + '%'); });
      const fresh = (j.segments || []).map(normLine);
      st.lines = st.lines.filter(l => !(l.end > cs && l.start < ce)).concat(fresh); sorted(); st.sel.clear(); renderRows();
      el.regenMsg.textContent = t('regenDone') + ' (' + fresh.length + ' ' + t('lines') + ')';
    } catch (e) { el.regenMsg.className = 'lvai-err'; el.regenMsg.textContent = (e.api && e.api.message) || e.message; }
    st.running = false; el.regen.disabled = !st.sel.size;
  }

  viewSetup();
  setTimeout(() => { const f = box.querySelector('select,button'); f && f.focus(); }, 30);
  return { close, state: st, el };
};
root.LVAI = L;
})(window);
