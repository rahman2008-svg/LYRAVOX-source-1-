"""Audio helpers built on ffmpeg / ffprobe (no Python audio libraries): probing, decoding to 16 kHz mono WAV, silence
detection, chunk planning and cutting."""
import json, re, subprocess, threading, time
from .errors import AudioError, Cancelled, JobTimeout

ALLOWED_EXT = ('.mp3', '.wav', '.m4a', '.aac', '.ogg')


def run_cmd(cmd, timeout=300, cancel=None, deadline=None, stderr_line=None):
    """Run a command, polling so a cancel flag / deadline can kill it. Returns (returncode, stdout_bytes, stderr_text)."""
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.DEVNULL)
    out_buf, err_buf = [], []

    def pump(stream, buf, cb=None):
        for chunk in iter(lambda: stream.read(4096), b''):
            buf.append(chunk)
            if cb:
                cb(chunk)
    # ffmpeg / demucs write progress with \r, so hand raw chunks to the callback
    t1 = threading.Thread(target=pump, args=(p.stdout, out_buf), daemon=True)
    t2 = threading.Thread(target=pump, args=(p.stderr, err_buf, stderr_line), daemon=True)
    t1.start(); t2.start()
    t0 = time.monotonic()
    try:
        while p.poll() is None:
            if cancel is not None and cancel.is_set():
                raise Cancelled()
            if deadline is not None and time.monotonic() > deadline:
                raise JobTimeout()
            if time.monotonic() - t0 > timeout:
                raise JobTimeout()
            time.sleep(0.05)
    except BaseException:
        p.kill(); p.wait()
        raise
    finally:
        t1.join(2); t2.join(2)
        for st in (p.stdout, p.stderr):                  # never leak pipe descriptors in a long-running server
            try: st.close()
            except Exception: pass
    return p.returncode, b''.join(out_buf), b''.join(err_buf).decode('utf-8', 'replace')


def probe(path):
    """Return {'duration', 'codec', 'sample_rate', 'channels'} or raise AudioError if there is no decodable audio stream."""
    try:
        rc, out, err = run_cmd(['ffprobe', '-v', 'error', '-show_entries', 'format=duration:stream=codec_type,codec_name,sample_rate,channels,duration',
                                '-of', 'json', path], timeout=30)
    except JobTimeout:
        raise AudioError('The audio file could not be analysed in time')
    except FileNotFoundError:
        raise AudioError('ffprobe is not installed on the server')
    if rc != 0:
        raise AudioError('This file is not a readable audio file')
    try:
        j = json.loads(out.decode('utf-8', 'replace') or '{}')
    except ValueError:
        raise AudioError('This file is not a readable audio file')
    streams = [s for s in j.get('streams', []) if s.get('codec_type') == 'audio']
    if not streams:
        raise AudioError('No audio stream found in this file')
    s = streams[0]
    dur = None
    for v in (j.get('format', {}).get('duration'), s.get('duration')):
        try:
            if v is not None and float(v) > 0:
                dur = float(v); break
        except (TypeError, ValueError):
            pass
    if not dur:
        raise AudioError('Could not determine the audio duration')
    return {'duration': dur, 'codec': s.get('codec_name', ''), 'sample_rate': int(s.get('sample_rate') or 0), 'channels': int(s.get('channels') or 0)}


def decode(src, dst, start=None, end=None, rate=16000, channels=1, cancel=None, deadline=None):
    """Decode (a part of) src to PCM WAV."""
    cmd = ['ffmpeg', '-v', 'error', '-y']
    if start:
        cmd += ['-ss', f'{start:.3f}']
    cmd += ['-i', src]
    if end is not None:
        cmd += ['-t', f'{max(0.0, end - (start or 0)):.3f}']
    cmd += ['-vn', '-ac', str(channels), '-ar', str(rate), '-c:a', 'pcm_s16le', dst]
    rc, _, err = run_cmd(cmd, timeout=600, cancel=cancel, deadline=deadline)
    if rc != 0:
        raise AudioError('Could not decode the audio: ' + err.strip().splitlines()[-1] if err.strip() else 'Could not decode the audio')


def detect_silences(wav, noise_db=-35.0, min_s=0.6, cancel=None, deadline=None):
    """[(start, end)] of silent stretches (ffmpeg silencedetect)."""
    rc, _, err = run_cmd(['ffmpeg', '-v', 'info', '-nostats', '-i', wav, '-af', f'silencedetect=noise={noise_db}dB:d={min_s}', '-f', 'null', '-'],
                         timeout=600, cancel=cancel, deadline=deadline)
    if rc != 0:
        raise AudioError('Silence analysis failed')
    starts = [float(x) for x in re.findall(r'silence_start: (-?[\d.]+)', err)]
    ends = [float(x) for x in re.findall(r'silence_end: (-?[\d.]+)', err)]
    out = []
    for i, s in enumerate(starts):
        e = ends[i] if i < len(ends) else None
        out.append((max(0.0, s), e))
    return out                                   # e is None for a silence that runs to the end of the file


def close_silences(silences, duration):
    return [(s, duration if e is None else e) for s, e in silences]


def first_sound(silences, duration):
    """Time where audio first becomes non-silent."""
    for s, e in close_silences(silences, duration):
        if s <= 0.05:
            return min(e, duration)
        break
    return 0.0


def plan_chunks(duration, silences, chunk_s=300, window_s=30.0):
    """Split [0, duration] into pieces of about chunk_s, cutting in the middle of a silence close to each target when there is
    one (so a sung phrase is not cut in half), otherwise exactly at the target. Returns [(start, end), ...]."""
    if duration <= chunk_s * 1.25:
        return [(0.0, duration)]
    sil = close_silences(silences, duration)
    cuts, pos = [], 0.0
    while duration - pos > chunk_s * 1.25:
        target = pos + chunk_s
        best = None
        for s, e in sil:
            mid = (s + e) / 2
            if abs(mid - target) <= window_s and mid > pos + chunk_s * 0.5 and mid < duration - 5:
                if best is None or abs(mid - target) < abs(best - target):
                    best = mid
        cut = best if best is not None else target
        cuts.append(cut); pos = cut
    pts = [0.0] + cuts + [duration]
    return [(pts[i], pts[i + 1]) for i in range(len(pts) - 1)]
