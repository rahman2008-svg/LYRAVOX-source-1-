"""Turn raw Whisper segments into lyric lines: filtering of music hallucinations, line splitting / merging from word timestamps,
confidence, instrumental gaps, and conversion to the LYRAVOX editor's lyric syntax.

Pure Python, no audio or model dependency, so it is fully unit-testable."""
import math, re, unicodedata

VIRAMA = {0x09CD, 0x094D, 0x0A4D, 0x0ACD, 0x0B4D, 0x0BCD, 0x0C4D, 0x0CCD, 0x0D4D}   # Bengali, Devanagari, ... hasanta / virama
ZWJ = {0x200C, 0x200D}


def clamp01(x):
    return max(0.0, min(1.0, x))


def segment_confidence(seg):
    """0..1 heuristic from Whisper's average log-probability (and word probabilities when present). It is an indicator of how
    sure the model was, not a calibrated probability of being correct."""
    vals = []
    if seg.avg_logprob is not None:
        vals.append(clamp01(math.exp(seg.avg_logprob)))
    wp = [w.probability for w in seg.words if w.probability is not None]
    if wp:
        vals.append(clamp01(sum(wp) / len(wp)))
    if not vals:
        return None
    c = sum(vals) / len(vals)
    if seg.no_speech_prob is not None:
        c *= 1.0 - 0.5 * clamp01(seg.no_speech_prob)
    return round(c, 3)


def is_hallucination(seg):
    """Segments Whisper tends to invent over music / silence."""
    t = seg.text.strip()
    if not t or not re.search(r'\w', t):
        return True
    if seg.no_speech_prob is not None and seg.no_speech_prob > 0.8 and (seg.avg_logprob is None or seg.avg_logprob < -0.8):
        return True
    if seg.compression_ratio is not None and seg.compression_ratio > 2.6:
        return True                                   # repetitive loop such as "la la la la la ..." produced by the decoder
    if seg.avg_logprob is not None and seg.avg_logprob < -1.6:
        return True
    return False


def drop_repeats(segs, keep=2):
    """Keep at most `keep` identical consecutive segments (decoder loops)."""
    out, run, last = [], 0, None
    for s in segs:
        key = re.sub(r'\W+', '', s.text).lower()
        if key == last:
            run += 1
        else:
            run, last = 1, key
        if run <= keep:
            out.append(s)
    return out


def _is_safe_cut(text, i):
    """True if text can be cut before index i without separating a combining mark / conjunct (Bangla, Devanagari ...)."""
    if i <= 0 or i >= len(text):
        return False
    prev, cur = text[i - 1], text[i]
    if unicodedata.category(cur).startswith('M') or ord(cur) in ZWJ:
        return False
    if ord(prev) in VIRAMA or ord(prev) in ZWJ:
        return False
    return True


def split_text_at(text, target):
    """Cut a long text near index `target`, preferring a space or punctuation, never inside a grapheme cluster."""
    best = None
    for off in range(0, min(len(text), 40)):
        for i in (target - off, target + off):
            if 0 < i < len(text) and (text[i - 1] in ' ,.;:!?،।、。' or text[i] == ' ') and _is_safe_cut(text, i):
                best = i; break
        if best: break
    if best is None:
        best = next((i for i in range(target, len(text)) if _is_safe_cut(text, i)), None)
    if best is None:
        return text, ''
    return text[:best].strip(), text[best:].strip()


def _words_to_lines(seg, max_chars, max_s, gap_s):
    """Split a segment into lines using its word timings: at pauses between words, and when a line gets too long."""
    lines, cur, cur_w = [], '', []

    def flush():
        nonlocal cur, cur_w
        t = cur.strip()
        if t:
            lines.append((cur_w[0].start, cur_w[-1].end, t, cur_w))
        cur, cur_w = '', []
    for w in seg.words:
        wt = w.text
        if cur_w:
            pause = w.start - cur_w[-1].end
            too_long = len((cur + wt).strip()) > max_chars or (w.end - cur_w[0].start) > max_s
            if pause > gap_s or too_long:
                flush()
        cur += wt if (cur or wt.startswith(' ')) else wt.lstrip()
        cur_w.append(w)
    flush()
    return lines


