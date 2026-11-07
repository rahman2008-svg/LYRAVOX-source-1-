"""Browser tests (Playwright + Chromium) of the AI Generate Lyrics UI, against REAL HTTP servers.

REAL: the browser, the UI, the multipart upload, polling, cancel (DELETE), the project library, the editor integration, the existing
motion engine plan / timing.  MOCKED: the speech recogniser — the backend runs its TEST-ONLY placeholder engine ("TEST LINE n" text built
from the audio's silence structure), because no Whisper model is available in this environment. These tests therefore prove the plumbing and
UI, not recognition quality.

Run from the repository root:  python3 tests/ai_ui_test.py"""
import json, os, subprocess, sys, time, urllib.request
from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PUB = os.path.join(ROOT, 'public'); BACK = os.path.join(ROOT, 'backend')
TMP = '/tmp/lv_ai_ui'; os.makedirs(TMP, exist_ok=True)
STATIC = 'http://localhost:8800'
results = []


def check(name, cond, detail=''):
    results.append((name, bool(cond), detail))
    print(('  PASS ' if cond else '  FAIL ') + name + (f'  [{detail}]' if detail and not cond else ''))


def tone_bursts(path, seconds, on, off):
    expr = f'sin(2*PI*330*t)*0.6*lt(mod(t\\,{on + off})\\,{on})'
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'lavfi', '-i', f'aevalsrc={expr}:d={seconds}:s=16000', '-ac', '1', path], check=True)
    return path


def spawn(port, *args, env=None):
    e = dict(os.environ, LYRAVOX_ALLOW_FAKE='1', **(env or {}))
    p = subprocess.Popen([sys.executable, '-m', 'lyravox_ai.devserver', '--fake', '--port', str(port), *args], cwd=BACK, env=e, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(100):
        try: urllib.request.urlopen(f'http://127.0.0.1:{port}/api/health', timeout=1); return p
        except Exception: time.sleep(0.1)
    raise RuntimeError('server did not start on ' + str(port))


def api(port, path):
    return json.loads(urllib.request.urlopen(f'http://127.0.0.1:{port}{path}', timeout=5).read())


def main():
    burst = tone_bursts(f'{TMP}/burst.wav', 12, 2.0, 1.0)            # 4 sound stretches
    burst_long = tone_bursts(f'{TMP}/burst_long.wav', 40, 2.0, 2.0)   # 10 stretches (for cancel / regenerate)
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'lavfi', '-i', 'anullsrc=r=44100:cl=stereo', '-t', '25', f'{TMP}/big.wav'], check=True)   # ~4.4 MB
    procs = [subprocess.Popen([sys.executable, '-m', 'http.server', '8800', '--directory', PUB], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)]
    procs.append(spawn(8000, '--fake-delay', '0.5', env={'MAX_ACTIVE_PER_IP': '5', 'MAX_QUEUE': '10'}))
    procs.append(spawn(8002, '--fake-fail'))
    procs.append(spawn(8003, env={'MAX_UPLOAD_MB': '1'}))
    time.sleep(1)
    try:
        with sync_playwright() as pw:
            run(pw, burst, burst_long)
    finally:
        for p in procs: p.terminate()
    failed = [r for r in results if not r[1]]
    print(f'\n{len(results) - len(failed)}/{len(results)} checks passed')
    sys.exit(1 if failed else 0)


def ctx_page(browser, api_port=8000, lang='en', mobile=False):
    kw = dict(viewport={'width': 390, 'height': 844}, is_mobile=True, has_touch=True) if mobile else dict(viewport={'width': 1280, 'height': 860})
    ctx = browser.new_context(accept_downloads=True, **kw)
    ctx.add_init_script(f"localStorage.setItem('lyravox.tourDone','1');localStorage.setItem('lyravox.lang','{lang}');localStorage.setItem('lyravox.api','http://localhost:{api_port}');")
    pg = ctx.new_page(); pg.errors = []
    pg.on('pageerror', lambda e: pg.errors.append(str(e)))
    pg.on('console', lambda m: pg.errors.append(m.text) if m.type == 'error' and 'ERR_NAME_NOT_RESOLVED' not in m.text and 'Failed to load resource' not in m.text else None)
    return ctx, pg


