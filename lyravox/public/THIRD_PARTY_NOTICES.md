# Third-party notices (LYRAVOX)

LYRAVOX is a modified version of JIZURA by hakoniwa (MIT License, see LICENSE). Reviewed for LYRAVOX 1.0.0: the only third-party code bundled in the deployed site is mp4-muxer; no font files, images or audio are bundled.

## mp4-muxer 5.2.2 (bundled)

`vendor/mp4-muxer.min.js` is embedded in each editor `index.html` and is used to write MP4 files.
Source: https://github.com/Vanilagy/mp4-muxer — licensed under the MIT License:

```
MIT License

Copyright (c) 2023 Vanilagy

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## AI Generate Lyrics backend (backend/, separate service; nothing below is bundled in the static site)

Python dependencies are installed from `backend/requirements*.txt` and are not vendored here. To the best of our knowledge:
faster-whisper (MIT) with OpenAI Whisper model weights (MIT) and the Silero VAD model it includes (MIT); optional Demucs (MIT) with PyTorch (BSD-style);
FastAPI (MIT), Uvicorn (BSD-3-Clause), python-multipart (Apache-2.0). FFmpeg is invoked as an external program and installed by the host's package manager
(LGPL or GPL depending on the build). Verify these licenses before redistributing the backend container image.

## Fonts (not bundled)

The editor and the site load typefaces at runtime from Google Fonts (https://fonts.google.com/); no font files are included
in this repository, and the browser sends an ordinary web request to Google when a font is needed. The families are
distributed through Google Fonts under open-source font licenses (predominantly the SIL Open Font License 1.1; check each
family's page before redistributing the font files themselves):

- Site and interface: Inter, JetBrains Mono, IBM Plex Mono, IBM Plex Sans JP.
- Japanese: Noto Sans JP, Noto Serif JP, Dela Gothic One, Zen Kaku Gothic New, Zen Old Mincho, Kaisei Tokumin,
  M PLUS Rounded 1c, Mochiy Pop One, DotGothic16, Yuji Syuku (and the other Japanese faces listed in src/02_fonts.js).
- Bangla (added by LYRAVOX): Noto Sans Bengali, Noto Serif Bengali, Hind Siliguri, Baloo Da 2, Tiro Bangla, Galada, Atma, Mina.
- Chinese and Korean faces used by those editions are listed in src/02b_lang.js.

Fonts that a user loads from their own device stay on that device and remain under their own licenses.
