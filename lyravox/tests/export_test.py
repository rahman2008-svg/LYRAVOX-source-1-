import asyncio, json, sys
from playwright.async_api import async_playwright
URL='http://localhost:8800/editor/bn/'
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--no-sandbox"])
        ctx = await b.new_context(viewport={'width':1280,'height':800}, accept_downloads=True)
        pg = await ctx.new_page()
        errs=[]
        pg.on('pageerror', lambda e: errs.append('PAGEERR '+str(e)))
        await ctx.add_init_script("localStorage.setItem('lyravox.tourDone','1')"); await pg.goto(URL, wait_until='domcontentloaded'); await pg.wait_for_timeout(3500)
        lyr = "আমার সোনার বাংলা\nআমি তোমায় ভালোবাসি\nক্ষণিকের স্বপ্ন\nচিরদিন তোমার আকাশ"
        await pg.fill('#lyrics', lyr)
        await pg.set_input_files('#audioFile','tests/click120.wav')
        await pg.wait_for_timeout(5000)
        a = await pg.evaluate("()=>({name:J.ui.audio&&J.ui.audio.name, dur:J.ui.audio&&J.ui.audio.duration, bpm:J.ui.audio&&J.ui.audio.bpm, beats:J.ui.audio&&J.ui.audio.beats.slice(0,6), planDur:J.ui.plan.duration, snap:J.ui.project.timing.snap, firstCuts:J.ui.plan.cuts.slice(0,5).map(c=>[+c.start.toFixed(3),+c.end.toFixed(3)])})")
        print('AUDIO', json.dumps(a))
        # make export small: 720p standard via project fields
        await pg.evaluate("()=>{J.ui.project.res=720; J.ui.project.quality='standard'; J.ui.project.fps=24;}")
        await pg.evaluate("()=>J.uiApi.replan()")
        await pg.wait_for_timeout(500)
        # switch to pro mode so #btnMP4 exists
        await pg.click('#modePro'); await pg.wait_for_timeout(500)
        async with pg.expect_download(timeout=240000) as d:
            await pg.evaluate("document.getElementById('btnMP4').click()")
        dl = await d.value
        await dl.save_as('tests/out.mp4')
        print('DOWNLOAD', dl.suggested_filename)
        await pg.wait_for_timeout(1500)
        txt = await pg.evaluate("()=>[...document.querySelectorAll('.exp-text')].map(e=>e.textContent)")
        print('STATUS', txt[:2])
        # library + export history
        lib = await pg.evaluate("""async()=>{const p=await LVStore.projects.list(); const e=await LVStore.exports.list(); const au=await LVStore.audio.list(); return {projects:p.map(r=>({id:r.id,title:r.title,lines:r.lines,audioId:r.audioId,thumb:r.thumb.length,lang:r.lang})), exports:e.map(x=>({f:x.format,n:x.name,s:x.size,W:x.W,H:x.H})), audio:au.map(x=>({n:x.name,s:x.size,d:x.duration,bpm:x.bpm}))}}""")
        print('LIB', json.dumps(lib,ensure_ascii=False))
        print('\n'.join(errs) or 'no page errors')
        await b.close()
asyncio.run(main())
