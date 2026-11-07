"""LYRAVOX build — produces the deployable static site in public/.
usage: python3 build.py            -> public/ (landing, studio, about, legal pages, editor editions, sitemap, robots)
       SITE_URL=https://example.com python3 build.py   -> canonical URLs / sitemap use that address
       python3 build.py --dev      -> also dev/www/lyravox.js + dev/www/test.html for the engine test tools
The editor is built from the original single-file pipeline (src/*.js + app/body.html + app/style.css + vendor/mp4-muxer),
one self-contained index.html per language edition under public/editor/ (English at /editor/, বাংলা at /editor/bn/, …)."""
import glob, os, shutil, sys, datetime
from app.english import localize_body, localize_js
from app import i18n, i18n_bn
ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)
read = lambda p: open(p, encoding='utf-8').read()
VERSION = read('VERSION').strip()
PUBLIC = 'public'
SITE = i18n.SITE
sources = sorted(glob.glob('src/*.js'))
js = '\n'.join(read(f) for f in sources)
mux = '/*! mp4-muxer v5.2.2 | MIT License | (c) 2023 Vanilagy | see THIRD_PARTY_NOTICES.md */\n' + read('vendor/mp4-muxer.min.js')
store = read('app/store.js')
aigen = read('app/aigen.js')
aigen_css = read('app/aigen.css')
API_URL = os.environ.get('LYRAVOX_API_URL', '').strip().rstrip('/')       # AI backend address baked into the pages (users can override it in the AI dialog)
LOGO = read('app/logo.svg.txt')
bad = i18n_bn.check()
if bad: raise SystemExit('Bangla glossary placeholder mismatch: %r' % (bad[:3],))

SPLASH = ('<div id="lvSplash" class="lv-splash" role="status" aria-label="LYRAVOX">' + LOGO.replace('id="lvg"', 'id="lvs"').replace('url(#lvg)', 'url(#lvs)') +
          '<b>LYRAVOX</b><i></i></div>')
DESC = {
    'en': 'Turn lyrics into animated lyric motion videos in your browser. 860 motion components, beat detection, tap-to-sync timeline, MP4 and transparent PNG export. No account, no upload.',
    'ja': 'LYRAVOX — 歌詞からリリックモーション動画をブラウザで作成し、MP4に書き出します。',
}
TITLE = {'en': 'LYRAVOX Editor — Lyric Motion Video Studio', 'ja': 'LYRAVOX エディター — リリックモーション動画スタジオ'}
FONT_LINKS = {'bn': '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Sans+Bengali:wght@400;500;700&amp;family=Hind+Siliguri:wght@400;500;600&amp;display=swap">'}

def build(lang):
    english = lang == 'en'
    local = lang in i18n.MODULES
    m = i18n.module(lang) if local else None
    title = TITLE['en'] if english else (m.TITLE if local else TITLE['ja'])
    description = DESC['en'] if english else (m.DESCRIPTION if local else DESC['ja'])
    folder = dict((c, f) for c, f, _, _ in i18n.EDITIONS)[lang]
    canonical = i18n.BASE + (folder + '/' if folder else '')
    language_nav = i18n.nav(lang)
    body = read('app/body.html').replace('@VERSION@', VERSION).replace('    <div class="acts">', '    ' + language_nav + '\n    <div class="acts">', 1)
    if english: body = localize_body(body)
    elif local: body = i18n.localize_body(lang, body)
    if english: script = '\n'.join(localize_js(read(f), f) for f in sources)
    elif local: script = '\n'.join(i18n.localize_js(lang, read(f), f) for f in sources)
    else: script = js
    script = script.replace('@VERSION@', VERSION)
    if english or local:
        marker = '/* ============================================================\n   LYRAVOX — editor UI'
        if marker not in script: raise ValueError('Could not find browser UI entry point')
        inject = read('app/english.js') + ('\n' + i18n.labels_js(lang) if local else '')
        script = script.replace(marker, inject + '\n' + marker, 1)
    alternates = '\n'.join(f'<link rel="alternate" hreflang="{hl}" href="{i18n.BASE}{f + "/" if f else ""}">' for c, f, hl, _ in i18n.EDITIONS)
    html_lang = dict((c, hl) for c, _, hl, _ in i18n.EDITIONS)[lang]
    up = '../' * (2 if folder else 1)                       # from public/editor[/xx]/ back to the site root (relative: works under any path)
    html = f'''<!doctype html>
<html lang="{html_lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{title}</title>
<meta name="description" content="{description}">
<meta name="theme-color" content="#060913">
<meta name="author" content="Prince AR Abdur Rahman">
<meta name="application-name" content="LYRAVOX">
<link rel="canonical" href="{canonical}">
{alternates}
<link rel="alternate" hreflang="x-default" href="{i18n.BASE}">
<link rel="icon" href="{up}favicon.svg" type="image/svg+xml">
<link rel="icon" href="{up}favicon-32.png" sizes="32x32" type="image/png">
<link rel="apple-touch-icon" href="{up}apple-touch-icon.png">
<link rel="manifest" href="{up}manifest.webmanifest">
<meta property="og:type" content="website">
<meta property="og:site_name" content="LYRAVOX">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{description}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{SITE}og-image.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{title}">
<meta name="twitter:description" content="{description}">
<meta name="twitter:image" content="{SITE}og-image.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<meta name="lyravox-api" content="{API_URL}">
{FONT_LINKS.get(lang, '')}
<style>
{read('app/style.css')}
{aigen_css}
</style>
</head>
<body>
{SPLASH}
<noscript><p style="padding:24px;color:#e8f1ff">LYRAVOX needs JavaScript to run the editor. Everything runs inside your browser; nothing is uploaded.</p></noscript>
{body}
<script src="{up}config.js"></script>
<script>
{mux}
</script>
<script>
{store}
</script>
<script>
{aigen}
</script>
<script>
{script}
</script>
</body>
</html>
'''
    target = os.path.join(PUBLIC, 'editor', folder, 'index.html') if folder else os.path.join(PUBLIC, 'editor', 'index.html')
    os.makedirs(os.path.dirname(target), exist_ok=True)
    open(target, 'w', encoding='utf-8').write(html)
    print(target, len(html), 'bytes')

if os.path.isdir(PUBLIC):
    for name in os.listdir(PUBLIC):
        p = os.path.join(PUBLIC, name)
        shutil.rmtree(p) if os.path.isdir(p) else os.remove(p)
os.makedirs(PUBLIC, exist_ok=True)
for code, _, _, _ in i18n.EDITIONS:
    build(code)

# the rest of the site: landing, studio, about, legal pages, assets, sitemap, robots
sys.path.insert(0, os.path.join(ROOT, 'site'))
import site_build
site_build.build(PUBLIC, VERSION, SITE, [(f, hl, name) for _, f, hl, name in i18n.EDITIONS])

if '--dev' in sys.argv:
    os.makedirs('dev/www', exist_ok=True)
    open('dev/www/lyravox.js', 'w', encoding='utf-8').write(js)
    open('dev/www/test.html', 'w', encoding='utf-8').write(read('dev/test.html').replace('jizura.js', 'lyravox.js'))
    print('dev/www ready: cd dev/www && python3 -m http.server 8765')
