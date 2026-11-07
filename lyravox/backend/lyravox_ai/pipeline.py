"""The transcription pipeline for one job:

   upload -> [vocal separation] -> decode 16 kHz mono -> silence analysis -> chunk plan -> language detection ->
   transcription chunk by chunk -> line building / alignment -> result

Progress is real (seconds of audio processed / total); nothing is simulated. Every step checks the cancel flag and the deadline."""
import os, shutil, time
from . import audio, lines as L
from .errors import AudioError, Cancelled, JobTimeout


class Context:
    """What the pipeline needs from the outside: engines and config."""
    def __init__(self, cfg, transcriber, separator):
        self.cfg, self.transcriber, self.separator = cfg, transcriber, separator


def _check(job):
    if job.cancel.is_set():
        raise Cancelled()
    if time.monotonic() > job.deadline:
        raise JobTimeout()


def run(job, ctx):
    """Fill job.result. Raises Cancelled / JobTimeout / AudioError / Exception; the caller records the outcome. The job's temp folder
    is removed by the caller in a finally block."""
    cfg, p = ctx.cfg, job.params
    work = job.workdir
    clip_s, clip_e = p.get('clip_start'), p.get('clip_end')
    warnings = []
    sep_info = {'requested': bool(p.get('vocal_separation')), 'used': False, 'error': None}

    job.set(stage='preparing', progress=0.01)
    _check(job)
    src = job.src_path
    wav = os.path.join(work, 'audio16k.wav')
    use_sep = sep_info['requested']
    prog_base, prog_sep = 0.03, 0.0
    if use_sep:
        if not ctx.separator.available():
            sep_info['error'] = 'Vocal separation is not available on this server; the original audio was used'
            warnings.append(sep_info['error']); use_sep = False
        else:
            prog_sep = 0.35
    if use_sep:
        job.set(stage='separating', progress=prog_base)
        clip_wav = os.path.join(work, 'clip44k.wav')
        audio.decode(src, clip_wav, clip_s, clip_e, rate=44100, channels=2, cancel=job.cancel, deadline=job.deadline)
        try:
            vocals = ctx.separator.separate(clip_wav, os.path.join(work, 'sep'),
                                            on_progress=lambda v: job.set(progress=prog_base + prog_sep * v),
                                            cancel=job.cancel, deadline=job.deadline)
            audio.decode(vocals, wav, rate=16000, channels=1, cancel=job.cancel, deadline=job.deadline)
            sep_info['used'] = True
        except (Cancelled, JobTimeout):
            raise
        except AudioError as e:                          # separation is optional: fall back to the original audio
            sep_info['error'] = str(e)
            warnings.append(f'{e}. The original audio was used instead.')
            audio.decode(clip_wav, wav, rate=16000, channels=1, cancel=job.cancel, deadline=job.deadline)
        finally:
            shutil.rmtree(os.path.join(work, 'sep'), ignore_errors=True)
            try: os.remove(clip_wav)
            except OSError: pass
    else:
        audio.decode(src, wav, clip_s, clip_e, rate=16000, channels=1, cancel=job.cancel, deadline=job.deadline)

    _check(job)
    info = audio.probe(wav)
    duration = info['duration']
    if duration > cfg.max_duration_s + 1:
        raise AudioError(f'Audio is longer than the {cfg.max_duration_s} s limit')
    base = prog_base + prog_sep
    job.set(stage='analyzing', progress=base)
    silences = audio.detect_silences(wav, cfg.silence_db, cfg.silence_min_s, cancel=job.cancel, deadline=job.deadline)
    chunks = audio.plan_chunks(duration, silences, cfg.chunk_s)

    # language: user choice, or detection restricted to the supported languages
    lang, lang_prob, lang_probs = p.get('language'), None, None
    if lang in (None, '', 'auto'):
        job.set(stage='detecting_language')
        t0 = audio.first_sound(silences, duration)
        probe_wav = os.path.join(work, 'langprobe.wav')
        audio.decode(wav, probe_wav, t0, min(duration, t0 + 30), cancel=job.cancel, deadline=job.deadline)
        _check(job)
        lang, lang_prob, lang_probs = ctx.transcriber.detect_language(probe_wav, cfg.languages, job.cancel)
        try: os.remove(probe_wav)
        except OSError: pass
        job.set(language=lang, language_probability=round(lang_prob, 3), language_detected=True)
    else:
        job.set(language=lang, language_probability=None, language_detected=False)

    job.set(stage='transcribing')
    raw, done = [], 0.0
    word_ts = bool(p.get('word_timestamps', cfg.word_timestamps))
    span = 0.95 - base
    for ci, (a, b) in enumerate(chunks):
        _check(job)
        cw = os.path.join(work, f'chunk{ci}.wav') if len(chunks) > 1 else wav
        if len(chunks) > 1:
            audio.decode(wav, cw, a, b, cancel=job.cancel, deadline=job.deadline)
        cdur = b - a
        def on_prog(v, a=a, cdur=cdur):
            job.set(progress=base + span * min(1.0, (a + cdur * v) / duration))
            if time.monotonic() > job.deadline:
                raise JobTimeout()
        for seg in ctx.transcriber.transcribe(cw, lang, word_ts, on_progress=on_prog, cancel=job.cancel, duration=cdur, offset=a):
            _check(job)
            raw.append(seg)
        if len(chunks) > 1:
            try: os.remove(cw)
            except OSError: pass

    job.set(stage='aligning', progress=0.96)
    out_lines = L.build_lines(raw)
    inst = L.find_instrumentals(out_lines, duration, cfg.interlude_min_s)
    off = float(clip_s or 0.0)
    if off:                                              # a regenerated clip is reported on the original song's timeline
        for l in out_lines:
            l['start'] = round(l['start'] + off, 2); l['end'] = round(l['end'] + off, 2)
            for w in l['words']:
                w['start'] = round(w['start'] + off, 2); w['end'] = round(w['end'] + off, 2)
        for g in inst:
            g['start'] = round(g['start'] + off, 2); g['end'] = round(g['end'] + off, 2)
    if not out_lines:
        warnings.append('No sung or spoken words were detected (instrumental audio, or the vocals were too quiet).')
    job.result = {
        'language': lang, 'language_probability': (round(lang_prob, 3) if lang_prob is not None else None),
        'language_probabilities': ({k: round(v, 3) for k, v in sorted(lang_probs.items(), key=lambda kv: -kv[1])[:5]} if lang_probs else None),
        'duration': round(duration, 2), 'clip': ({'start': clip_s, 'end': clip_e} if (clip_s is not None or clip_e is not None) else None),
        'chunks': len(chunks), 'segments': [{'id': l['id'], 'start': l['start'], 'end': l['end'], 'text': l['text'], 'confidence': l['confidence'],
                                             'approx_timing': l['approx'], 'words': l['words']} for l in out_lines],
        'instrumentals': inst, 'vocal_separation': sep_info, 'model': getattr(ctx.transcriber, 'model_name', ctx.transcriber.name),
        'engine': ctx.transcriber.name, 'warnings': warnings,
    }
    job.set(progress=1.0)
