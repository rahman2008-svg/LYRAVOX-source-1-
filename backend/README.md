# LYRAVOX AI backend

Speech-to-text for the **AI Generate Lyrics** feature: FastAPI + faster-whisper (open-source Whisper), optional Demucs vocal separation. No API keys, no paid service.
REST contract: [`../docs/API.md`](../docs/API.md).

```
Audio upload → [Demucs vocal separation] → 16 kHz mono → silence analysis → chunking → language detection → faster-whisper → lyric lines
```

## Run locally
System package: **ffmpeg** (with ffprobe). Python 3.10+.

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt                 # FastAPI, uvicorn, faster-whisper
# optional vocal separation (large, pulls in PyTorch):
#   pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu && pip install -r requirements-demucs.txt
cp .env.example .env                            # then export the variables you want (or set them inline)
WHISPER_MODEL=base uvicorn lyravox_ai.api:app --host 0.0.0.0 --port 8000
```
The first request downloads the model (a few hundred MB for `small`). Check: `curl localhost:8000/api/health`.

**Dependency-free dev server** (stdlib only, same REST contract, reads uploads into memory — development only):
`python -m lyravox_ai.devserver --port 8000`

Point the frontend at it: in the AI dialog open *Section & server*, or set `apiUrl` in `config.js` (see the root README).

## Deploy on Render
`render.yaml` in the repository root defines the service (Docker, because ffmpeg must be installed).
1. Render dashboard → **New → Blueprint** → select this repository → apply.
2. Set `ALLOWED_ORIGINS` to your Vercel domain (comma separated list; `*` allows every site).
3. Wait for the build (it downloads the Whisper model into the image), then open `https://<service>.onrender.com/api/health`.
4. Put that URL into the frontend's `config.js` (`apiUrl`), redeploy the frontend.

Choosing a plan and model (guidance, **not measured by the authors on Render**): `free` (512 MB, sleeps when idle, slow) → `tiny`; `starter` (512 MB) → `base`;
`standard` (2 GB) → `small`, which is the smallest model we would call usable for Bangla/Hindi; Demucs needs about 2 GB and is slow on CPU.
Build with Demucs: set the Docker build arg `INSTALL_DEMUCS=1`.

## Environment variables
See [`.env.example`](.env.example). None is secret.

| variable | default | purpose |
|---|---|---|
| `WHISPER_MODEL` | `base` | `tiny`, `base`, `small`, `medium`, `large-v3` or a model path |
| `WHISPER_DEVICE` / `WHISPER_COMPUTE` | `cpu` / `int8` | CTranslate2 device and precision |
| `WHISPER_BEAM`, `WORD_TIMESTAMPS` | `5`, `true` | decoding beam size; per-word timings |
| `MAX_UPLOAD_MB` | `50` | upload size limit |
| `MAX_DURATION_S` | `900` | longest audio / clip accepted |
| `CHUNK_S` | `300` | chunk length for long audio (cut at silences) |
| `MAX_CONCURRENT_JOBS` | `1` | jobs processed at once |
| `MAX_QUEUE` / `MAX_ACTIVE_PER_IP` | `6` / `2` | queue size; unfinished jobs per client |
| `JOB_TIMEOUT_S` / `JOB_TTL_S` | `1800` / `1800` | per-job deadline; how long results are kept |
| `ALLOWED_LANGUAGES` | `bn,en,hi` | languages offered |
| `ALLOWED_ORIGINS` | `*` | CORS origins |
| `DEMUCS_ENABLED`, `DEMUCS_MODEL`, `DEMUCS_TIMEOUT_S` | `1`, `htdemucs`, `900` | optional vocal separation |
| `INTERLUDE_MIN_S` | `6` | gaps at least this long are reported as instrumental |
| `PRELOAD_MODEL` | `1` | load the model in the background at start |
| `LYRAVOX_TMP` | system temp | working folder |

## Tests
```bash
cd backend
python -m unittest discover -s tests -p "test_*.py" -t tests       # no extra packages needed
```
* `test_audio.py` – REAL ffmpeg/ffprobe on generated audio in all five formats, silence detection, chunk planning.
* `test_lines.py` – line building / hallucination filtering / Bangla-safe splitting on **synthetic** segments.
* `test_service_jobs.py` – REAL validation, job lifecycle, cancel, timeout, limits, concurrency, cleanup, 25-minute chunked run. The speech engine is the **test-only placeholder**.
* `test_http_contract.py` – REAL sockets and multipart uploads against the stdlib server (placeholder engine).
* `test_fastapi_app.py` – the same contract against the FastAPI app; **skipped unless** `pip install -r requirements-dev.txt`.
* `test_real_transcription.py` – **real Whisper** on your recordings (`tests/audio/{bn,en,hi}.*` + `.txt` references); skipped unless `LYRAVOX_REAL=1`, faster-whisper and recordings exist.
* `scripts/eval_transcription.py DIR` – prints WER / CER / timestamp error for your recordings.

The placeholder engine (`FakeTestTranscriber`) refuses to start without `LYRAVOX_ALLOW_FAKE=1` and is never used by `api.py` unless you wire it in yourself.

## Known limitations
* Whisper is a speech model. **Singing over loud instruments is hard for it**; expect mistakes, missed or invented words, and weaker results for Bangla and Hindi than for English, especially with the small models. Enable vocal separation on dense mixes. Lyrics must be reviewed by a person.
* `confidence` is a heuristic, not a probability of being correct.
* Job state is in memory, one process: a restart loses running and finished jobs (clients get a clear 404 / network error). Run one worker (`--workers 1`).
* FastAPI spools multipart uploads to disk before the handler runs; oversized uploads are refused early from the Content-Length header, but a client that lies about it can still make the server receive up to the proxy's limit.
* Language detection is restricted to the supported languages; audio in another language will be forced into the nearest supported one.
