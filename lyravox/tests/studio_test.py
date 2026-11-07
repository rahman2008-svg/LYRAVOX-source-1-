import asyncio, json
from playwright.async_api import async_playwright
B='http://localhost:8800'
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--no-sandbox"])
        ctx = await b.new_context(viewport={'width':1280,'height':800}, accept_downloads=True)
        await ctx.add_init_script("localStorage.setItem('lyravox.tourDone','1')")
        pg = await ctx.new_page(); errs=[]
        pg.on('pageerror', lambda e: errs.append('PAGEERR '+str(e)))
        pg.on('console', lambda m: errs.append('CONSOLE '+m.text[:150]) if m.type=='error' and 'ERR_NAME_NOT_RESOLVED' not in m.text else None)
        # landing
        await pg.goto(B+'/', wait_until='domcontentloaded'); await pg.wait_for_timeout(800)
        print('landing title:', await pg.title(), '| editor href:', await pg.get_attribute('a[data-editor]','href'))
        await pg.screenshot(path='tests/landing_en.png')
        await pg.click('.lang button[data-l=bn]'); await pg.wait_for_timeout(400)
        print('bn title:', await pg.title(), '| editor href:', await pg.get_attribute('a[data-editor]','href'))
        await pg.screenshot(path='tests/landing_bn.png')
        # studio: lyrics studio -> open in editor
        await pg.goto(B+'/studio/#lyrics', wait_until='domcontentloaded'); await pg.wait_for_timeout(800)
        await pg.fill('#ltitle','আমার গান'); await pg.fill('#lyr',"আমার সোনার বাংলা\nআমি তোমায় ভালোবাসি\nচিরদিন তোমার আকাশ")
        await pg.click('#lstamp'); print('stamped:', (await pg.input_value('#lyr')).split('\n')[:2])
        await pg.click('#lstrip'); await pg.click('#lsave')
        await pg.click('#lopen'); await pg.wait_for_url('**/editor/bn/', timeout=15000); await pg.wait_for_timeout(3500)
        r = await pg.evaluate("()=>({lyr:document.getElementById('lyrics').value.slice(0,40), title:document.getElementById('songTitle').value, lang:J.ui.plan.lang})")
        print('EDITOR got:', json.dumps(r,ensure_ascii=False))
        await pg.wait_for_timeout(3000)  # autosave
        # back to studio
        await pg.click('.lv-studio-link'); await pg.wait_for_url('**/studio/', timeout=10000); await pg.wait_for_timeout(1000)
        n = await pg.evaluate("()=>[...document.querySelectorAll('.proj h4')].map(e=>e.textContent)")
        print('PROJECT CARDS:', n)
        await pg.screenshot(path='tests/studio_projects.png')
        # export project, import it back
        async with pg.expect_download() as d: await pg.click('.proj [data-act=exp]')
        dl=await d.value; await dl.save_as('tests/proj.json'); print('exported', dl.suggested_filename)
        await pg.set_input_files('#pimport','tests/proj.json'); await pg.wait_for_timeout(800)
        print('after import cards:', await pg.evaluate("()=>document.querySelectorAll('.proj').length"))
        # duplicate + delete
        await pg.click('.proj [data-act=dup]'); await pg.wait_for_timeout(500)
        pg.on('dialog', lambda dlg: asyncio.ensure_future(dlg.accept()))
        await pg.click('.proj [data-act=del]'); await pg.wait_for_timeout(500)
        print('after dup+del:', await pg.evaluate("()=>document.querySelectorAll('.proj').length"))
        # audio library
        await pg.click('#tab-audio'); await pg.set_input_files('#afile','tests/click120.wav'); await pg.wait_for_timeout(800)
        print('audio rows:', await pg.evaluate("()=>[...document.querySelectorAll('#alist .nm')].map(e=>e.textContent)"))
        # open project with audio from library: use song
        await pg.click('#alist [data-act=use]'); await pg.wait_for_url('**/editor/bn/', timeout=15000); await pg.wait_for_timeout(5000)
        r = await pg.evaluate("()=>({audio:J.ui.audio&&J.ui.audio.name,bpm:J.ui.audio&&J.ui.audio.bpm})"); print('EDITOR AUDIO FROM LIBRARY:', r)
        # export history tab
        await pg.goto(B+'/studio/#exports', wait_until='domcontentloaded'); await pg.wait_for_timeout(800)
        print('exports empty visible:', await pg.is_visible('#eempty'))
        # mobile
        m = await b.new_context(viewport={'width':390,'height':844}, is_mobile=True, has_touch=True, device_scale_factor=2, user_agent='Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 Chrome/120 Mobile Safari/537.36')
        await m.add_init_script("localStorage.setItem('lyravox.tourDone','1');localStorage.setItem('lyravox.lang','bn')")
        mp = await m.new_page(); mp.on('pageerror', lambda e: errs.append('M PAGEERR '+str(e)))
        await mp.goto(B+'/', wait_until='domcontentloaded'); await mp.wait_for_timeout(800); await mp.screenshot(path='tests/m_landing.png')
        await mp.goto(B+'/studio/', wait_until='domcontentloaded'); await mp.wait_for_timeout(800); await mp.screenshot(path='tests/m_studio.png')
        sw = await mp.evaluate("()=>[document.documentElement.scrollWidth, innerWidth]"); print('studio mobile scrollWidth/innerWidth:', sw)
        await mp.goto(B+'/editor/bn/', wait_until='domcontentloaded'); await mp.wait_for_timeout(4500); await mp.screenshot(path='tests/m_editor.png')
        print('editor mobile:', await mp.evaluate("()=>({mobile:document.getElementById('app').classList.contains('is-mobile'), sw:document.documentElement.scrollWidth, iw:innerWidth})"))
        await mp.goto(B+'/nope/x', wait_until='domcontentloaded')
        print('errors:', errs or 'none')
        await b.close()
asyncio.run(main())
