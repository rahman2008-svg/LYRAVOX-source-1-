# LYRAVOX — Turn Every Lyric Into a Visual Story.   _v1.1.0 — now with AI Generate Lyrics_

Independent online lyric motion video studio. Write lyrics, add a song, get beat-timed animated typography and export
MP4 / PNG sequence / transparent PNG — all in the browser. No account, no upload, no API keys.

- Developer: **Prince AR Abdur Rahman** · Publisher: **NexVora Lab's Ofc** · Bangladesh · v1.0.0
- Portfolio: https://prince-ar-abdur-rahman.vercel.app
- Based on **JIZURA** by hakoniwa (MIT) — https://github.com/852wa/JIZURA — see `LICENSE`, `THIRD_PARTY_NOTICES.md`.

## What is in the box
| URL | What |
|---|---|
| `/` | Landing page (EN / বাংলা) |
| `/studio/` | Dashboard: projects, import, audio library, lyrics studio, export history (IndexedDB, this browser only) |
| `/editor/` , `/editor/bn/` | The editor (English, বাংলা). Also `/editor/ja/ zh-hant/ zh-hans/ ko/ id/ vi/` |
| `/about/ /developer/ /credits/ /privacy/ /terms/ /contact/` | Pages, `404.html`, `sitemap.xml`, `robots.txt`, `manifest.webmanifest` |

The editor is the original JIZURA engine (860 motion components, beat detection, tap-sync, timeline, MP4 / PNG export,
LRC import/export, project save/load, aspect ratios, resolution/fps, mobile mode), rebranded, with:
Bangla edition (grapheme-cluster-safe text layout, Bengali fonts, translated UI), Studio library integration (autosave to
the library, export logging), LYRAVOX theme and loading screen.

## AI Generate Lyrics (new in 1.1.0)
Upload a song (mp3, wav, m4a, aac, ogg) and let AI detect the sung lyrics in **Bangla, English or Hindi**, with automatic or manual language choice, optional vocal separation (Demucs), line and word timestamps and confidence indicators.
Review them in a line editor, then send them to the editor with their timestamps; the existing motion components, effects and export engine work on them exactly as on typed lyrics.