def build_lines(raw_segments, max_chars=42, max_s=7.0, gap_s=0.8):
    """Raw segments -> list of dict lines {start, end, text, confidence, words, approx}. `approx` is True when timings of a split
    line were interpolated from text length because the model gave no word timestamps."""
    segs = drop_repeats([s for s in raw_segments if not is_hallucination(s)])
    out = []
    for s in segs:
        conf = segment_confidence(s)
        text = s.text.strip()
        wl = [(a, b, t, ws) for a, b, t, ws in _words_to_lines(s, max_chars, max_s, gap_s)] if s.words else []
        if wl and ''.join(t for _, _, t, _ in wl).replace(' ', '') == text.replace(' ', ''):
            for a, b, t, ws in wl:
                wp = [w.probability for w in ws if w.probability is not None]
                out.append({'start': round(a, 2), 'end': round(b, 2), 'text': t, 'confidence': (round(sum(wp) / len(wp), 3) if wp else conf), 'approx': False,
                            'words': [{'start': round(w.start, 2), 'end': round(w.end, 2), 'text': w.text.strip(), 'confidence': (round(w.probability, 3) if w.probability is not None else None)} for w in ws]})
            continue
        # no (usable) word timestamps: split by length, interpolate times proportionally
        pieces, rest = [], text
        while len(rest) > max_chars:
            a, b = split_text_at(rest, max_chars)
            if not b:
                break
            pieces.append(a); rest = b
        pieces.append(rest)
        total = max(1, sum(len(p) for p in pieces)); pos = s.start
        for p in pieces:
            d = (s.end - s.start) * len(p) / total
            out.append({'start': round(pos, 2), 'end': round(pos + d, 2), 'text': p, 'confidence': conf, 'approx': len(pieces) > 1, 'words': []})
            pos += d
    # no overlaps, sane ordering
    out.sort(key=lambda l: l['start'])
    for i in range(len(out) - 1):
        if out[i]['end'] > out[i + 1]['start']:
            out[i]['end'] = max(out[i]['start'], out[i + 1]['start'])
    for i, l in enumerate(out):
        l['id'] = i + 1
    return out


def find_instrumentals(lines, duration, min_s=6.0):
    """Gaps with no lyric line (intro / break / outro) of at least min_s seconds."""
    gaps, pos = [], 0.0
    for l in lines:
        if l['start'] - pos >= min_s:
            gaps.append({'start': round(pos, 2), 'end': round(l['start'], 2)})
        pos = max(pos, l['end'])
    if duration - pos >= min_s:
        gaps.append({'start': round(pos, 2), 'end': round(duration, 2)})
    return gaps


def fmt_ts(t):
    t = max(0.0, t)
    m = int(t // 60)
    return f'[{m:02d}:{t - m * 60:05.2f}]'


_SPECIAL_START = re.compile(r'^[#\[\s]+')


def sanitize_for_editor(text):
    """Escape characters that mean something in the LYRAVOX lyric syntax: '/' cut, '|' note, '*' emphasis, trailing '!' flash,
    a leading '#' comment and a leading '[' tag."""
    t = text.replace('/', ' ').replace('|', ' ').replace('*', '')
    t = _SPECIAL_START.sub('', t)
    t = re.sub(r'!+$', '', t).strip()
    return re.sub(r'\s{2,}', ' ', t)


def to_editor_lyrics(lines, instrumentals=None, timestamps=True):
    """LRC-style text for the editor: '[mm:ss.xx]text' per line, plus '[mm:ss.xx][interlude N]' for instrumental gaps."""
    rows = []
    for l in lines:
        t = sanitize_for_editor(l['text'])
        if t:
            rows.append((l['start'], (fmt_ts(l['start']) if timestamps else '') + t))
    for g in (instrumentals or []):
        n = max(1, int(g['end'] - g['start'] + 0.5))      # half-up, same as the browser's Math.round
        rows.append((g['start'], (fmt_ts(g['start']) if timestamps else '') + f'[interlude {n}]'))
    rows.sort(key=lambda r: r[0])
    return '\n'.join(r[1] for r in rows)