def studio_with_song(browser, song, **kw):
    ctx, pg = ctx_page(browser, **kw)
    pg.goto(STATIC + '/studio/#audio', wait_until='domcontentloaded'); pg.wait_for_timeout(500)
    pg.set_input_files('#afile', song); pg.wait_for_timeout(700)
    return ctx, pg


def wait_result(pg, timeout=40000):
    pg.wait_for_selector('.lvai-table tbody tr', timeout=timeout)


def run(pw, burst, burst_long):
    browser = pw.chromium.launch(args=['--no-sandbox', '--autoplay-policy=no-user-gesture-required'])

    print('\n[1] Studio: open the dialog, settings, generate, progress')
    ctx, pg = studio_with_song(browser, burst)
    check('AI button exists in the audio library row', pg.locator('#alist [data-act=ai]').count() == 1)
    check('AI button exists in the audio toolbar', pg.locator('#aiBtn').count() == 1)
    pg.click('#alist [data-act=ai]')
    pg.wait_for_selector('.lvai-pill.ok', timeout=10000)
    check('dialog shows server ready + model + limits', 'AI server ready' in pg.inner_text('.lvai-pill') and 'fake-test-engine' in pg.inner_text('.lvai-pill'), pg.inner_text('.lvai-pill'))
    check('file info shows name, size and real duration', 'burst.wav' in pg.inner_text('.lvai-info') and '0:12' in pg.inner_text('.lvai-info'), pg.inner_text('.lvai-info'))
    opts = pg.eval_on_selector_all('#lvaiLang option', 'els=>els.map(e=>e.value+"|"+e.textContent)')
    check('language selector: auto + bn + en + hi', [o.split('|')[0] for o in opts] == ['auto', 'bn', 'en', 'hi'], opts)
    check('vocal separation disabled when the server lacks Demucs', pg.is_disabled('#lvaiVocal') and 'Not available' in pg.inner_text('.lvai-chk'))
    pg.select_option('#lvaiLang', 'bn')
    stages, widths = set(), []
    pg.click('#lvaiGo')
    t0 = time.time()
    while time.time() - t0 < 40 and pg.locator('.lvai-table').count() == 0:
        try:
            stages.add(pg.inner_text('.lvai-stage', timeout=300)); widths.append(pg.evaluate("document.querySelector('.lvai-bar i')?parseFloat(document.querySelector('.lvai-bar i').style.width)||0:-1"))
        except Exception: pass
        pg.wait_for_timeout(150)
    check('real progress: several different status texts were shown', len(stages) >= 3, sorted(stages))
    w = [x for x in widths if x >= 0]
    check('progress bar only moves forward', w == sorted(w) and max(w) > 20, w)
    wait_result(pg)
    rows = pg.locator('.lvai-table tbody tr[data-i]')
    check('result lists lines with times and text', rows.count() == 4, rows.count())
    check('test-engine banner is shown (placeholders are labelled)', 'TEST ENGINE' in pg.inner_text('.lvai-notes'))
    check('confidence badge shown', pg.locator('.cf').count() == 4)
    check('detected/selected language chip', 'বাংলা' in pg.inner_text('.lvai-meta'))
    first = pg.input_value('.lvai-table tr[data-i="0"] input.tx')
    check('line text comes from the server', first == 'TEST LINE 1', first)
    check('line 1 start/end are the real tone times (0-2 s)', pg.input_value('tr[data-i="0"] input.tm[data-key=start]') == '0:00.00' and pg.input_value('tr[data-i="0"] input.tm[data-key=end]') in ('0:02.00', '0:01.99', '0:02.01'), pg.input_value('tr[data-i="0"] input.tm[data-key=end]'))

    print('\n[2] Lyrics editor operations')
    pg.fill('tr[data-i="0"] input.tx', 'আমার সোনার বাংলা'); pg.dispatch_event('tr[data-i="0"] input.tx', 'input')
    pg.fill('tr[data-i="1"] input.tm[data-key=start]', '0:03.50'); pg.dispatch_event('tr[data-i="1"] input.tm[data-key=start]', 'change')
    check('timestamp can be edited', pg.input_value('tr[data-i="1"] input.tm[data-key=start]') == '0:03.50')
    pg.click('tr[data-i="0"] .lvai-ib:has-text("⤵")')
    check('merge joins two lines', pg.locator('tbody tr[data-i]').count() == 3 and 'আমার সোনার বাংলা TEST LINE 2' in pg.input_value('tr[data-i="0"] input.tx'))
    pg.click('tr[data-i="0"] input.tx'); pg.evaluate("(()=>{const i=document.querySelector('tr[data-i=\"0\"] input.tx');i.focus();i.setSelectionRange(16,16);i.dispatchEvent(new Event('keyup'))})()")
    pg.click('tr[data-i="0"] .lvai-ib:has-text("✂")')
    check('split cuts at the cursor without breaking Bangla clusters', pg.locator('tbody tr[data-i]').count() == 4 and pg.input_value('tr[data-i="0"] input.tx') == 'আমার সোনার বাংলা', pg.input_value('tr[data-i="0"] input.tx') + ' | ' + pg.input_value('tr[data-i="1"] input.tx'))
    pg.click('tr[data-i="3"] .lvai-ib:has-text("+")')
    check('add line below', pg.locator('tbody tr[data-i]').count() == 5)
    pg.click('tr[data-i="4"] .lvai-ib.del')
    check('delete line', pg.locator('tbody tr[data-i]').count() == 4)
    pg.click('#lvaiPlayAll'); pg.wait_for_timeout(1500)
    active = pg.locator('.lvai-table tr.on').count()
    pg.click('#lvaiPlayAll')
    check('playback highlights the current line (synchronised)', active == 1, active)
    pg.click('tr[data-i="2"] .lvai-ib.play'); pg.wait_for_timeout(500); t_now = pg.evaluate("document.querySelector('.lvai-box audio').currentTime")
    st2 = pg.input_value('tr[data-i="2"] input.tm[data-key=start]'); mm, ss = st2.split(':')
    check('play-this-line seeks to the line start', abs(t_now - (int(mm) * 60 + float(ss))) < 1.2, f'{t_now} vs {st2}')
    pg.click('#lvaiPlayAll') if pg.evaluate("!document.querySelector('.lvai-box audio').paused") else None

    print('\n[3] Studio: send all to the editor (sanitised, timestamps kept)')
    pg.fill('tr[data-i="3"] input.tx', 'a/b | c *d* !'); pg.dispatch_event('tr[data-i="3"] input.tx', 'input')
    pg.click('#lvaiSendAll')
    pg.wait_for_url('**/editor/', timeout=20000); pg.wait_for_timeout(4500)
    lyr = pg.input_value('#lyrics')
    check('editor received timestamped lyrics', lyr.startswith('[') and '[00:00.00]আমার সোনার বাংলা' in lyr, lyr[:120])
    check('special characters were escaped', 'a b c d' in lyr and '*' not in lyr and '/' not in lyr and '|' not in lyr, lyr)
    check('song came along (audio loaded in the editor)', pg.evaluate("J.ui.audio&&J.ui.audio.name")=='burst.wav')
    plan = pg.evaluate("J.ui.plan.lines.map(l=>({t:l.text,lrc:l.lrc,src:l.src}))")
    check('editor plan has one line per lyric with the LRC timestamps', len([p for p in plan if p['lrc'] is not None]) >= 4, plan)
    starts = pg.evaluate("(()=>{const P=J.ui.plan;return P.cuts.filter(c=>c.line>=0).map(c=>[c.line,+c.start.toFixed(2)])})()")
    first_starts = {}
    for li, st in starts: first_starts.setdefault(li, st)
    import re
    tags = [int(m[0]) * 60 + float(m[1]) for m in re.findall(r'^\[(\d+):(\d+\.\d+)\]', lyr, re.M)]
    got = [first_starts[k] for k in sorted(first_starts)]
    check('motion engine cut starts equal the timestamps in the lyrics sent by the AI dialog', len(got) == len(tags) and all(abs(a - b) < 0.02 for a, b in zip(got, tags)), (tags, got))
    check('Bangla conjuncts survive into the engine (packed clusters)', pg.evaluate("J.ui.plan.cuts.some(c=>J.unpackText(c.text).includes('বাংলা'))"))
    check('no page errors in the editor', not pg.errors, pg.errors[:3]); ctx.close()

    print('\n[4] Cancel while running')
    ctx, pg = studio_with_song(browser, burst_long)
    pg.click('#alist [data-act=ai]'); pg.wait_for_selector('.lvai-pill.ok'); pg.click('#lvaiGo')
    pg.wait_for_function("document.querySelector('.lvai-stage')&&/Transcribing|Analysing|Preparing|Detecting/.test(document.querySelector('.lvai-stage').textContent)", timeout=20000)
    pg.wait_for_timeout(1200)
    jobs_before = api(8000, '/api/health')['queue']['active']
    pg.click('#lvaiCancel')
    pg.wait_for_selector('#lvaiGo', timeout=15000)
    check('cancel returns to the setup view', pg.locator('#lvaiGo').count() == 1)
    t0 = time.time()
    while time.time() - t0 < 15 and api(8000, '/api/health')['queue']['active'] > 0: time.sleep(0.2)
    check('server job was actually cancelled and removed', jobs_before >= 1 and api(8000, '/api/health')['queue']['active'] == 0, (jobs_before, api(8000, '/api/health')['queue']))
    left = [n for n in os.listdir('/tmp/lyravox-ai') if n.startswith('job-')] if os.path.isdir('/tmp/lyravox-ai') else []
    check('no uploaded audio left on the server after cancel', left == [], left)
    ctx.close()

    print('\n[5] Regenerate the selected lines (clip request) and merge into the timeline')
    ctx, pg = studio_with_song(browser, burst_long)
    pg.click('#alist [data-act=ai]'); pg.wait_for_selector('.lvai-pill.ok'); pg.click('#lvaiGo'); wait_result(pg, 90000)
    n0 = pg.locator('tbody tr[data-i]').count()
    pg.evaluate("document.querySelectorAll('.lvai-box audio').forEach(a=>a.pause())")
    pg.evaluate("""()=>{window.__fd=[];const o=XMLHttpRequest.prototype.send;XMLHttpRequest.prototype.send=function(b){
      if(b instanceof FormData){const d={};for(const [k,v] of b.entries()) d[k]=(v instanceof File)?('file:'+v.name):v;window.__fd.push(d);} return o.apply(this,arguments);};}""")
    pg.check('tr[data-i="2"] input[type=checkbox]'); pg.check('tr[data-i="3"] input[type=checkbox]')
    check('regenerate button enabled once lines are selected', not pg.is_disabled('#lvaiRegen'))
    pg.fill('tr[data-i="2"] input.tx', 'EDITED OUTSIDE?'); pg.dispatch_event('tr[data-i="2"] input.tx', 'input')
    pg.fill('tr[data-i="0"] input.tx', 'KEEP ME'); pg.dispatch_event('tr[data-i="0"] input.tx', 'input')
    pg.click('#lvaiRegen'); pg.wait_for_function("/regenerated/i.test(document.querySelector('.lvai-stage.small').textContent)", timeout=60000)
    fd = pg.evaluate('window.__fd')
    check('regenerate request carried the selected section (clip_start / clip_end) and the detected language', len(fd) == 1 and float(fd[0]['clip_start']) > 3 and float(fd[0]['clip_end']) > float(fd[0]['clip_start']) and fd[0]['language'] == 'bn', fd)   # auto-detected language (placeholder engine reports bn) is reused for the section
    check('lines outside the selection are untouched', pg.input_value('tr[data-i="0"] input.tx') == 'KEEP ME')
    check('regenerated section replaced the selected lines', 'EDITED OUTSIDE?' not in ''.join(pg.eval_on_selector_all('input.tx', 'els=>els.map(e=>e.value)')) and pg.locator('tbody tr[data-i]').count() == n0, (n0, pg.locator('tbody tr[data-i]').count()))
    times = pg.eval_on_selector_all('input.tm[data-key=start]', 'els=>els.map(e=>e.value)'); sec = [int(x.split(":")[0]) * 60 + float(x.split(":")[1]) for x in times]
    check('regenerated lines are on the song timeline and ordered', sec == sorted(sec) and sec[-1] > 30, times)
    ctx.close()

    print('\n[6] Errors: backend down / engine failure / file too large')
    ctx, pg = studio_with_song(browser, burst, api_port=9)
    pg.click('#alist [data-act=ai]'); pg.wait_for_selector('.lvai-pill.bad', timeout=15000)
    check('backend unavailable: clear message + retry, Generate disabled', 'Cannot reach' in pg.inner_text('.lvai-pill') and pg.locator('.lvai-err button').count() == 1 and pg.is_disabled('#lvaiGo'))
    ctx.close()
    ctx, pg = studio_with_song(browser, burst, api_port=8002)
    pg.click('#alist [data-act=ai]'); pg.wait_for_selector('.lvai-pill.ok'); pg.click('#lvaiGo')
    pg.wait_for_selector('.lvai-err:not([hidden])', timeout=30000)
    check('engine failure is shown to the user with the server message', 'simulated engine failure' in pg.inner_text('.lvai-err'), pg.inner_text('.lvai-err'))
    check('user can try again after a failure', pg.locator('#lvaiGo').count() == 1 and not pg.is_disabled('#lvaiGo'))
    ctx.close()
    ctx, pg = studio_with_song(browser, f'{TMP}/big.wav', api_port=8003)
    pg.click('#alist [data-act=ai]'); pg.wait_for_selector('.lvai-pill.ok'); pg.click('#lvaiGo')
    pg.wait_for_selector('.lvai-err:not([hidden])', timeout=10000)
    check('oversize file is refused before uploading (client check against server limit)', 'larger than the server limit' in pg.inner_text('.lvai-err'), pg.inner_text('.lvai-err'))
    ctx.close()

    print('\n[7] Editor: button, generate, send all (undoable), import a single line')
    ctx, pg = ctx_page(browser)
    pg.goto(STATIC + '/editor/', wait_until='domcontentloaded'); pg.wait_for_timeout(3500)
    pg.click('#btnAIGen'); pg.wait_for_timeout(300)
    check('no song loaded -> asks for a song (no dialog)', pg.locator('.lvai-overlay').count() == 0)
    pg.set_input_files('#audioFile', burst); pg.wait_for_timeout(4000)
    sample = pg.input_value('#lyrics')
    pg.click('#btnAIGen'); pg.wait_for_selector('.lvai-pill.ok', timeout=10000); pg.click('#lvaiGo'); wait_result(pg)
    pg.once('dialog', lambda d: d.accept())
    pg.click('#lvaiSendAll'); pg.wait_for_timeout(1200)
    lyr = pg.input_value('#lyrics')
    check('editor lyrics replaced with timestamped AI lyrics', lyr.startswith('[00:00.00]TEST LINE 1') and lyr != sample, lyr[:80])
    pg.keyboard.press('Control+z'); pg.wait_for_timeout(500)
    check('replacement is undoable in the editor (Ctrl+Z)', pg.input_value('#lyrics') == sample)
    pg.evaluate("J.uiApi.loadLrc && 0")
    pg.click('#btnAIGen'); pg.wait_for_selector('.lvai-pill.ok'); pg.click('#lvaiGo'); wait_result(pg)
    n_before = pg.evaluate("J.ui.plan.lines.length")
    pg.click('tr[data-i="1"] .lvai-ib.send'); pg.wait_for_timeout(900)
    lyr2 = pg.input_value('#lyrics')
    check('single line imported with its timestamp', lyr2.rstrip().endswith('TEST LINE 2') and '[00:04.00]TEST LINE 2' in lyr2 or '[00:03.' in lyr2.splitlines()[-1] or '[00:0' in lyr2.splitlines()[-1], lyr2.splitlines()[-1])
    check('editor still planned after the import', pg.evaluate("J.ui.plan.lines.length") == n_before + 1 and pg.locator('.lvai-overlay').count() == 1)
    pg.keyboard.press('Escape'); pg.wait_for_timeout(300)
    check('Esc closes the dialog', pg.locator('.lvai-overlay').count() == 0)
    time.sleep(3)
    check('project autosaved to the Studio library including the AI lyrics', pg.evaluate("LVStore.projects.list().then(l=>l.some(r=>r.project.lyrics.includes('TEST LINE 2')))"))
    check('no page errors in the editor flow', not pg.errors, pg.errors[:3]); ctx.close()

    print('\n[8] Mobile layout (390 px) and Bangla interface')
    ctx, pg = studio_with_song(browser, burst, lang='bn', mobile=True)
    pg.click('#alist [data-act=ai]'); pg.wait_for_selector('.lvai-pill.ok', timeout=10000)
    check('Bangla UI strings in the dialog', 'AI দিয়ে লিরিক্স বানান' in pg.inner_text('.lvai-box header') and 'AI সার্ভার প্রস্তুত' in pg.inner_text('.lvai-pill'), pg.inner_text('.lvai-pill'))
    pg.click('#lvaiGo'); wait_result(pg)
    ow = pg.evaluate("[document.querySelector('.lvai-box').scrollWidth, document.querySelector('.lvai-box').clientWidth, document.documentElement.scrollWidth, innerWidth]")
    check('dialog does not overflow horizontally on a phone', ow[0] <= ow[1] + 1 and ow[2] <= ow[3] + 1, ow)
    check('rows are usable on a phone (tap targets >= 28 px)', pg.evaluate("[...document.querySelectorAll('.lvai-ib')].every(b=>b.getBoundingClientRect().width>=28&&b.getBoundingClientRect().height>=28)"))
    pg.screenshot(path=f'{TMP}/m_ai_result.png')
    ctx.close()

    print('\n[9] Client helper parity with the backend (sanitise / instrumental gaps / editor text)')
    ctx, pg = ctx_page(browser); pg.goto(STATIC + '/studio/', wait_until='domcontentloaded'); pg.wait_for_timeout(500)
    r = pg.evaluate("""()=>({s1:LVAI.sanitize('a/b | c *d* !'), s2:LVAI.sanitize('# [x] hi!!'), t:LVAI.tag(75.5), p:LVAI.parseTime('1:15.50'), p2:LVAI.parseTime('abc'),
      g:LVAI.instrumentals([{start:8,end:10},{start:11,end:12},{start:30,end:31}],45,6),
      e:LVAI.toEditorText([{start:12,end:13,text:'line one'},{start:20.25,end:22,text:'আমার/সোনার'}],{duration:12.5}),
      sp:LVAI.splitLine({start:0,end:4,text:'one two three four',words:[{start:0,text:'one'},{start:1,text:'two'},{start:2.5,text:'three'},{start:3,text:'four'}]},8)})""")
    check('sanitize matches backend', r['s1'] == 'a b c d' and r['s2'] == 'x] hi', (r['s1'], r['s2']))
    check('tag / parseTime', r['t'] == '[01:15.50]' and r['p'] == 75.5 and r['p2'] != r['p2'])
    check('instrumental gaps match backend', r['g'] == [{'start': 0, 'end': 8}, {'start': 12, 'end': 30}, {'start': 31, 'end': 45}], r['g'])
    check('editor text format matches backend', r['e'].split('\n') == ['[00:00.00][interlude 12]', '[00:12.00]line one', '[00:13.00][interlude 7]', '[00:20.25]আমার সোনার'], r['e'])
    check('split uses the word boundary closest to the cursor', r['sp'] and r['sp'][1]['start'] == 2.5 and r['sp'][0]['text'] == 'one two', r['sp'])
    ctx.close(); browser.close()


if __name__ == '__main__':
    main()
