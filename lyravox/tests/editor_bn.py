import asyncio, json, sys
from playwright.async_api import async_playwright
URL = sys.argv[1] if len(sys.argv)>1 else 'http://localhost:8800/editor/bn/'
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--no-sandbox"])
        ctx = await b.new_context(viewport={'width':1280,'height':800})
        pg = await ctx.new_page()
        errs=[]
        pg.on('pageerror', lambda e: errs.append('PAGEERR '+str(e)))
        pg.on('console', lambda m: errs.append('CONSOLE '+m.type+' '+m.text[:200]) if m.type in ('error',) else None)
        await pg.goto(URL, wait_until='domcontentloaded')
        await pg.wait_for_timeout(4000)
        info = await pg.evaluate("""()=>({lang:document.documentElement.lang, title:document.title, hasJ:typeof J, ui:!!(J&&J.ui&&J.ui.project), splash:!!document.getElementById('lvSplash'), lyrics:document.getElementById('lyrics').value.slice(0,60), planLang:J.ui.plan&&J.ui.plan.lang, cuts:J.ui.plan&&J.ui.plan.cuts.length, brand:document.querySelector('.brand .word').textContent, bnOpt:!!document.querySelector('#lyricLang option[value=bn]')})""")
        print(json.dumps(info,ensure_ascii=False))
        lyr = "আমার সোনার বাংলা, আমি তোমায় ভালোবাসি\nচিরদিন তোমার আকাশ, তোমার বাতাস\nক্ষণিকের স্বপ্ন স্ট্রিট দৃষ্টি"
        await pg.fill('#lyrics', lyr)
        await pg.wait_for_timeout(4000)
        r = await pg.evaluate("""()=>{const p=J.ui.plan;return {lang:p.lang, cuts:p.cuts.map(c=>[J.unpackText(c.text), [...c.text].length]).slice(0,10), lines:p.lines.map(l=>l.text), faces:J.faceOf('gothic_bold').family}}""")
        print(json.dumps(r,ensure_ascii=False))
        await pg.evaluate("J.uiApi.seek(J.ui.plan.cuts.find(c=>c.line>=0).start+0.9)")
        await pg.wait_for_timeout(800)
        await pg.screenshot(path='tests/bn_editor.png')
        await pg.locator('#view').screenshot(path='tests/bn_view.png')
        print('\n'.join(errs[:15]) or 'no console errors')
        await b.close()
asyncio.run(main())
