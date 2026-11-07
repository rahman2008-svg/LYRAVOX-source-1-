# LYRAVOX AI — REST API

Base URL: the address of the backend (for example `https://lyravox-ai.onrender.com`, or `http://localhost:8000`). No authentication and no API keys.
All responses are JSON (`application/json; charset=utf-8`). CORS: origins listed in `ALLOWED_ORIGINS`.

Errors always have this shape (the HTTP status is the one in the table):

```json
{ "error": { "code": "file_too_large", "message": "The file is larger than the 50 MB limit." } }
```

## `GET /api/health`
Engine, limits and queue state. The UI uses it to enable the dialog and to validate files before uploading.

```json
{
  "status": "ok", "version": "1.1.0", "engine": "faster-whisper", "engine_available": true, "model": "base",
  "vocal_separation_available": false, "languages": ["bn", "en", "hi"],
  "limits": { "max_upload_mb": 50, "max_duration_s": 900, "chunk_s": 300, "job_timeout_s": 1800 },
  "queue": { "active": 0, "running": 0, "max": 6 }, "formats": [".mp3", ".wav", ".m4a", ".aac", ".ogg"]
}
```
`status` is `degraded` when the speech engine is not installed.

## `POST /api/transcribe`
`multipart/form-data`. **Content-Length is required.** Returns **202** immediately; the work happens in the background.

| field | type | default | meaning |
|---|---|---|---|
| `file` | file | — | audio: mp3, wav, m4a, aac, ogg. The content is verified with ffprobe; the extension alone is not trusted |
| `language` | string | `auto` | `auto` or one of `languages` from `/api/health`. `auto` detects among the supported languages only |
| `vocal_separation` | bool | `false` | separate vocals with Demucs first. Falls back to the original audio (with a warning) if unavailable or failing |
| `word_timestamps` | bool | server default (`true`) | per-word timings, used to split lines at real pauses |
| `clip_start`, `clip_end` | seconds | whole file | transcribe only this section (used by "Regenerate selected lines"). Returned times are on the original song's timeline |

```json
{ "job_id": "9f2c…", "status": "queued", "poll_url": "/api/transcribe/9f2c…" }
```

| status | code | when |
|---|---|---|
| 413 | `file_too_large` | larger than `MAX_UPLOAD_MB` (checked from Content-Length, and again while streaming) |
| 413 | `duration_exceeded` | longer than `MAX_DURATION_S` (after applying a clip range) |
| 411 | `length_required` | no Content-Length |
| 415 | `unsupported_type` | extension not in the list |
| 422 | `invalid_audio` / `empty_file` / `missing_file` / `unsupported_language` / `invalid_parameter` | the file is not decodable audio, empty, absent, or a field is invalid |
| 429 | `too_many_jobs` | this client already has `MAX_ACTIVE_PER_IP` unfinished jobs |
| 503 | `server_busy` | `MAX_QUEUE` jobs are already waiting or running |

## `GET /api/transcribe/{job_id}`
Status while running, result when done. `progress` is 0–1 and never goes backwards; it is computed from seconds of audio processed.

```json
{
  "job_id": "9f2c…", "status": "completed", "stage": "completed", "progress": 1.0,
  "input": { "filename": "song.mp3", "size": 4311023, "duration": 214.6, "codec": "mp3" },
  "language": "bn", "language_probability": 0.93, "language_detected": true,
  "language_probabilities": { "bn": 0.93, "hi": 0.05, "en": 0.01 },
  "duration": 214.6, "clip": null, "chunks": 1, "engine": "faster-whisper", "model": "base",
  "segments": [
    { "id": 1, "start": 12.4, "end": 16.1, "text": "…", "confidence": 0.81, "approx_timing": false,
      "words": [ { "start": 12.4, "end": 12.9, "text": "…", "confidence": 0.9 } ] }
  ],
  "instrumentals": [ { "start": 0.0, "end": 12.4 } ],
  "vocal_separation": { "requested": true, "used": false, "error": "…" },
  "warnings": []
}
```
* `status`: `queued` → `running` → `completed` | `failed` | `cancelled`.
* `stage`: `queued`, `preparing`, `separating`, `analyzing`, `detecting_language`, `transcribing`, `aligning`, `completed`…
* `confidence`: 0–1 heuristic from Whisper's log-probabilities. It indicates how sure the model was, **not** a calibrated probability of being right. `null` if the engine gives none.
* `approx_timing`: `true` when a long segment had to be split without word timestamps, so the new line times were interpolated from text length.
* `instrumentals`: gaps of at least `INTERLUDE_MIN_S` between lyric lines (intro, breaks, outro).
* Failure: `"status": "failed", "error": {"code": "timeout" | "transcription_failed" | "audio_error" | "out_of_memory", "message": "…"}`.
* Results are kept for `JOB_TTL_S` (30 min) and then answer **404** `job_not_found`.

## `DELETE /api/transcribe/{job_id}`
Cancels a queued or running job (the running work stops at its next check, the Demucs process is killed) and forgets it. Always `200 {"job_id": "…", "status": "cancelled" | "deleted"}`; unknown id → 404. The uploaded audio is deleted as soon as processing stops.

## Processing guarantees
* The upload and every derived file live in a private temp folder, deleted **before** the final status is published (completed, failed, cancelled, timed out). Leftover folders from a crash are removed at start.
* At most `MAX_CONCURRENT_JOBS` jobs run at once; the rest wait in a bounded queue. Submissions are admitted atomically, so the limits hold under concurrent requests.
* Long audio is split at silences into chunks of about `CHUNK_S` seconds and transcribed chunk by chunk, so memory does not grow with song length. The language is decided once and reused for all chunks.
* Each job has a deadline (`JOB_TIMEOUT_S`).

## Using the output in the LYRAVOX editor
The editor accepts `[mm:ss.xx]text` lines and `[mm:ss.xx][interlude N]` breaks. The frontend converts segments to that form and escapes characters that have meaning in the lyric syntax (`/`, `|`, `*`, a trailing `!`, a leading `#` or `[`).