* **Where:** Studio → *Audio Library* (✨ AI Generate Lyrics on every song, and in the toolbar), Studio → *Lyrics Studio* (*From audio*), and the editor's *Audio* section.
* **Dialog:** file info, language (auto-detect / Bangla / English / Hindi), vocal separation toggle, *Generate Lyrics*, real progress and status (upload %, then the server's real stage/progress), errors, *Cancel* (stops the server job).
* **Lyrics editor:** edit text, edit start/end times (↑/↓ nudge 0.1 s), split at the cursor, merge, delete, add, play a line, whole-song playback with the current line highlighted, *Regenerate selected lines* (re-transcribes just that section), reset, copy, download `.lrc`.
* **Send to the editor:** *Send all* (replaces the lyrics; undoable with Ctrl+Z in the editor), *→* on a line (appends one line), *Send selected*. Timestamps become `[mm:ss.xx]` tags the engine uses as line start times; instrumental gaps become `[interlude N]`. Characters that mean something in the lyric syntax are escaped.

### Architecture
```
Browser (Vercel, static)                               Backend (Render, Docker)
 Studio / editor ── aigen.js ──REST──▶  FastAPI  ─▶ job queue ─▶ ffmpeg ─▶ [Demucs] ─▶ faster-whisper ─▶ lines
   └ project library (IndexedDB)         POST/GET/DELETE /api/transcribe, GET /api/health   (temp files deleted after each job)
```
The frontend stays a static site; **everything except AI Generate Lyrics works without the backend**. The AI feature is *not* offline: it needs the backend (see [docs/OFFLINE_TRANSCRIPTION.md](docs/OFFLINE_TRANSCRIPTION.md) for the browser-only investigation: not implemented). Audio is uploaded to the backend only when you press *Generate*; the backend deletes it when the job ends.

### Setup
1. **Backend** — see [backend/README.md](backend/README.md) (local run, Docker, Render, all environment variables). API: [docs/API.md](docs/API.md).
2. **Render:** *New → Blueprint* on this repository (`render.yaml`), set `ALLOWED_ORIGINS` to your Vercel domain.
3. **Connect the frontend (Vercel):** set `apiUrl` in `site/assets/config.js` and run `python3 build.py` (or, to skip the rebuild, edit the committed `public/config.js` directly; the next build would overwrite it):
   ```js
   window.LYRAVOX_CONFIG = { apiUrl: "https://your-service.onrender.com" };
   ```
   commit and redeploy. Alternatives: build with `LYRAVOX_API_URL=https://…  python3 build.py` (writes it into `public/config.js`), or let each user type the address in the AI dialog (*Section & server*, stored in their browser). On `localhost` the default is `http://localhost:8000`.
4. Local try-out without a model: `LYRAVOX_ALLOW_FAKE=1 python -m lyravox_ai.devserver --fake` runs a **placeholder** engine (text "TEST LINE n") that exercises the UI. It is for testing only and the UI labels it.

### Known limitations of AI Generate Lyrics
* Whisper is a speech model; singing over loud music is hard for it. Expect errors and missed/invented words, and clearly weaker Bangla and Hindi than English, especially with `tiny`/`base`. Use `small` or larger for Bangla/Hindi, enable vocal separation for dense mixes, and always review the result. No accuracy figure for Bangla/Hindi was measured in this project (see [docs/TEST_REPORT.md](docs/TEST_REPORT.md)).
* The free Render plan is slow, sleeps when idle and has little memory.
* Job state lives in the server's memory (one process); a restart loses it.
* Timestamps from Whisper are typically good to a fraction of a second but can drift on long held notes; adjust them in the line editor.

## Build & deploy
Requires Python 3 only (no npm dependencies).

```bash
python3 build.py                      # writes public/
SITE_URL=https://your-domain.com python3 build.py   # canonical URLs, sitemap and Open Graph use this address
python3 -m http.server 8800 --directory public       # preview at http://localhost:8800/
```

`public/` is committed, so **Vercel needs no build step**: import the GitHub repo, framework "Other", output directory
`public` (already set in `vercel.json`). The default `SITE_URL` is `https://lyravox.vercel.app` — set your real domain and rebuild
before publishing so canonical/OG/sitemap URLs are correct.

## Layout of the source
`src/*.js` engine + UI (concatenated in file order) · `src/02c_bangla.js` Bangla language + cluster packing ·
`src/13_lyravox.js` Studio integration · `app/` editor HTML/CSS, i18n glossaries (`app/bn/*.tsv` = Bangla) ·
`app/store.js` shared project library · `site/` site generator + assets · `build.py` · `tests/` browser tests (Playwright) ·
`dev/smoke_all.py` renders every registered motion expression · `app/aigen.js` + `aigen.css` AI dialog · `backend/` AI service · `docs/` API, test report, offline assessment.

## Tests (Playwright + Chromium)
```bash
python3 build.py && python3 -m http.server 8800 --directory public &
python3 tests/editor_bn.py      # Bangla boot, planning, rendering
python3 tests/export_test.py    # audio analysis, MP4 export, library + export history
python3 tests/png_test.py       # PNG sequence + transparent PNG
python3 tests/studio_test.py    # landing, Studio flows, import/export, mobile layout
python3 tests/ai_ui_test.py     # AI Generate Lyrics UI + editor integration (starts its own test servers; placeholder speech engine)
(cd backend && python3 -m unittest discover -s tests -p 'test_*.py' -t tests)   # backend, see backend/README.md
python3 build.py --dev && python3 dev/build_test.py all --all-packs   # then: python3 dev/smoke_all.py t_all
```

## Notes
- Fonts load from Google Fonts at runtime (not bundled). Offline, the browser falls back to system fonts.
- MP4 export uses WebCodecs: use current Chrome or Edge (Android Chrome included).
- Privacy: editing, projects and exports never leave the browser; only the optional AI feature uploads audio (to your backend).
- The "AE" button in the editor still writes the After Effects data file; the After Effects panel itself is not part of this
  repository (it is still JIZURA-branded upstream).
