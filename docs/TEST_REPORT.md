# LYRAVOX 1.1.0 — Test report (AI Generate Lyrics)

Every number below comes from a run that was actually executed in the development sandbox (headless Chromium 153, ffmpeg, Python 3).
**The sandbox has no network, no `faster-whisper`, no FastAPI/uvicorn, no Demucs, no Whisper model weights and no speech recordings.**
So: everything around the speech recogniser was tested for real; **the recogniser itself (Whisper), Demucs and the FastAPI process were not run.**

Legend: **REAL** = real code path, real files/sockets/browser · **MOCK** = the speech engine was the test-only placeholder (`FakeTestTranscriber`: text "TEST LINE n" built from silence in the audio; never real lyrics) · **NOT RUN** = could not be executed here.

## The 16 required checks
| # | Check | Result | How |
|---|---|---|---|
| 1 | Existing motion-engine regression | **PASS, REAL** | `dev/smoke_all.py` renders every registered expression: 860 components (184 layout, 125 enter, 52 hold, 109 exit, 130 decor, 62 treat, 66 bg, 36 cam, 69 fx, 27 trans), 0 problems, 0 page errors |
| 2 | Bangla rendering | **PASS, REAL** | same 860 components with Bangla text (`dev/smoke_all_bn.py`, 16:9 and 9:16): 0 problems; `tests/editor_bn.py`: conjuncts stay whole, words not split, preview frame inspected visually. Fonts load from Google Fonts, unreachable in the sandbox, so the visual check used a system fallback font |
| 3 | Audio synchronisation | **PASS, REAL** | 120 BPM test track detected as 120 BPM; beats in the exported MP4 audio sit within 2 ms of the original 0.5 s grid; AI timestamps → editor cut starts equal the lyric tags within 0.02 s |
| 4 | MP4 export | **PASS, REAL** | H.264 1280×720, 254 frames, Opus audio, 10.62 s; PNG sequence 69 frames; transparent PNG has real alpha (0–157) |
| 5 | Audio upload validation | **PASS, REAL** | wrong extension 415; random bytes named .mp3 → 422 `invalid_audio` (content checked with ffprobe); empty 422; oversize 413 (by Content-Length *and* while streaming); too long 413 (a clip of the same file is accepted); bad parameters 422; client refuses oversize/too-long before uploading |
| 6 | Transcription API integration | **PASS (API, UI REAL; engine MOCK)** | `POST/GET/DELETE` + `/api/health` over real HTTP with multipart uploads, structured errors, CORS preflight; browser UI end-to-end against live servers |
| 7 | Bangla transcription | **NOT RUN** | needs the Whisper model + a Bangla recording |
| 8 | English transcription | **NOT RUN** | same |
| 9 | Hindi transcription | **NOT RUN** | same |
| 10 | Timestamp accuracy | **PARTIAL** | REAL: the pipeline puts lines where the audio has sound (placeholder lines start/end within ±0.2 s of the tone boundaries), chunk and clip offsets are applied correctly, the editor honours the tags exactly. **NOT RUN:** Whisper's own timestamp error on real singing |
| 11 | Long audio | **PASS for the pipeline, REAL decode / MOCK engine** | 25-minute audio: cut into 5 chunks at silences (no line straddles a cut), ordered offsets, 150 lines, memory growth +87 MB, 2 s. **NOT RUN:** real-model speed (CPU Whisper is typically slower than real time on small hosts; set `MAX_DURATION_S` accordingly) |
| 12 | Failure handling | **PASS, REAL** | engine exception → `failed`/`transcription_failed` shown in the UI with a retry; timeout → `failed`/`timeout`; undecodable audio; cancel (queued and running); Demucs missing or failing → falls back to the original audio with a warning (separator is MOCK in this test); temp folders gone in every case |
| 13 | Backend unavailable | **PASS, REAL** | unreachable address → red status, "Cannot reach the AI server", retry button, Generate disabled |
| 14 | Lyrics → editor integration | **PASS, REAL** | send all (undoable with Ctrl+Z), single line, selected lines; timestamps and interludes preserved; special characters escaped; song loads with the project; Bangla clusters survive into the engine; project autosaved to the Studio library; export history still logs |
| 15 | Mobile responsive layout | **PASS (emulated)** | Chromium at 390×844 with touch: no horizontal overflow in Studio, editor or the AI dialog; tap targets ≥ 28 px; Bangla UI. Not a physical phone |
| 16 | Nothing existing broken | **PASS, REAL** | landing, Studio flows (projects, import/export, duplicate, delete, audio library → editor), editor boot, exports, regression above all re-run on the final build |

## Suites and counts (final build)
| suite | command | result |
|---|---|---|
| Backend | `cd backend && python -m unittest discover -s tests -p "test_*.py" -t tests` | 63 tests: **53 passed, 10 skipped, 0 failed** (also clean with `-W error::ResourceWarning`) |
| ↳ skipped | | 6 × `test_fastapi_app.py` (fastapi/httpx not installed) and 4 × `test_real_transcription.py` (no model/recordings) — reported as skipped, not passed |
| AI UI + editor integration | `python3 tests/ai_ui_test.py` | **56 / 56 checks** (browser REAL, speech engine MOCK) |
| Studio / landing / mobile | `python3 tests/studio_test.py` | pass, no console errors |
| Editor Bangla + audio + MP4 | `tests/editor_bn.py`, `tests/export_test.py`, `tests/png_test.py` | pass |
| Engine | `dev/smoke_all.py`, `dev/smoke_all_bn.py` | 860 / 860, 0 problems each |

## Not verified — please do before relying on it
* **The real recogniser.** `FasterWhisperTranscriber` (language detection among bn/en/hi, decoding options, word timestamps) and `DemucsSeparator` were written against the libraries' documented APIs but **never executed**. Run `LYRAVOX_REAL=1 python -m unittest discover -s tests -p test_real_transcription.py -t tests` (or `scripts/eval_transcription.py`) with real Bangla / English / Hindi recordings and read the WER and timestamp numbers it prints. Expect weaker Bangla/Hindi than English, especially with `tiny`/`base`.
* **The FastAPI app** (`api.py`) was not started; it is a thin adapter over the tested `service.py`, and `test_fastapi_app.py` runs the same contract tests once `requirements-dev.txt` is installed.
* **Docker image, Render deployment, Vercel deployment** were not built or deployed. Render plan/model advice is guidance, not measurement.

## Defects found and fixed while testing
* Pipe descriptors of ffmpeg subprocesses were not closed (a leak in a long-running server) — caught by `-W error::ResourceWarning`; fixed.
* A job was reported *completed* a few milliseconds before its temp files were deleted; cleanup now happens before the final status is published.
* `DELETE` on a running job left it queryable; it is now hidden immediately and dropped when the worker stops.
* The first test expectations for the editor cut starts, interlude text and clip parameters were wrong (not the product); they now check the real contract (lyric tags in the text sent to the editor, in-page `FormData`).
* Site copy claimed "no upload"; privacy, terms, about and landing text now state that only the optional AI feature uploads audio.
