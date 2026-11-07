"""Speech-to-text and vocal-separation engines.

* FasterWhisperTranscriber — the real engine (faster-whisper / CTranslate2, open-source Whisper models, runs on this server).
* DemucsSeparator          — optional vocal separation with Demucs (a subprocess, so it can be cancelled and time-limited).
* FakeTestTranscriber      — TEST ONLY. Produces placeholder text from the audio's silence structure so the API / UI plumbing can be
                             tested without a model. It refuses to start unless LYRAVOX_ALLOW_FAKE=1 and never produces real lyrics.
"""
import glob, importlib.util, os, re, sys, threading
from dataclasses import dataclass, field
from . import audio
from .errors import AudioError, Cancelled


@dataclass
class Word:
    start: float
    end: float
    text: str
    probability: float = None


@dataclass
class RawSegment:
    start: float
    end: float
    text: str
    avg_logprob: float = None
    no_speech_prob: float = None
    compression_ratio: float = None
    words: list = field(default_factory=list)


class FasterWhisperTranscriber:
    name = 'faster-whisper'

    def __init__(self, cfg):
        self.cfg = cfg
        self._model = None
        self._lock = threading.Lock()

    @staticmethod
    def installed():
        return importlib.util.find_spec('faster_whisper') is not None

    @property
    def model_name(self):
        return self.cfg.whisper_model

    def model(self):
        with self._lock:
            if self._model is None:
                from faster_whisper import WhisperModel          # imported lazily: the API starts even while the model loads
                kw = {'device': self.cfg.whisper_device, 'compute_type': self.cfg.whisper_compute}
                if self.cfg.whisper_cache:
                    kw['download_root'] = self.cfg.whisper_cache
                self._model = WhisperModel(self.cfg.whisper_model, **kw)
            return self._model

    def warm_up(self):
        self.model()

    def detect_language(self, wav_path, allowed, cancel=None):
        """Return (language, probability, {lang: prob}) restricted to the allowed languages. Whisper's own pick can be a language
        outside the supported set (Bangla singing is often heard as Hindi / Urdu), so the best ALLOWED language wins."""
        m = self.model()
        segs, info = m.transcribe(wav_path, language=None, task='transcribe', beam_size=1, vad_filter=False, without_timestamps=True)
        # info is available before any decoding; the generator is never iterated, so this costs one encoder pass
        probs = {}
        for item in (getattr(info, 'all_language_probs', None) or []):
            try:
                probs[item[0]] = float(item[1])
            except (TypeError, ValueError, IndexError):
                pass
        if not probs:
            probs = {info.language: float(info.language_probability)}
        cand = {k: v for k, v in probs.items() if k in allowed} or probs
        best = max(cand, key=cand.get)
        return best, cand[best], probs

    def transcribe(self, wav_path, language, word_timestamps, on_progress=None, cancel=None, duration=None, offset=0.0):
        m = self.model()
        segs, info = m.transcribe(
            wav_path, language=language, task='transcribe', beam_size=self.cfg.whisper_beam, word_timestamps=word_timestamps,
            vad_filter=True, vad_parameters={'min_silence_duration_ms': 500},
            condition_on_previous_text=False,              # stops a hallucinated phrase from repeating through a whole song
            no_speech_threshold=0.6, compression_ratio_threshold=2.4, log_prob_threshold=-1.0)
        for s in segs:
            if cancel is not None and cancel.is_set():
                raise Cancelled()
            words = [Word(offset + w.start, offset + w.end, w.word, getattr(w, 'probability', None)) for w in (s.words or [])]
            if on_progress and duration:
                on_progress(min(1.0, s.end / duration))
            yield RawSegment(offset + s.start, offset + s.end, s.text.strip(), s.avg_logprob, s.no_speech_prob, s.compression_ratio, words)
        if on_progress:
            on_progress(1.0)


class DemucsSeparator:
    name = 'demucs'

    def __init__(self, cfg):
        self.cfg = cfg

    @staticmethod
    def installed():
        return importlib.util.find_spec('demucs') is not None

    def available(self):
        return self.cfg.demucs_enabled and self.installed()

    def separate(self, src, outdir, on_progress=None, cancel=None, deadline=None):
        """Run demucs --two-stems=vocals on src (a WAV). Returns the path of vocals.wav. Raises AudioError on failure."""
        cmd = [sys.executable, '-m', 'demucs.separate', '-n', self.cfg.demucs_model, '--two-stems', 'vocals', '-d', 'cpu', '-o', outdir, src]
        seen = [0.0]

        def on_err(chunk):                       # demucs prints a tqdm bar:  " 42%|████ ..."
            for m in re.finditer(rb'(\d{1,3})%\|', chunk):
                v = min(100, int(m.group(1))) / 100.0
                if v >= seen[0] and on_progress:
                    seen[0] = v; on_progress(v)
        rc, _, err = audio.run_cmd(cmd, timeout=self.cfg.demucs_timeout_s, cancel=cancel, deadline=deadline, stderr_line=on_err)
        if rc != 0:
            raise AudioError('Vocal separation failed: ' + (err.strip().splitlines()[-1][:200] if err.strip() else 'unknown error'))
        found = glob.glob(os.path.join(outdir, '*', '*', 'vocals.*'))
        if not found:
            raise AudioError('Vocal separation produced no vocal track')
        return found[0]


class FakeTestTranscriber:
    """TEST ONLY — never real transcription. See module docstring."""
    name = 'fake-test-engine'
    model_name = 'fake-test-engine'

    def __init__(self, cfg, delay=0.0, fail_on=None):
        if os.environ.get('LYRAVOX_ALLOW_FAKE') != '1':
            raise RuntimeError('FakeTestTranscriber is for automated tests only (set LYRAVOX_ALLOW_FAKE=1)')
        self.cfg, self.delay, self.fail_on = cfg, delay, fail_on
        self.calls = []

    def warm_up(self):
        pass

    def detect_language(self, wav_path, allowed, cancel=None):
        self.calls.append(('detect', wav_path))
        return (sorted(allowed)[0] if allowed else 'en'), 0.9, {'en': 0.9}

    def transcribe(self, wav_path, language, word_timestamps, on_progress=None, cancel=None, duration=None, offset=0.0):
        import time
        self.calls.append(('transcribe', wav_path, language, offset))
        if self.fail_on == 'transcribe':
            raise RuntimeError('simulated engine failure')
        dur = duration or audio.probe(wav_path)['duration']
        sil = audio.close_silences(audio.detect_silences(wav_path, self.cfg.silence_db, 0.4), dur)
        # "sound" = the stretches between silences; one placeholder line per stretch
        pts, pos = [], 0.0
        for s, e in sil:
            if s - pos > 0.3:
                pts.append((pos, s))
            pos = e
        if dur - pos > 0.3:
            pts.append((pos, dur))
        for i, (a, b) in enumerate(pts):
            if cancel is not None and cancel.is_set():
                raise Cancelled()
            if self.delay:
                time.sleep(self.delay)
            words = []
            label = f'TEST LINE {i + 1}'
            if word_timestamps:
                toks = label.split(' ')
                for k, tk in enumerate(toks):
                    words.append(Word(offset + a + (b - a) * k / len(toks), offset + a + (b - a) * (k + 1) / len(toks), ' ' + tk, 0.9))
            if on_progress:
                on_progress(b / dur)
            yield RawSegment(offset + a, offset + b, label, -0.2, 0.05, 1.0, words)
        if on_progress:
            on_progress(1.0)
