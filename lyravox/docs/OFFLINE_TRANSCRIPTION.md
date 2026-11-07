# Is browser-only (offline) transcription feasible for LYRAVOX?

**Status: investigated, NOT implemented. LYRAVOX 1.1.0 does not claim any offline AI.** The AI lyrics feature requires the LYRAVOX AI backend (network).
The rest of LYRAVOX (editing, beat detection, export) already runs in the browser; it still loads fonts from Google Fonts unless they are cached.

## What was possible to check in the development sandbox
The sandbox has no network, no browser model files and no speech recordings, so **nothing below was run or measured**. This is an assessment from how the pieces work, to be verified before relying on it.

## The candidate
Whisper compiled for the browser: ONNX Runtime Web (WASM, optionally WebGPU) running Whisper `tiny` / `base` / `small` ONNX exports (for example through transformers.js, Apache-2.0; Whisper is MIT).
It decodes audio in the page, so it would need no server and no upload.

## Findings
| question | assessment |
|---|---|
| Can it run in a static, Vercel-hosted page? | Yes in principle: static JS + WASM + model files; no backend. |
| Model download | Not offline on first use. `tiny` is on the order of tens of MB, `base` roughly a hundred, `small` a few hundred (quantised, approximate). Files would have to be self-hosted (Vercel static limits apply) or fetched from a model hub. After the first download the browser can cache them and work offline. |
| Memory / speed on Android Chrome | Risky. `base` and above can exceed phone memory; WASM CPU inference is several times slower than real time for long songs on mid-range phones; WebGPU is not available everywhere. |
| Accuracy for Bangla and Hindi | The documented weak point: the small Whisper models are least accurate exactly for these languages, and for singing over music. The server path can use `small`/`medium`, which is a quality step the browser cannot afford. **Not measured here.** |
| Word timestamps | Possible with the right export, but adds memory and code. |
| Vocal separation | Not realistic in the browser at acceptable size and speed. |
| Does it risk the existing app? | It must not be bundled into the editor (several MB of JS/WASM). If ever added it should be an opt-in lazy-loaded module with its own memory guard, so the 860-component engine and exports are unaffected. |

## Recommendation
1. Keep the server path (faster-whisper) as the supported way; it is the only one that can plausibly serve Bangla/Hindi acceptably.
2. If an offline mode is wanted later, add a lazy-loaded **"Lite (offline, beta)"** option with `tiny`/`base`, English-first, clearly labelled as lower quality, after measuring Bangla/Hindi accuracy on real recordings with `backend/scripts/eval_transcription.py`-style data.
3. Do not call the system offline until a real offline run (airplane mode, cached model) has been tested.
