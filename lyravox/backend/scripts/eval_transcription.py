#!/usr/bin/env python3
"""Evaluate REAL transcription quality on your own recordings (needs faster-whisper + a model).

    python scripts/eval_transcription.py DIR [--language bn] [--model small]

DIR holds  name.<audio>  +  name.txt (reference words)  [+ name.times.json = [[start, end], ...] per phrase].
Prints, per file: detected language, word error rate, character error rate, median / 90th-percentile start-time error, and the
transcript, so you can judge Bangla / English / Hindi quality on the material you care about."""
import argparse, glob, json, os, re, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from lyravox_ai.config import Config
from lyravox_ai.service import Service


def edit(a, b):
    d = list(range(len(b) + 1))
    for i in range(1, len(a) + 1):
        p, d[0] = d[0], i
        for j in range(1, len(b) + 1):
            p, d[j] = d[j], min(d[j] + 1, d[j - 1] + 1, p + (a[i - 1] != b[j - 1]))
    return d[len(b)]


def norm(t): return re.sub(r'[^\w\s]', '', t.lower()).strip()


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('dir'); ap.add_argument('--language', default='auto'); ap.add_argument('--model'); a = ap.parse_args()
    cfg = Config.from_env()
    if a.model: cfg.whisper_model = a.model
    cfg.max_duration_s = 3600; cfg.job_timeout_s = 7200
    svc = Service(cfg)
    files = [f for f in sorted(glob.glob(os.path.join(a.dir, '*'))) if f.lower().endswith(('.wav', '.mp3', '.m4a', '.aac', '.ogg'))]
    for f in files:
        base = os.path.splitext(f)[0]; t0 = time.time()
        with open(f, 'rb') as fh: data = fh.read()
        job = svc.create_job(os.path.basename(f), iter([data]), svc.parse_params({'language': a.language}), 'eval')
        while True:
            st = svc.get(job.id)
            if st['status'] in ('completed', 'failed'): break
            time.sleep(0.5)
        print(f'\n== {os.path.basename(f)}  status={st["status"]}  {time.time() - t0:.0f}s  model={st.get("model")}')
        if st['status'] != 'completed': print('   ', st.get('error')); continue
        hyp = norm(' '.join(s['text'] for s in st['segments']))
        print(f'   language={st["language"]} (p={st.get("language_probability")})  lines={len(st["segments"])}  warnings={st["warnings"]}')
        if os.path.exists(base + '.txt'):
            ref = norm(open(base + '.txt', encoding='utf-8').read())
            w = edit(ref.split(), hyp.split()) / max(1, len(ref.split())); c = edit(list(ref), list(hyp)) / max(1, len(ref))
            print(f'   WER={w:.3f}  CER={c:.3f}')
        if os.path.exists(base + '.times.json'):
            ref_t = json.load(open(base + '.times.json')); errs = sorted(abs(s['start'] - r[0]) for s, r in zip(st['segments'], ref_t))
            if errs: print(f'   start error: median {errs[len(errs) // 2]:.2f}s  p90 {errs[int(len(errs) * .9)]:.2f}s  over {len(errs)} lines')
        for s in st['segments']: print(f'   [{s["start"]:7.2f}-{s["end"]:7.2f}] ({s["confidence"]}) {s["text"]}')
    svc.shutdown()


if __name__ == '__main__':
    main()
