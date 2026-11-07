"""Test helpers. Audio is generated with ffmpeg (real encoders, real files). The 'speech' is tone bursts separated by silence — NOT
speech — so tests that use it can check audio handling, silence detection, chunking and timestamps plumbing, never recognition quality."""
import os, subprocess, sys, tempfile, shutil, time
os.environ.setdefault('LYRAVOX_ALLOW_FAKE', '1')
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from lyravox_ai.config import Config
from lyravox_ai.engines import FakeTestTranscriber, Word, RawSegment
from lyravox_ai.service import Service

ENCODERS = {
    'wav': ['-c:a', 'pcm_s16le'], 'mp3': ['-c:a', 'libmp3lame', '-b:a', '64k'], 'ogg': ['-c:a', 'libvorbis', '-q:a', '2'],
    'm4a': ['-c:a', 'aac', '-b:a', '64k'], 'aac': ['-c:a', 'aac', '-b:a', '64k', '-f', 'adts'],
}


def tmpdir():
    return tempfile.mkdtemp(prefix='lvtest-')


def make_audio(path, seconds=10.0, on=3.0, off=2.0, fmt=None, rate=16000):
    """Tone bursts: `on` seconds of sound then `off` seconds of silence, repeating."""
    fmt = fmt or os.path.splitext(path)[1][1:]
    expr = f"sin(2*PI*330*t)*0.6*lt(mod(t\\,{on + off})\\,{on})"
    cmd = ['ffmpeg', '-v', 'error', '-y', '-f', 'lavfi', '-i', f'aevalsrc={expr}:d={seconds}:s={rate}', '-ac', '1', '-ar', str(rate)] + ENCODERS[fmt] + [path]
    subprocess.run(cmd, check=True)
    return path


def encoder_available(fmt):
    d = tmpdir()
    try:
        make_audio(os.path.join(d, 't.' + fmt), 1.0, 0.5, 0.2)
        return True
    except Exception:
        return False
    finally:
        shutil.rmtree(d, ignore_errors=True)


def make_service(delay=0.0, fail_on=None, **cfg_kw):
    cfg = Config()
    cfg.tmp_root = os.path.join(tmpdir(), 'jobs')
    for k, v in cfg_kw.items():
        setattr(cfg, k, v)
    eng = FakeTestTranscriber(cfg, delay=delay, fail_on=fail_on)
    return Service(cfg, eng), cfg, eng


def wait_done(svc, job_id, timeout=60):
    t0 = time.time()
    while time.time() - t0 < timeout:
        s = svc.get(job_id)
        if s['status'] in ('completed', 'failed', 'cancelled'):
            return s
        time.sleep(0.05)
    raise AssertionError('job did not finish: ' + str(svc.get(job_id)))


def submit(svc, path, params=None, client='1.1.1.1'):
    with open(path, 'rb') as f:
        data = f.read()
    return svc.create_job(os.path.basename(path), iter([data[i:i + 65536] for i in range(0, len(data), 65536)]), svc.parse_params(params or {}), client, len(data))


def leftover(cfg):
    return [n for n in os.listdir(cfg.tmp_root) if n.startswith('job-')] if os.path.isdir(cfg.tmp_root) else []
