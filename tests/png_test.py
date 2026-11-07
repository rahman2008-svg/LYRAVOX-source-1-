import asyncio, zipfile, io
from playwright.async_api import async_playwright
from PIL import Image
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--no-sandbox"]); ctx = await b.new_context(viewport={'width':1280,'height':800}, accept_downloads=True)
        await ctx.add_init_script("localStorage.setItem('lyravox.tourDone','1')")
        pg = await ctx.new_page(); await pg.goto('http://localhost:8800/editor/bn/', wait_until='domcontentloaded'); await pg.wait_for_timeout(3500)
        await pg.fill('#lyrics',"আমার সোনার বাংলা\nক্ষণিকের স্বপ্ন"); await pg.wait_for_timeout(1500)
        await pg.evaluate("()=>{J.ui.project.res=720; J.ui.project.fps=12; J.uiApi.replan();}"); await pg.wait_for_timeout(800)
        for bid,name in (('btnPNGA','alpha'),('btnPNG','plain')):
            async with pg.expect_download(timeout=200000) as d: await pg.evaluate(f"document.getElementById('{bid}').click()")
            dl=await d.value; path=f'tests/{name}.zip'; await dl.save_as(path)
            z=zipfile.ZipFile(path); names=z.namelist(); im=Image.open(io.BytesIO(z.read(names[len(names)//2])))
            a=im.getchannel('A') if im.mode=='RGBA' else None
            print(name, dl.suggested_filename, len(names),'files', im.size, im.mode, 'alpha range', a.getextrema() if a else None)
        await b.close()
asyncio.run(main())
