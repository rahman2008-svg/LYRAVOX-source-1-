"""REAL speech-recognition tests with the actual faster-whisper model on real recordings.

These tests are SKIPPED unless all of the following are true (none of them were available in the sandbox where this repository was written,
which has no network, no faster-whisper and no speech recordings — so NO recognition result in this project has been verified there):

  1. `pip install faster-whisper` and the model can be loaded (WHISPER_MODEL, default 'base'; needs a download on first use)
  2. recordings exist:  backend/tests/audio/bn.wav  en.wav  hi.wav   (any format ffmpeg reads; sung or spoken)
  3. a reference next to each recording:  bn.txt / en.txt / hi.txt  (the true words, one line per phrase)
  Optional timing reference:  bn.times.json  = [[start_s, end_s], ...] for each phrase.

Run:  LYRAVOX_REAL=1 python -m unittest discover -s tests -p test_real_transcription.py -t tests
Quality gate (adjustable with env): WER <= REAL_MAX_WER (default 0.6 — Whisper on singing is far from perfect), median start-time error <= REAL_MAX_START_ERR (default 1.0 s).
The numbers are printed so you can judge them yourself; scripts/eval_transcription.py gives the same report for any folder."""
import importlib.util, json, os, re, time, unittest
from helpers import *

AUDIO = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'audio')
HAVE = bool(importlib.util.find_spec('faster_whisper')) and os.environ.get('LYRAVOX_REAL') == '1'


def wer(ref, hyp):
    r, h = ref.split(), hyp.split()
    d = [[0] * (len(h) + 1) for _ in range(len(r) + 1)]
    for i in range(len(r) + 1): d[i][0] = i
    for j in range(len(h) + 1): d[0][j] = j
    for i in range(1, len(r) + 1):
        for j in range(1, len(h) + 1):
            d[i][j] = min(d[i - 1][j] + 1, d[i][j - 1] + 1, d[i - 1][j - 1] + (r[i - 1] != h[j - 1]))
    return d[len(r)][len(h)] / max(1, len(r))


def norm(t): return re.sub(r'[^\w\s]', '', t.lower()).strip()


@unittest.skipUnless(HAVE, 'faster-whisper not installed or LYRAVOX_REAL!=1: REAL transcription NOT tested in this environment')
class RealTranscription(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from lyravox_ai.config import Config
        from lyravox_ai.service import Service
        cfg = Config.from_env(); cfg.tmp_root = os.path.join(tmpdir(), 'jobs'); cfg.job_timeout_s = 1800
        cls.svc = Service(cfg)

    @classmethod
    def tearDownClass(cls):
        cls.svc.shutdown()

    def _run(self, lang, language):
        found = [os.path.join(AUDIO, f'{lang}.{e}') for e in ('wav', 'mp3', 'm4a', 'ogg', 'aac') if os.path.exists(os.path.join(AUDIO, f'{lang}.{e}'))]
        ref = os.path.join(AUDIO, f'{lang}.txt')
        if not found or not os.path.exists(ref):
            self.skipTest(f'no tests/audio/{lang}.* recording + {lang}.txt reference supplied')
        job = submit(self.svc, found[0], {'language': language})
        st = wait_done(self.svc, job.id, timeout=1800)
        self.assertEqual(st['status'], 'completed', st.get('error'))
        hyp = norm(' '.join(s['text'] for s in st['segments'])); truth = norm(open(ref, encoding='utf-8').read())
        w = wer(truth, hyp)
        print(f'\n   [{lang}] language={st["language"]} WER={w:.2f} model={st["model"]} lines={len(st["segments"])}')
        self.assertLessEqual(w, float(os.environ.get('REAL_MAX_WER', 0.6)))
        tj = os.path.join(AUDIO, f'{lang}.times.json')
        if os.path.exists(tj):
            ref_t = json.load(open(tj)); errs = sorted(abs(a['start'] - b[0]) for a, b in zip(st['segments'], ref_t))
            med = errs[len(errs) // 2]; print(f'   [{lang}] median start-time error {med:.2f} s over {len(errs)} lines')
            self.assertLessEqual(med, float(os.environ.get('REAL_MAX_START_ERR', 1.0)))
        return st

    def test_bangla(self): self._run('bn', 'bn')
    def test_english(self): self._run('en', 'en')
    def test_hindi(self): self._run('hi', 'hi')

    def test_auto_detects_among_supported_languages(self):
        for lang in ('bn', 'en', 'hi'):
            if not any(os.path.exists(os.path.join(AUDIO, f'{lang}.{e}')) for e in ('wav', 'mp3', 'm4a', 'ogg', 'aac')): continue
            with self.subTest(lang=lang):
                st = self._run(lang, 'auto'); self.assertEqual(st['language'], lang)


if __name__ == '__main__':
    unittest.main()
