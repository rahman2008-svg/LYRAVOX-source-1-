/* LYRAVOX project library — shared by the Studio dashboard and the editor (same origin).
   Everything lives in this browser: IndexedDB "lyravox-library" (projects, audio, exports). No server, no account.
   The editor itself keeps ONE "current project" slot (localStorage lyravox.project.v1 + the song in IndexedDB "lyravox" / files / song);
   openInEditor() fills that slot, so the editor's own boot code stays unchanged. */
(function (root) {
'use strict';
const DB = 'lyravox-library', VER = 1;
let dbp = null;
const open = () => dbp || (dbp = new Promise((res, rej) => {
  if (typeof indexedDB === 'undefined') return rej(new Error('IndexedDB is not available in this browser'));
  const r = indexedDB.open(DB, VER);
  r.onupgradeneeded = () => {
    const d = r.result;
    if (!d.objectStoreNames.contains('projects')) d.createObjectStore('projects', { keyPath: 'id' });
    if (!d.objectStoreNames.contains('audio')) d.createObjectStore('audio', { keyPath: 'id' });
    if (!d.objectStoreNames.contains('exports')) d.createObjectStore('exports', { keyPath: 'id' });
  };
  r.onsuccess = () => res(r.result); r.onerror = () => { dbp = null; rej(r.error); };
}));
const tx = async (store, mode, fn) => {
  const db = await open();
  return new Promise((res, rej) => {
    const t = db.transaction(store, mode), s = t.objectStore(store);
    let out; try { out = fn(s); } catch (e) { return rej(e); }
    t.oncomplete = () => res(out && 'result' in out ? out.result : out); t.onerror = () => rej(t.error); t.onabort = () => rej(t.error);
  });
};
const all = (store) => tx(store, 'readonly', s => s.getAll());
const crud = (store) => ({
  list: async () => (await all(store)) || [],
  get: (id) => tx(store, 'readonly', s => s.get(id)),
  put: (rec) => tx(store, 'readwrite', s => { s.put(rec); }),
  delete: (id) => tx(store, 'readwrite', s => { s.delete(id); }),
  clear: () => tx(store, 'readwrite', s => { s.clear(); }),
});
const S = { open, projects: crud('projects'), audio: crud('audio'), exports: crud('exports') };

S.uid = () => Date.now().toString(36) + Math.random().toString(36).slice(2, 8);
S.LS_KEY = 'lyravox.project.v1';
S.CUR_KEY = 'lyravox.currentId';
S.lang = () => { try { return localStorage.getItem('lyravox.lang') === 'bn' ? 'bn' : 'en'; } catch (e) { return 'en'; } };
S.root = () => location.pathname.replace(/(?:studio|editor)\/(?:[a-z-]+\/)?(?:index\.html)?$/, '');
S.editorUrl = () => S.root() + (S.lang() === 'bn' ? 'editor/bn/' : 'editor/');

/* the editor's own song slot (IndexedDB "lyravox", store "files", key "song" — same record shape as src/10_audio.js) */
const editorDb = () => new Promise((res, rej) => {
  const r = indexedDB.open('lyravox', 1);
  r.onupgradeneeded = () => { if (!r.result.objectStoreNames.contains('files')) r.result.createObjectStore('files'); };
  r.onsuccess = () => res(r.result); r.onerror = () => rej(r.error);
});
S.setEditorSong = async (file) => {
  const db = await editorDb();
  const data = file ? await file.arrayBuffer() : null;
  await new Promise((res, rej) => {
    const t = db.transaction('files', 'readwrite'), st = t.objectStore('files');
    if (file) st.put({ name: file.name, type: file.type, data }, 'song'); else st.delete('song');
    t.oncomplete = res; t.onerror = () => rej(t.error);
  });
  db.close();
};
S.getEditorSong = async () => {
  const db = await editorDb();
  const rec = await new Promise((res, rej) => { const q = db.transaction('files', 'readonly').objectStore('files').get('song'); q.onsuccess = () => res(q.result); q.onerror = () => rej(q.error); });
  db.close();
  return rec && rec.data ? new File([rec.data], rec.name || 'song', { type: rec.type || '' }) : null;
};

/* a project record: { id, title, artist, created, updated, thumb, lines, lang, audioId, project } */
S.countLines = (lyrics) => String(lyrics || '').split('\n').filter(l => l.trim() && !/^\s*(#|\/\/)/.test(l)).length;
S.makeRecord = (project, extra) => Object.assign({
  id: S.uid(), title: project.title || '', artist: project.artist || '', created: Date.now(), updated: Date.now(), thumb: '',
  lines: S.countLines(project.lyrics), lang: project.lang || 'auto', audioId: '', project,
}, extra || {});

/* put a library project into the editor slot and go to the editor */
S.openInEditor = async (id) => {
  const rec = await S.projects.get(id);
  if (!rec) throw new Error('Project not found');
  localStorage.setItem(S.LS_KEY, JSON.stringify(rec.project));
  localStorage.setItem(S.CUR_KEY, rec.id);
  if (rec.audioId) {
    const a = await S.audio.get(rec.audioId);
    if (a && a.data) await S.setEditorSong(new File([a.data], a.name, { type: a.type }));
    else await S.setEditorSong(null);
  } else await S.setEditorSong(null);
  location.href = S.editorUrl();
};
/* a fresh project (optionally with lyrics / title / audio) → library → editor */
S.createAndOpen = async (opts) => {
  opts = opts || {};
  let project = opts.project || null;
  if (!project) {
    // keys left out fall back to the editor defaults (sample lyrics of the edition)
    project = {};
    if (opts.lyrics) project.lyrics = opts.lyrics;
    if (opts.title) project.title = opts.title;
    if (opts.artist) project.artist = opts.artist;
  }
  const rec = S.makeRecord(project, { audioId: opts.audioId || '' });
  if (opts.audioId) {
    const a = await S.audio.get(opts.audioId);
    if (a) project.audioName = a.name;
  }
  await S.projects.put(rec);
  await S.openInEditor(rec.id);
};

/* export history */
S.logExport = async (e) => {
  const rec = Object.assign({ id: S.uid(), at: Date.now() }, e);
  await S.exports.put(rec);
  const list = await S.exports.list();
  if (list.length > 300) { list.sort((a, b) => a.at - b.at); for (const x of list.slice(0, list.length - 300)) await S.exports.delete(x.id); }
  return rec;
};

S.fmtBytes = (n) => !n ? '—' : n < 1024 ? n + ' B' : n < 1048576 ? (n / 1024).toFixed(0) + ' KB' : (n / 1048576).toFixed(1) + ' MB';
S.fmtTime = (s) => { s = Math.max(0, Math.round(s || 0)); return Math.floor(s / 60) + ':' + String(s % 60).padStart(2, '0'); };
root.LVStore = S;
})(window);
