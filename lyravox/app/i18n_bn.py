"""LYRAVOX Bangla (বাংলা) edition glossary.
Keys are the original Japanese phrases (same keys as app/english.py); values are Bangla. The Bangla text lives in app/bn/*.tsv
(one entry per line: <index>TAB<value>, index = position in the English glossary of the same section). Anything not translated
falls back to the English value. build.py runs check() so a broken placeholder fails the build instead of the editor."""
import os, re
from app import english

_HERE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'bn')

def _load(name):
    out = {}
    with open(os.path.join(_HERE, name + '.tsv'), encoding='utf-8') as f:
        for line in f.read().split('\n'):
            if not line: continue
            i, _, v = line.partition('\t')
            out[int(i)] = v
    return out

def _section(name, en):
    bn = _load(name)
    keys = list(en.keys())
    res = {}
    for i, k in enumerate(keys):
        res[k] = bn.get(i, en[k])
    return res

BODY = _section('body', english.BODY)
UI = _section('ui', english.UI)
EXPORT = _section('export', english.EXPORT)

_TOK = re.compile(r'\$\{[^}]*\}|<[^>]+>|\bid="[^"]*"|\bvalue="[^"]*"|\[interlude[^\]]*\]')
def _norm(t):
    t = re.sub(r'\s(aria-label|title)="[^"]*"', '', t)                      # translated attribute text
    return re.sub(r"'[^']*'", "''", t)                                      # string literals inside ${ ... }

def check():
    """every markup tag / ${expression} / id / value in the English text must appear unchanged in the Bangla text"""
    bad = []
    for sec, en, bn in (('BODY', english.BODY, BODY), ('UI', english.UI, UI), ('EXPORT', english.EXPORT, EXPORT)):
        for k in en:
            if 'value="bn"' in bn[k]: continue             # the Bangla edition adds its own language option
            a, b = sorted(_norm(x) for x in _TOK.findall(en[k])), sorted(_norm(x) for x in _TOK.findall(bn[k]))
            if a != b: bad.append((sec, en[k][:70], [t for t in a if t not in b][:3]))
    return bad

STYLES = {
    'hrRuin': ('ধ্বংসাবশেষ', ''), 'hrNightRec': ('মধ্যরাতের রেকর্ডিং', ''), 'hrCurse': ('অভিশাপের চিঠি', ''),
    'noir': ('রঙিন নোয়ার', ''), 'crimson': ('টকটকে লাল সংকেত', ''), 'caution': ('সতর্কতা', ''), 'magenta': ('ম্যাজেন্টা পপ', ''),
    'paper': ('কাগজ ও কালি', ''), 'hud': ('ডার্ক HUD', ''), 'mint': ('মিন্ট টার্মিনাল', ''), 'specimen': ('টাইপ স্পেসিমেন', ''),
    'transit': ('ট্রানজিট', ''), 'blueprint': ('ব্লুপ্রিন্ট', ''), 'rouge': ('লাল গ্রেডিয়েন্ট', ''), 'mono': ('মনো RGB', ''),
    'sakura': ('সাকুরা', ''), 'ocean': ('গভীর সমুদ্র', ''), 'sunset': ('সূর্যাস্ত গ্রেডিয়েন্ট', ''), 'forest': ('বনের নোট', ''),
    'vapor': ('ভেপারওয়েভ', ''), 'newsprint': ('নিউজপ্রিন্ট', ''), 'synth80': ('৮০-র দশকের সিন্থ', ''), 'kraft': ('ক্রাফট কাগজ', ''),
    'candy': ('ক্যান্ডি', ''), 'acid': ('অ্যাসিড', ''), 'sumi': ('কালি ও লাল', ''), 'gold': ('সোনালি রাত', ''),
}
MOODS = {'horror': 'হরর', 'glitch': 'গ্লিচ', 'calm': 'শান্ত', 'pop': 'পপ', 'graphic': 'গ্রাফিক', 'editorial': 'এডিটোরিয়াল',
         'emotional': 'আবেগী', 'chaos': 'বিশৃঙ্খল'}
SAMPLE = ('আমি আজও মনে রাখি/ভোরের সেই আলো\nমিলিয়ে যাওয়া কণ্ঠস্বর দূরে বাজে\nএই যে, এখনও কি সময় আছে?\n'
          'স্বচ্ছ হয়েই শেষ হওয়া যাবে না!')
TITLE = 'LYRAVOX — লিরিক মোশন ভিডিও স্টুডিও'
DESCRIPTION = 'ব্রাউজারেই লিরিক্সকে অ্যানিমেটেড লিরিক মোশন ভিডিওতে বদলে MP4 এক্সপোর্ট করুন। বাংলা ও ইংরেজি সমর্থিত, কোনো API key লাগে না।'
