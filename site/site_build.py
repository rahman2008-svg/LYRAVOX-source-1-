# -*- coding: utf-8 -*-
"""LYRAVOX site generator: landing, studio, about, developer, credits, privacy, terms, contact, 404, sitemap, robots, manifest, vercel config."""
import os, shutil, datetime, json
HERE = os.path.dirname(os.path.abspath(__file__))
DEV = dict(name='Prince AR Abdur Rahman', org="NexVora Lab's Ofc", portfolio='https://prince-ar-abdur-rahman.vercel.app',
           fb='https://www.facebook.com/share/1BNn32qoJo/', ig='https://www.instagram.com/ur___abdur____rahman__',
           mail='prince.ar.abdur.rahman2008@gmail.com', wa='01707424006', wa_intl='8801707424006', phone='01796951709')
UPDATED = '2026-11-06'

def t(en, bn): return f'<span class="t-en">{en}</span><span class="t-bn">{bn}</span>'
def tb(en, bn): return f'<div class="t-en">{en}</div><div class="t-bn">{bn}</div>'
LOGO = open(os.path.join(HERE, '..', 'app', 'logo.svg.txt'), encoding='utf-8').read()

def shell(rel, slug, title_en, title_bn, desc_en, desc_bn, body, site, ver, head_extra='', cur='', body_class=''):
    url = site + (slug + '/' if slug else '')
    nav = [('', 'Home', 'হোম'), ('studio/', 'Studio', 'স্টুডিও'), ('about/', 'About', 'পরিচিতি'), ('developer/', 'Developer', 'ডেভেলপার'), ('credits/', 'Credits', 'ক্রেডিট'), ('contact/', 'Contact', 'যোগাযোগ')]
    navh = ''.join(f'<a href="{rel}{p}"{" aria-current=page" if (p.rstrip("/") == cur) else ""}>{t(e, b)}</a>' for p, e, b in nav)
    navh += f'<a class="btn pri sm" data-editor href="{rel}editor/">{t("Open Editor", "এডিটর খুলুন")}</a>'
    footer = f'''<footer class="ft"><div class="wrap"><div class="cols">
<div><a class="logo" href="{rel}" style="padding:0">{LOGO}<span>LYRAVOX</span></a><p style="color:var(--muted);font-size:14px;max-width:26em;margin:12px 0 0">{t("Turn Every Lyric Into a Visual Story.", "প্রতিটি লিরিক্সকে বানান একটি দৃশ্যকাহিনি।")}</p></div>
<div><h4>{t("Product", "প্রোডাক্ট")}</h4><a data-editor href="{rel}editor/">{t("Editor", "এডিটর")}</a><a href="{rel}studio/">{t("Studio", "স্টুডিও")}</a><a href="{rel}about/">{t("About", "পরিচিতি")}</a></div>
<div><h4>{t("Company", "প্রতিষ্ঠান")}</h4><a href="{rel}developer/">{t("Developer", "ডেভেলপার")}</a><a href="{rel}credits/">{t("Credits & licenses", "ক্রেডিট ও লাইসেন্স")}</a><a href="{rel}contact/">{t("Contact", "যোগাযোগ")}</a></div>
<div><h4>{t("Legal", "আইনি")}</h4><a href="{rel}privacy/">{t("Privacy policy", "গোপনীয়তা নীতি")}</a><a href="{rel}terms/">{t("Terms of use", "ব্যবহারের শর্ত")}</a><a href="{rel}sitemap.xml">Sitemap</a></div>
</div><p class="small">© 2026 {DEV["org"]} · LYRAVOX v{ver} · {t("Developed by", "ডেভেলপার")} {DEV["name"]} · {t("Made in Bangladesh", "বাংলাদেশে তৈরি")}<br>{t("Built on the open-source JIZURA by hakoniwa, MIT License.", "ওপেন সোর্স JIZURA (hakoniwa, MIT লাইসেন্স)-এর উপর ভিত্তি করে তৈরি।")}</p></div></footer>'''
    api_url = os.environ.get('LYRAVOX_API_URL', '').strip().rstrip('/')
    inline_js = "<script>(function(){var l='en';try{l=localStorage.getItem('lyravox.lang')||(/^bn/i.test(navigator.language)?'bn':'en')}catch(e){}var d=document.documentElement;d.setAttribute('data-lang',l);d.lang=l;var t=d.getAttribute('data-title-'+l);if(t)document.title=t;window.LV_ROOT='@ROOT@';})();</script>".replace('@ROOT@', rel)
    ld = json.dumps({"@context": "https://schema.org", "@type": "SoftwareApplication", "name": "LYRAVOX", "applicationCategory": "MultimediaApplication", "operatingSystem": "Any (modern browser)",
                     "softwareVersion": ver, "description": desc_en, "url": site, "inLanguage": ["en", "bn"], "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
                     "author": {"@type": "Person", "name": DEV['name'], "url": DEV['portfolio']}, "publisher": {"@type": "Organization", "name": DEV['org']}}, ensure_ascii=False)
    return f'''<!doctype html>
<html lang="en" data-lang="en" data-title-en="{title_en}" data-title-bn="{title_bn}">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{title_en}</title>
<meta name="description" content="{desc_en}">
<meta name="theme-color" content="#060913"><meta name="author" content="{DEV['name']}"><meta name="robots" content="{'noindex' if slug == '404' else 'index, follow'}">
<link rel="canonical" href="{url}">
<link rel="icon" href="{rel}favicon.svg" type="image/svg+xml"><link rel="icon" href="{rel}favicon-32.png" sizes="32x32" type="image/png"><link rel="apple-touch-icon" href="{rel}apple-touch-icon.png"><link rel="manifest" href="{rel}manifest.webmanifest">
<meta property="og:type" content="website"><meta property="og:site_name" content="LYRAVOX"><meta property="og:title" content="{title_en}"><meta property="og:description" content="{desc_en}"><meta property="og:url" content="{url}">
<meta property="og:image" content="{site}og-image.png"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630"><meta property="og:locale" content="en_US"><meta property="og:locale:alternate" content="bn_BD">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{title_en}"><meta name="twitter:description" content="{desc_en}"><meta name="twitter:image" content="{site}og-image.png">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&amp;family=JetBrains+Mono:wght@500;700&amp;family=Noto+Sans+Bengali:wght@400;500;600;700;800&amp;display=swap">
<link rel="stylesheet" href="{rel}assets/site.css?v={ver}">{'<link rel="stylesheet" href="' + rel + 'assets/aigen.css?v=' + ver + '"><meta name="lyravox-api" content="' + api_url + '"><script src="' + rel + 'config.js"></script>' if slug == 'studio' else ''}
{inline_js}
<script type="application/ld+json">{ld}</script>
{head_extra}
</head>
<body class="{body_class}">
<a class="sr" href="#main">Skip to content</a>
<header class="hd"><div class="wrap"><a class="logo" href="{rel}" aria-label="LYRAVOX home">{LOGO}<span>LYRAVOX</span></a>
<button class="menu-btn" aria-expanded="false" aria-controls="nav" type="button">☰</button>
<nav class="nav" id="nav" aria-label="Main">{navh}<span class="lang" role="group" aria-label="Language"><button type="button" data-l="en" aria-pressed="true">EN</button><button type="button" data-l="bn" aria-pressed="false">বাংলা</button></span></nav></div></header>
<main id="main">
{body}
</main>
{footer}
<script src="{rel}assets/site.js?v={ver}" defer></script>
{'<script src="' + rel + 'assets/store.js?v=' + ver + '" defer></script><script src="' + rel + 'assets/aigen.js?v=' + ver + '" defer></script><script src="' + rel + 'assets/studio.js?v=' + ver + '" defer></script>' if slug == 'studio' else ''}
</body>
</html>
'''

def ico(e): return f'<div class="ico" aria-hidden="true">{e}</div>'
def card(e, h_en, h_bn, p_en, p_bn): return f'<div class="card">{ico(e)}<h3>{t(h_en, h_bn)}</h3><p>{t(p_en, p_bn)}</p></div>'

def landing(rel, site, ver):
    feats = [
        ('✍️', 'Lyrics editor', 'লিরিক্স এডিটর', 'One line is one phrase. Add cuts, emphasis, notes and interludes with a tiny syntax, in English, বাংলা and more.', 'এক লাইন মানে এক বাক্যাংশ। ছোট সিনট্যাক্সে কাট, জোর, টীকা ও বাদ্যাংশ যোগ করুন, ইংরেজি, বাংলা ও আরও ভাষায়।'),
        ('🎧', 'Audio & beat detection', 'অডিও ও বিট শনাক্ত', 'Load mp3, wav or m4a. LYRAVOX analyses the track in your browser, finds BPM and beats and snaps cuts to them.', 'mp3, wav বা m4a দিন। LYRAVOX ব্রাউজারেই গান বিশ্লেষণ করে BPM ও বিট খোঁজে এবং কাট সেগুলোর সাথে মেলায়।'),
        ('⏱️', 'Tap-to-sync & timeline', 'ট্যাপ সিঙ্ক ও টাইমলাইন', 'Tap while the song plays to stamp every line, then drag markers on the zoomable timeline for frame-accurate timing.', 'গান চলার সময় ট্যাপ করে প্রতিটি লাইনের সময় বসান, তারপর জুমযোগ্য টাইমলাইনে মার্কার টেনে নিখুঁত করুন।'),
        ('🎬', '860 motion components', '৮৬০টি মোশন কম্পোনেন্ট', 'Kinetic, typographic, decorative, layout and horror parts, mixed by a seed so every variation is different and repeatable.', 'কাইনেটিক, টাইপোগ্রাফিক, ডেকোরেটিভ, লেআউট ও হরর পার্ট, সিড দিয়ে মেশানো, তাই প্রতিটি ভ্যারিয়েশন আলাদা কিন্তু পুনরায় বানানো যায়।'),
        ('🔤', 'Typography & text effects', 'টাইপোগ্রাফি ও টেক্সট ইফেক্ট', 'Per-character animation that respects Bangla conjuncts, plus fonts for Latin, Bengali, Japanese, Chinese and Korean lyrics.', 'বাংলা যুক্তাক্ষর অক্ষুণ্ণ রেখে প্রতি অক্ষরে অ্যানিমেশন, সাথে ল্যাটিন, বাংলা, জাপানি, চীনা ও কোরিয়ান ফন্ট।'),
        ('🎨', 'Backgrounds, colours & styles', 'ব্যাকগ্রাউন্ড, রং ও স্টাইল', '27 styles, mood, palette and custom colours. Green-screen or black-background output for compositing.', '২৭টি স্টাইল, মুড, প্যালেট ও কাস্টম রং। কম্পোজিটিংয়ের জন্য গ্রিন স্ক্রিন বা কালো ব্যাকগ্রাউন্ড আউটপুট।'),
        ('📤', 'MP4, PNG & transparent PNG', 'MP4, PNG ও স্বচ্ছ PNG', 'H.264 MP4 with audio, PNG sequences, transparent PNG and separated back/front layers, from 9:16 to 16:9 up to 4K.', 'অডিওসহ H.264 MP4, PNG সিকোয়েন্স, স্বচ্ছ PNG এবং আলাদা back/front লেয়ার, ৯:১৬ থেকে ১৬:৯ এবং ৪K পর্যন্ত।'),
        ('📱', 'Mobile editing mode', 'মোবাইল এডিটিং মোড', 'A touch-first layout for Android Chrome with a phone-safe 1080p export limit.', 'Android Chrome-এর জন্য টাচ-ফার্স্ট লেআউট, ফোনে নিরাপদ ১০৮০p এক্সপোর্ট সীমা সহ।'),
        ('✨', 'AI Generate Lyrics', 'AI দিয়ে লিরিক্স', 'Optional: detect sung lyrics in Bangla, English or Hindi from your song, correct them in a line editor and send them, with timestamps, straight into the editor. Needs the LYRAVOX AI server.', 'ঐচ্ছিক: গান থেকে বাংলা, ইংরেজি বা হিন্দি লিরিক্স শনাক্ত করুন, লাইন এডিটরে ঠিক করুন, আর টাইমস্ট্যাম্পসহ সরাসরি এডিটরে পাঠান। LYRAVOX AI সার্ভার লাগে।'),
        ('🔒', 'Private by design', 'গোপনীয়তাই মূলনীতি', 'No account and no API keys. Editing, projects, songs and exports stay in your browser; only the optional AI lyrics feature sends the song to the AI server you choose, which deletes it after processing.', 'অ্যাকাউন্ট বা API key লাগে না। এডিটিং, প্রজেক্ট, গান ও এক্সপোর্ট ব্রাউজারেই থাকে; শুধু ঐচ্ছিক AI লিরিক্স ফিচার গানটি আপনার বেছে নেওয়া AI সার্ভারে পাঠায়, যা প্রসেসিংয়ের পর মুছে ফেলে।'),
    ]
    fh = ''.join(card(*f) for f in feats)
    demos = [('d-type', 'Typewriter', 'Hello, Dhaka', 'ভালোবাসি আমি'), ('d-glitch', 'Glitch', 'GLITCH', 'গ্লিচ'), ('d-neon', 'Neon', 'Neon Rain', 'নিয়ন বৃষ্টি'), ('d-wave', 'Wave', 'Rhythm', 'ছন্দ'),
             ('d-blur', 'Blur reveal', 'Fade In', 'আলো'), ('d-karaoke', 'Karaoke fill', 'Sing along', 'গাও সাথে'), ('d-flip', 'Flip', 'Flip', 'উল্টো'), ('d-stack', 'Scale stack', 'Louder', 'আরও জোরে')]
    dh = ''
    for cls, nm, en, bn in demos:
        if cls == 'd-wave':
            inner_en = ''.join(f'<span style="animation-delay:{i*0.1}s">{c}</span>' for i, c in enumerate(en))
            inner = f'<b class="t-en">{inner_en}</b><b class="t-bn">{bn}</b>'
        else:
            inner = f'<b class="t-en" data-t="{en}">{en}</b><b class="t-bn" data-t="{bn}">{bn}</b>'
        dh += f'<div class="demo {cls}" role="img" aria-label="{nm} animation demo">{inner}<small>{nm}</small></div>'
    steps = [('Paste your lyrics', 'লিরিক্স পেস্ট করুন', 'Type or paste lyrics, import an LRC file, or let AI detect them from the song. Bangla and English both work.', 'লিরিক্স লিখুন বা পেস্ট করুন, LRC ফাইল ইমপোর্ট করুন, বা AI দিয়ে গান থেকে শনাক্ত করান। বাংলা ও ইংরেজি দুটোই চলে।'),
             ('Add your song', 'গান যোগ করুন', 'Load an audio file. Beats are detected and cuts are timed to them. Tap to sync if you want exact line starts.', 'অডিও ফাইল দিন। বিট শনাক্ত হয়ে কাট তার সাথে মেলে। লাইনের ঠিক শুরু চাইলে ট্যাপ সিঙ্ক করুন।'),
             ('Create a variation', 'ভ্যারিয়েশন বানান', 'Press once for a complete design. Randomize, shuffle or re-roll just one line until it feels right.', 'একবার চাপলেই পূর্ণ ডিজাইন। পছন্দ না হওয়া পর্যন্ত র‍্যান্ডমাইজ, শাফল বা শুধু একটি লাইন আবার বাছুন।'),
             ('Export & share', 'এক্সপোর্ট ও শেয়ার', 'Choose ratio and resolution and export MP4 or PNG, all inside your browser.', 'রেশিও ও রেজোলিউশন বেছে MP4 বা PNG এক্সপোর্ট করুন, সবকিছু আপনার ব্রাউজারেই।')]
    sh = ''.join(f'<div class="step"><h3>{t(a, b)}</h3><p>{t(c, d)}</p></div>' for a, b, c, d in steps)
    return f'''
<section class="hero"><div id="bgtype" aria-hidden="true"></div><div class="wrap">
<span class="badge"><i></i>{t("Free · edits in your browser · v" + ver, "বিনামূল্যে · ব্রাউজারেই এডিট · v" + ver)}</span>
<h1>{t('Turn Every Lyric Into a <span class="grad">Visual Story.</span>', 'প্রতিটি লিরিক্সকে বানান একটি <span class="grad">দৃশ্যকাহিনি।</span>')}</h1>
<p class="lead">{t("LYRAVOX is an independent lyric motion video studio. Write lyrics, add a song, and get beat-timed animated typography, exported as MP4 or PNG without leaving your browser.", "LYRAVOX একটি স্বাধীন লিরিক মোশন ভিডিও স্টুডিও। লিরিক্স লিখুন, গান যোগ করুন, আর পান বিট-মেলানো অ্যানিমেটেড টাইপোগ্রাফি, ব্রাউজার ছাড়াই MP4 বা PNG হিসেবে এক্সপোর্ট করা।")}</p>
<div class="cta"><a class="btn pri" data-editor href="{rel}editor/">{t("Create Your First Video", "আপনার প্রথম ভিডিও বানান")} →</a><a class="btn" href="{rel}studio/">{t("Open Studio", "স্টুডিও খুলুন")}</a></div>
<div class="chips"><span>{t("No account", "অ্যাকাউন্ট নেই")}</span><span>{t("Edits & exports stay local", "এডিট ও এক্সপোর্ট লোকালিই থাকে")}</span><span>{t("No API keys", "API key নেই")}</span><span>English + বাংলা</span></div>
</div></section>
<section class="s" id="features"><div class="wrap"><div class="eyebrow">{t("Features", "বৈশিষ্ট্য")}</div><h2 class="t">{t("Everything a lyric video needs, in one tab", "লিরিক ভিডিওর সবকিছু, একটি ট্যাবে")}</h2><p class="sub">{t("A full editing engine with 860 motion components, not a template picker.", "৮৬০টি মোশন কম্পোনেন্টসহ পূর্ণাঙ্গ এডিটিং ইঞ্জিন, শুধু টেমপ্লেট বাছাই নয়।")}</p><div class="grid g3">{fh}</div></div></section>
<section class="s" id="how"><div class="wrap"><div class="eyebrow">{t("How it works", "যেভাবে কাজ করে")}</div><h2 class="t">{t("From lyrics to video in four steps", "লিরিক্স থেকে ভিডিও, চার ধাপে")}</h2><div class="steps">{sh}</div></div></section>
<section class="s" id="showcase"><div class="wrap"><div class="eyebrow">{t("Animation showcase", "অ্যানিমেশন শোকেস")}</div><h2 class="t">{t("A small taste of the motion", "মোশনের এক ঝলক")}</h2><p class="sub">{t("These are quick previews of effect styles. The editor itself contains 860 components with seeded variations.", "এগুলো ইফেক্ট স্টাইলের ছোট প্রিভিউ। এডিটরে সিড-নির্ভর ভ্যারিয়েশনসহ ৮৬০টি কম্পোনেন্ট আছে।")}</p><div class="grid g4">{dh}</div></div></section>
<section class="s"><div class="wrap"><div class="stats"><div><b class="grad">860</b><span>{t("motion components", "মোশন কম্পোনেন্ট")}</span></div><div><b class="grad">8</b><span>{t("editor languages", "এডিটর ভাষা")}</span></div><div><b class="grad">4</b><span>{t("export types", "এক্সপোর্ট ধরন")}</span></div><div><b class="grad">0</b><span>{t("API keys needed", "API key লাগে")}</span></div></div></div></section>
<section class="s" id="developer"><div class="wrap"><div class="eyebrow">{t("Developer", "ডেভেলপার")}</div><h2 class="t">{t("Built in Bangladesh", "বাংলাদেশে তৈরি")}</h2>
<div class="dev"><div class="avatar" aria-hidden="true">AR</div><div><h3>{DEV["name"]}</h3><p>{t("Founder & Independent Student Developer · " + DEV["org"], "প্রতিষ্ঠাতা ও স্বাধীন শিক্ষার্থী ডেভেলপার · " + DEV["org"])}</p><p>{t("LYRAVOX is published by NexVora Lab's Ofc on top of the open-source JIZURA editing engine.", "LYRAVOX প্রকাশ করেছে NexVora Lab's Ofc, ওপেন সোর্স JIZURA এডিটিং ইঞ্জিনের উপর ভিত্তি করে।")}</p>
<div class="links"><a class="btn sm" href="{rel}developer/">{t("Full profile", "পূর্ণ প্রোফাইল")}</a><a class="btn sm" href="{DEV['portfolio']}" target="_blank" rel="noopener">Portfolio</a><a class="btn sm" href="{rel}contact/">{t("Contact", "যোগাযোগ")}</a></div></div></div></div></section>
<section class="s"><div class="wrap" style="text-align:center"><h2 class="t">{t("Ready to see your lyrics move?", "আপনার লিরিক্স নড়তে দেখতে প্রস্তুত?")}</h2><p class="sub" style="margin-inline:auto">{t("Open the editor. It starts with sample lyrics so you can press play right away.", "এডিটর খুলুন। নমুনা লিরিক্স দেওয়া থাকে, তাই সঙ্গে সঙ্গেই প্লে করতে পারবেন।")}</p><a class="btn pri" data-editor href="{rel}editor/">{t("Create Your First Video", "আপনার প্রথম ভিডিও বানান")} →</a></div></section>'''

def studio(rel, site, ver):
    side = [('projects', '📁', 'Projects', 'প্রজেক্ট'), ('audio', '🎵', 'Audio Library', 'অডিও লাইব্রেরি'), ('lyrics', '📝', 'Lyrics Studio', 'লিরিক্স স্টুডিও'), ('exports', '🧾', 'Export History', 'এক্সপোর্ট ইতিহাস')]
    sb = ''.join(f'<button type="button" role="tab" id="tab-{k}" aria-selected="{"true" if k=="projects" else "false"}">{i} <span>{t(e, b)}</span><span class="cnt" id="cnt-{k}"></span></button>' if k != 'lyrics' else f'<button type="button" role="tab" id="tab-{k}" aria-selected="false">{i} <span>{t(e, b)}</span></button>' for k, i, e, b in side)
    return f'''<div class="wrap studio"><nav class="side" role="tablist" aria-label="Studio">{sb}</nav><div>
<section class="pane" id="pane-projects"><h2>{t("Projects", "প্রজেক্ট")}</h2><p class="d">{t("Your projects are saved automatically while you edit, in this browser only.", "এডিট করার সময় আপনার প্রজেক্ট নিজে থেকেই সেভ হয়, শুধু এই ব্রাউজারে।")}</p>
<div class="bar"><button class="btn pri" id="btnNew" type="button">+ {t("Create New Project", "নতুন প্রজেক্ট বানান")}</button><label class="btn" for="pimport">⬆ {t("Import Project", "প্রজেক্ট ইমপোর্ট")}</label><input id="pimport" type="file" accept=".json,application/json" multiple hidden>
<input type="search" id="pq" placeholder="Search…" aria-label="Search projects"><select id="psort" aria-label="Sort"><option value="recent">Recent</option><option value="name">A–Z</option></select></div>
<div id="drop" class="drop" style="margin-bottom:16px">{t("Drop a project file here (.json from the editor's Save button, also JIZURA projects)", "এখানে প্রজেক্ট ফাইল ফেলুন (এডিটরের Save বাটনের .json, JIZURA প্রজেক্টও চলে)")}</div>
<h3 style="margin:18px 0 10px">{t("Recent Projects", "সাম্প্রতিক প্রজেক্ট")}</h3><div class="pgrid" id="pgrid"></div><div class="empty" id="pempty" hidden>{t("No projects yet. Create one or import a project file.", "এখনও কোনো প্রজেক্ট নেই। নতুন বানান বা প্রজেক্ট ফাইল ইমপোর্ট করুন।")}</div></section>
<section class="pane" id="pane-audio" hidden><h2>{t("Audio Library", "অডিও লাইব্রেরি")}</h2><p class="d">{t("Songs used by your projects, kept in this browser. Add songs here to start a project from them.", "আপনার প্রজেক্টে ব্যবহৃত গান, এই ব্রাউজারে রাখা। এখান থেকে গান যোগ করে সেটি দিয়ে প্রজেক্ট শুরু করতে পারেন।")}</p>
<div class="bar"><label class="btn pri" for="afile">⬆ {t("Add song", "গান যোগ করুন")}</label><input id="afile" type="file" accept="audio/*,.mp3,.wav,.m4a,.aac,.ogg,.flac" multiple hidden><label class="btn" for="aifile" id="aiBtn">✨ {t("AI Generate Lyrics", "AI দিয়ে লিরিক্স বানান")}</label><input id="aifile" type="file" accept="audio/*,.mp3,.wav,.m4a,.aac,.ogg" hidden></div><div id="alist"></div><div class="empty" id="aempty" hidden>{t("No songs yet. Upload one or open a project that has a song.", "এখনও কোনো গান নেই। গান আপলোড করুন বা গানসহ প্রজেক্ট খুলুন।")}</div></section>
<section class="pane" id="pane-lyrics" hidden><h2>{t("Lyrics Studio", "লিরিক্স স্টুডিও")}</h2><p class="d">{t("Prepare lyrics before you open the editor: clean them up, import an LRC file, add evenly spaced timestamps, and send them to a new project.", "এডিটর খোলার আগে লিরিক্স তৈরি করুন: পরিষ্কার করুন, LRC ফাইল ইমপোর্ট করুন, সমান ব্যবধানে টাইমস্ট্যাম্প বসান এবং নতুন প্রজেক্টে পাঠান।")}</p>
<div class="two"><div><div class="fld"><label for="ltitle">{t("Song title", "গানের নাম")}</label><input id="ltitle" type="text" maxlength="80"></div>
<div class="fld"><label for="lyr">{t("Lyrics (one line = one phrase; [mm:ss.xx] timestamps are kept)", "লিরিক্স (এক লাইন = এক বাক্যাংশ; [mm:ss.xx] টাইমস্ট্যাম্প থাকবে)")}</label><textarea id="lyr" spellcheck="false" lang="bn"></textarea></div><div class="stat-line" id="lstats" aria-live="polite"></div>
<div class="bar"><button class="btn sm" id="lclean" type="button">{t("Clean up", "পরিষ্কার করুন")}</button><button class="btn sm" id="lstrip" type="button">{t("Remove timestamps", "টাইমস্ট্যাম্প সরান")}</button><span class="fld" style="margin:0;display:flex;flex-direction:row;align-items:center;gap:6px"><label for="lstep" style="margin:0">{t("Seconds between lines", "দুই লাইনের মাঝে সেকেন্ড")}</label><input id="lstep" type="number" min="0.5" step="0.5" value="4" style="width:80px"></span><button class="btn sm" id="lstamp" type="button">{t("Add timestamps", "টাইমস্ট্যাম্প যোগ")}</button></div>
<div class="bar"><button class="btn pri" id="lopen" type="button">{t("Open in editor as new project", "নতুন প্রজেক্ট হিসেবে এডিটরে খুলুন")} →</button><label class="btn" for="lfile">{t("Import .lrc / .txt", ".lrc / .txt ইমপোর্ট")}</label><label class="btn" for="aifile2">✨ {t("From audio (AI)", "অডিও থেকে (AI)")}</label><input id="aifile2" type="file" accept="audio/*,.mp3,.wav,.m4a,.aac,.ogg" hidden><input id="lfile" type="file" accept=".lrc,.txt,text/plain" hidden><button class="btn" id="lsave" type="button">{t("Save draft", "ড্রাফট সেভ")}</button><button class="btn" id="ltxt" type="button">.txt</button><button class="btn" id="llrc" type="button">.lrc</button></div></div>
<aside class="panel"><h3>{t("Drafts", "ড্রাফট")}</h3><div id="drafts"></div><h3 style="margin-top:18px">{t("Syntax", "সিনট্যাক্স")}</h3><div class="prose" style="font-size:13px"><p><code>/</code> {t("cut", "কাট")} · <code>*word*</code> {t("emphasis", "জোর")} · <code>!</code> {t("flash", "ফ্ল্যাশ")} · <code>| note</code> {t("annotation", "টীকা")} · <code>[interlude 8]</code> {t("8 s instrumental", "৮ সে. বাদ্য")} · <code># comment</code></p></div></aside></div></section>
<section class="pane" id="pane-exports" hidden><h2>{t("Export History", "এক্সপোর্ট ইতিহাস")}</h2><p class="d">{t("A log of what you exported from the editor on this device. Files are in your downloads folder, not here.", "এই ডিভাইসে এডিটর থেকে যা এক্সপোর্ট করেছেন তার তালিকা। ফাইল আপনার ডাউনলোড ফোল্ডারে, এখানে নয়।")}</p>
<div class="bar"><button class="btn danger sm" id="eclear" type="button" hidden>{t("Clear history", "ইতিহাস মুছুন")}</button></div>
<div class="tblwrap"><table class="t" id="etable" hidden><thead><tr><th>{t("Date", "তারিখ")}</th><th>{t("Project", "প্রজেক্ট")}</th><th>{t("Format", "ফরম্যাট")}</th><th>{t("Size", "আকার")}</th><th>{t("Details", "বিবরণ")}</th><th></th></tr></thead><tbody id="ebody"></tbody></table></div><div class="empty" id="eempty" hidden>{t("No exports yet. Export a video, PNG ZIP, LRC or AE data from the editor and it appears here.", "এখনও কোনো এক্সপোর্ট নেই। এডিটর থেকে ভিডিও, PNG ZIP, LRC বা AE ডেটা এক্সপোর্ট করলে এখানে দেখা যাবে।")}</div></section>
</div></div><div class="toast" id="toast" role="status" aria-live="polite"></div>'''

def page(h_en, h_bn, inner): return f'<div class="wrap page"><h1>{t(h_en, h_bn)}</h1><div class="prose">{inner}</div></div>'

def about():
    return page('About LYRAVOX', 'LYRAVOX সম্পর্কে', tb(f'''<p>LYRAVOX is an independent online lyric motion video studio. You write or paste lyrics, add a song, and LYRAVOX builds animated, beat-timed typography that you can export as MP4, PNG sequences or transparent PNG, all inside your browser.</p>
<h2>What it does</h2><ul><li>Lyrics editor with a small syntax for cuts, emphasis, notes and instrumental breaks, plus LRC import and export.</li><li>Browser-side audio analysis: BPM and beat detection, tap-to-sync and a draggable, zoomable timeline.</li><li>860 motion components, 27 styles, moods, palettes, custom colours and fonts.</li><li>Export H.264 MP4 (with audio), PNG sequence ZIP, transparent PNG and back/front layers; multiple aspect ratios, resolutions and frame rates.</li><li>Projects are saved in your browser and can be exported to or imported from a .json file.</li><li>AI Generate Lyrics (optional, needs the AI server): speech-to-text with Whisper for Bangla, English and Hindi, optional vocal separation, an editable line list with timestamps, and one-click transfer into the editor.</li><li>Editor languages: English, বাংলা, 日本語, 繁體中文, 简体中文, 한국어, Bahasa Indonesia, Tiếng Việt.</li></ul>
<h2>Principles</h2><p>No account and no mandatory API keys or paid services. Editing, audio analysis and export run locally in your browser. The optional AI Generate Lyrics feature is the one exception: it sends the song you choose to the LYRAVOX AI server (a separate backend) for transcription and the server deletes it after processing. LYRAVOX is free software released under the MIT License.</p>
<h2>Origin</h2><p>The editing engine is a rebranded and extended version of <strong>JIZURA</strong> by hakoniwa (MIT License). LYRAVOX adds the Bangla language edition with proper conjunct handling, the Studio dashboard, project and audio library, export history and a new brand. See <a href="../credits/">Credits &amp; licenses</a>.</p>''', f'''<p>LYRAVOX একটি স্বাধীন অনলাইন লিরিক মোশন ভিডিও স্টুডিও। আপনি লিরিক্স লেখেন বা পেস্ট করেন, গান যোগ করেন, আর LYRAVOX বিট-মেলানো অ্যানিমেটেড টাইপোগ্রাফি বানিয়ে দেয়, যা ব্রাউজারের ভেতরেই MP4, PNG সিকোয়েন্স বা স্বচ্ছ PNG হিসেবে এক্সপোর্ট করা যায়।</p>
<h2>কী কী করে</h2><ul><li>কাট, জোর, টীকা ও বাদ্যাংশের ছোট সিনট্যাক্সসহ লিরিক্স এডিটর, সাথে LRC ইমপোর্ট ও এক্সপোর্ট।</li><li>ব্রাউজারেই অডিও বিশ্লেষণ: BPM ও বিট শনাক্ত, ট্যাপ সিঙ্ক এবং টানা-যায় ও জুম-করা-যায় এমন টাইমলাইন।</li><li>৮৬০টি মোশন কম্পোনেন্ট, ২৭টি স্টাইল, মুড, প্যালেট, কাস্টম রং ও ফন্ট।</li><li>অডিওসহ H.264 MP4, PNG সিকোয়েন্স ZIP, স্বচ্ছ PNG ও back/front লেয়ার এক্সপোর্ট; একাধিক অ্যাসপেক্ট রেশিও, রেজোলিউশন ও ফ্রেম রেট।</li><li>প্রজেক্ট ব্রাউজারে সেভ হয় এবং .json ফাইলে এক্সপোর্ট/ইমপোর্ট করা যায়।</li><li>AI দিয়ে লিরিক্স (ঐচ্ছিক, AI সার্ভার লাগে): বাংলা, ইংরেজি ও হিন্দির জন্য Whisper-ভিত্তিক স্পিচ-টু-টেক্সট, ঐচ্ছিক কণ্ঠ আলাদা করা, টাইমস্ট্যাম্পসহ সম্পাদনাযোগ্য লাইন তালিকা এবং এক ক্লিকে এডিটরে পাঠানো।</li><li>এডিটরের ভাষা: English, বাংলা, 日本語, 繁體中文, 简体中文, 한국어, Bahasa Indonesia, Tiếng Việt।</li></ul>
<h2>নীতি</h2><p>অ্যাকাউন্ট, বাধ্যতামূলক API key বা পেইড সার্ভিস নেই। এডিটিং, অডিও বিশ্লেষণ ও এক্সপোর্ট আপনার ব্রাউজারেই চলে। ঐচ্ছিক AI লিরিক্স ফিচারটি একমাত্র ব্যতিক্রম: আপনার বেছে নেওয়া গান লেখা বের করার জন্য LYRAVOX AI সার্ভারে (আলাদা ব্যাকএন্ড) পাঠানো হয় এবং প্রসেসিংয়ের পর সার্ভার তা মুছে ফেলে। LYRAVOX MIT লাইসেন্সের অধীনে মুক্ত সফটওয়্যার।</p>
<h2>উৎস</h2><p>এডিটিং ইঞ্জিনটি hakoniwa-র <strong>JIZURA</strong> (MIT লাইসেন্স)-এর রিব্র্যান্ড করা ও সম্প্রসারিত সংস্করণ। LYRAVOX যোগ করেছে সঠিক যুক্তাক্ষর-সামলানো বাংলা সংস্করণ, স্টুডিও ড্যাশবোর্ড, প্রজেক্ট ও অডিও লাইব্রেরি, এক্সপোর্ট ইতিহাস এবং নতুন ব্র্যান্ড। দেখুন <a href="../credits/">ক্রেডিট ও লাইসেন্স</a>।</p>'''))

def developer():
    links = [('🌐 Portfolio', DEV['portfolio'], 'prince-ar-abdur-rahman.vercel.app'), ('📘 Facebook', DEV['fb'], 'facebook.com/share/1BNn32qoJo'), ('📸 Instagram', DEV['ig'], '@ur___abdur____rahman__'),
             ('✉️ Email', 'mailto:' + DEV['mail'], DEV['mail']), ('💬 WhatsApp', 'https://wa.me/' + DEV['wa_intl'], DEV['wa']), ('📞 Contact', 'tel:' + DEV['phone'], DEV['phone'])]
    cards = ''.join(f'<a class="card" href="{u}"' + (' target="_blank" rel="noopener"' if u.startswith('http') else '') + f'><h3>{n}</h3><small>{s}</small></a>' for n, u, s in links)
    return f'''<div class="wrap page"><h1>{t("About the Developer", "ডেভেলপার সম্পর্কে")}</h1>
<div class="dev" style="margin:24px 0"><div class="avatar" aria-hidden="true">AR</div><div><h3>{DEV["name"]}</h3><p>{t("Founder & Independent Student Developer", "প্রতিষ্ঠাতা ও স্বাধীন শিক্ষার্থী ডেভেলপার")}</p><p>{DEV["org"]} · {t("Bangladesh", "বাংলাদেশ")}</p></div></div>
<div class="prose">{tb("<p>Prince AR Abdur Rahman builds independent apps and web platforms under NexVora Lab's Ofc. LYRAVOX is the lyric motion studio of that lab: a free, privacy-first tool that makes lyric videos possible from a phone or a computer, in Bangla as well as English.</p>", "<p>প্রিন্স এআর আব্দুর রহমান NexVora Lab's Ofc-এর অধীনে স্বাধীন অ্যাপ ও ওয়েব প্ল্যাটফর্ম বানান। LYRAVOX সেই ল্যাবের লিরিক মোশন স্টুডিও: একটি বিনামূল্যের, গোপনীয়তা-প্রথম টুল, যা ফোন বা কম্পিউটার থেকে ইংরেজির পাশাপাশি বাংলায়ও লিরিক ভিডিও বানানো সম্ভব করে।</p>")}</div>
<h2 style="margin-top:34px">{t("Find me", "যোগাযোগের মাধ্যম")}</h2><div class="ctc">{cards}</div></div>'''

MIT_ORIG = '''MIT License

Copyright (c) 2026 hakoniwa

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.'''

def credits(ver):
    # the license text is read from the repository files so the page can never drift from them
    lic = open(os.path.join(HERE, '..', 'LICENSE'), encoding='utf-8').read().strip()
    mux = open(os.path.join(HERE, '..', 'vendor', 'LICENSE.mp4-muxer.txt'), encoding='utf-8').read().strip()
    from html import escape as E
    return page('Credits & licenses', 'ক্রেডিট ও লাইসেন্স', tb(f'''<h2>About LYRAVOX</h2><p>LYRAVOX {ver} is developed by <strong>{DEV["name"]}</strong> and published by <strong>{DEV["org"]}</strong>, Bangladesh.</p>
<h2>About NexVora Lab's Ofc</h2><p>NexVora Lab's Ofc is an independent software lab founded by {DEV["name"]}, building Android apps and web platforms.</p>
<h2>Original project attribution</h2><p>LYRAVOX is a modified, rebranded version of <strong>JIZURA</strong> by <strong>hakoniwa</strong>, released under the MIT License (<a href="https://github.com/852wa/JIZURA" target="_blank" rel="noopener">github.com/852wa/JIZURA</a>). The engine (planner, 860 motion components, renderer, MP4/PNG export) comes from that project. LYRAVOX changes include the new brand and interface theme, the Bangla edition (language detection, Bengali fonts, grapheme-cluster-safe text layout, translated interface), the Studio dashboard, project/audio library, export history and the site pages. JIZURA is not affiliated with and does not endorse LYRAVOX.</p>
<h2>Open-source license</h2><p>LYRAVOX is distributed under the MIT License. The original copyright line is kept, with a line for the LYRAVOX modifications added.</p><pre>{E(lic)}</pre>
<h2>Third-party notices</h2>
<h3>mp4-muxer (bundled in the editor)</h3><p>Used to write MP4 files. MIT License, © 2023 Vanilagy.</p><pre>{E(mux)}</pre>
<h3>AI Generate Lyrics backend (separate service, not bundled in the site)</h3><p>faster-whisper (MIT) running OpenAI Whisper model weights (MIT), including the Silero VAD model it ships (MIT); optional Demucs (MIT) for vocal separation; FastAPI (MIT), Uvicorn (BSD-3-Clause), python-multipart (Apache-2.0); FFmpeg is called as an external program and is installed by the host's package manager (its LGPL/GPL terms depend on the build). Licenses stated to the best of our knowledge; check them before redistributing the backend image.</p>
<h3>Fonts (loaded from Google Fonts at runtime, not bundled)</h3><p>The editor and the site request font files from Google Fonts only when they are needed (this sends a normal web request to Google). The families include Inter, JetBrains Mono, IBM Plex Sans JP, Noto Sans / Serif JP, KR, TC, SC and Bengali, Hind Siliguri, Baloo Da 2, Tiro Bangla, Galada, Atma, Mina and the Japanese display faces listed in the original JIZURA notices. These are distributed by Google Fonts under open-source font licenses (predominantly the SIL Open Font License 1.1). Fonts you load yourself stay on your device and remain under their own licenses.</p>
<h3>Your content</h3><p>You own the videos and images you export. Lyrics and music remain the property of their rights holders: make sure you may use them.</p>''',
f'''<h2>LYRAVOX সম্পর্কে</h2><p>LYRAVOX {ver}-এর ডেভেলপার <strong>{DEV["name"]}</strong> এবং প্রকাশক <strong>{DEV["org"]}</strong>, বাংলাদেশ।</p>
<h2>NexVora Lab's Ofc সম্পর্কে</h2><p>NexVora Lab's Ofc একটি স্বাধীন সফটওয়্যার ল্যাব, প্রতিষ্ঠাতা {DEV["name"]}, যেখানে Android অ্যাপ ও ওয়েব প্ল্যাটফর্ম বানানো হয়।</p>
<h2>মূল প্রজেক্টের স্বীকৃতি</h2><p>LYRAVOX হলো <strong>hakoniwa</strong>-র <strong>JIZURA</strong>-র পরিবর্তিত ও রিব্র্যান্ড করা সংস্করণ, MIT লাইসেন্সে প্রকাশিত (<a href="https://github.com/852wa/JIZURA" target="_blank" rel="noopener">github.com/852wa/JIZURA</a>)। ইঞ্জিন (প্ল্যানার, ৮৬০টি মোশন কম্পোনেন্ট, রেন্ডারার, MP4/PNG এক্সপোর্ট) ওই প্রজেক্ট থেকে নেওয়া। LYRAVOX-এর পরিবর্তনের মধ্যে আছে নতুন ব্র্যান্ড ও থিম, বাংলা সংস্করণ (ভাষা শনাক্ত, বাংলা ফন্ট, যুক্তাক্ষর-নিরাপদ টেক্সট লেআউট, অনূদিত ইন্টারফেস), স্টুডিও ড্যাশবোর্ড, প্রজেক্ট/অডিও লাইব্রেরি, এক্সপোর্ট ইতিহাস ও সাইট পেজ। JIZURA-র সাথে LYRAVOX-এর কোনো সম্পর্ক নেই এবং তারা এটি অনুমোদনও করে না।</p>
<h2>ওপেন-সোর্স লাইসেন্স</h2><p>LYRAVOX MIT লাইসেন্সে বিতরিত। মূল কপিরাইট লাইন অক্ষুণ্ণ রাখা হয়েছে, সাথে LYRAVOX-এর পরিবর্তনের একটি লাইন যোগ হয়েছে।</p><pre>{E(lic)}</pre>
<h2>থার্ড-পার্টি নোটিস</h2>
<h3>mp4-muxer (এডিটরে বান্ডল করা)</h3><p>MP4 ফাইল লিখতে ব্যবহৃত। MIT লাইসেন্স, © ২০২৩ Vanilagy।</p><pre>{E(mux)}</pre>
<h3>AI লিরিক্স ব্যাকএন্ড (আলাদা সার্ভিস, সাইটে বান্ডল করা নয়)</h3><p>faster-whisper (MIT), OpenAI Whisper মডেল ওয়েট (MIT) চালানো, সাথে তার Silero VAD মডেল (MIT); কণ্ঠ আলাদা করতে ঐচ্ছিক Demucs (MIT); FastAPI (MIT), Uvicorn (BSD-3-Clause), python-multipart (Apache-2.0); FFmpeg বাইরের প্রোগ্রাম হিসেবে চালানো হয় এবং হোস্টের প্যাকেজ ম্যানেজার ইনস্টল করে (এর LGPL/GPL শর্ত বিল্ডভেদে ভিন্ন)। লাইসেন্স আমাদের জানা মতে; ব্যাকএন্ড ইমেজ পুনর্বিতরণের আগে যাচাই করুন।</p>
<h3>ফন্ট (রানটাইমে Google Fonts থেকে লোড হয়, বান্ডল করা নয়)</h3><p>এডিটর ও সাইট প্রয়োজন হলেই Google Fonts থেকে ফন্ট ফাইল চায় (এতে Google-এ একটি সাধারণ ওয়েব অনুরোধ যায়)। ফ্যামিলির মধ্যে আছে Inter, JetBrains Mono, IBM Plex Sans JP, Noto Sans / Serif (JP, KR, TC, SC, Bengali), Hind Siliguri, Baloo Da 2, Tiro Bangla, Galada, Atma, Mina এবং মূল JIZURA নোটিসে তালিকাভুক্ত জাপানি ডিসপ্লে ফন্ট। এগুলো Google Fonts-এ ওপেন-সোর্স ফন্ট লাইসেন্সে (প্রধানত SIL Open Font License 1.1) বিতরিত। আপনি নিজে যে ফন্ট লোড করেন তা আপনার ডিভাইসেই থাকে এবং নিজস্ব লাইসেন্সের অধীন।</p>
<h3>আপনার কনটেন্ট</h3><p>আপনার এক্সপোর্ট করা ভিডিও ও ছবির মালিক আপনি। লিরিক্স ও গানের মালিকানা স্বত্বাধিকারীদের: ব্যবহারের অধিকার আছে কিনা নিশ্চিত করুন।</p>'''))

def privacy():
    return page('Privacy Policy', 'গোপনীয়তা নীতি', tb(f'''<p><em>Last updated: {UPDATED}</em></p><p>LYRAVOX is designed so that your creative work never leaves your device.</p>
<h2>What stays on your device</h2><p>Lyrics, songs, projects, thumbnails and the export history are processed and stored only in your browser (IndexedDB and localStorage). Except for the optional AI feature described below, they are not uploaded anywhere, and LYRAVOX has no accounts. Clearing your browser's site data deletes them.</p>
<h2>AI Generate Lyrics (optional)</h2><p>This is the only feature that sends your audio over the network. When you press <em>Generate Lyrics</em>, the song (or the section you chose) is uploaded to the LYRAVOX AI server whose address is configured for the site (or that you typed in the dialog), where it is converted to text. The server keeps the upload only while it is processed and deletes it, and every file derived from it, as soon as the job ends (completed, failed or cancelled). The resulting lyrics are held in the server's memory for a short time (30 minutes by default) so your browser can fetch them, then forgotten. If you run your own server, you control all of this; if you use someone else's, their policy applies. Do not upload audio you are not allowed to share.</p>
<h2>What we collect</h2><p>LYRAVOX does not run analytics, advertising or tracking scripts and sets no cookies. Your language choice is stored locally.</p>
<h2>Third parties</h2><ul><li><strong>Google Fonts</strong>: fonts are requested from fonts.googleapis.com / fonts.gstatic.com when needed. Google receives a standard web request (such as your IP address and browser details) under its own privacy policy.</li><li><strong>AI server</strong>: see the AI Generate Lyrics section above; it is hosted separately (for example on Render), which may keep ordinary server logs.</li><li><strong>Hosting</strong>: the site is served by a static host (for example Vercel), which may keep ordinary server logs.</li><li>Links to Facebook, Instagram, WhatsApp, email and the developer's portfolio lead to services with their own policies.</li></ul>
<h2>Your control</h2><p>You can delete projects, songs and export history from the Studio, or clear all site data in your browser settings. Exported files are saved by your browser to your own device.</p>
<h2>Contact</h2><p>Questions: <a href="mailto:{DEV["mail"]}">{DEV["mail"]}</a>.</p>''', f'''<p><em>সর্বশেষ হালনাগাদ: {UPDATED}</em></p><p>LYRAVOX এমনভাবে বানানো যাতে আপনার সৃজনশীল কাজ কখনো আপনার ডিভাইস ছেড়ে না যায়।</p>
<h2>যা আপনার ডিভাইসেই থাকে</h2><p>লিরিক্স, গান, প্রজেক্ট, থাম্বনেইল ও এক্সপোর্ট ইতিহাস শুধু আপনার ব্রাউজারে (IndexedDB ও localStorage) প্রসেস ও সংরক্ষিত হয়। নিচে বর্ণিত ঐচ্ছিক AI ফিচার ছাড়া এগুলো কোথাও আপলোড হয় না, আর LYRAVOX-এর কোনো অ্যাকাউন্ট নেই। ব্রাউজারের সাইট ডেটা মুছলে এগুলোও মুছে যায়।</p>
<h2>AI দিয়ে লিরিক্স (ঐচ্ছিক)</h2><p>এটিই একমাত্র ফিচার যা আপনার অডিও নেটওয়ার্কে পাঠায়। <em>লিরিক্স তৈরি করুন</em> চাপলে গান (বা আপনার বাছা অংশ) সাইটে কনফিগার করা (বা আপনার ডায়ালগে দেওয়া) LYRAVOX AI সার্ভারে আপলোড হয় এবং সেখানে লেখায় রূপান্তরিত হয়। সার্ভার আপলোডটি শুধু প্রসেসিংয়ের সময় রাখে এবং কাজ শেষ হওয়া মাত্র (সম্পন্ন, ব্যর্থ বা বাতিল) তা ও তার থেকে তৈরি সব ফাইল মুছে ফেলে। ফলাফল লিরিক্স অল্প সময় (ডিফল্ট ৩০ মিনিট) সার্ভারের মেমরিতে থাকে যাতে আপনার ব্রাউজার তা নিতে পারে, তারপর ভুলে যাওয়া হয়। নিজের সার্ভার চালালে সবকিছু আপনার নিয়ন্ত্রণে; অন্যের সার্ভার ব্যবহার করলে তাদের নীতি প্রযোজ্য। যে অডিও শেয়ার করার অধিকার আপনার নেই তা আপলোড করবেন না।</p>
<h2>আমরা কী সংগ্রহ করি</h2><p>LYRAVOX কোনো অ্যানালিটিক্স, বিজ্ঞাপন বা ট্র্যাকিং স্ক্রিপ্ট চালায় না এবং কুকি সেট করে না। আপনার ভাষার পছন্দ লোকালি রাখা হয়।</p>
<h2>তৃতীয় পক্ষ</h2><ul><li><strong>Google Fonts</strong>: প্রয়োজনে fonts.googleapis.com / fonts.gstatic.com থেকে ফন্ট চাওয়া হয়। Google একটি সাধারণ ওয়েব অনুরোধ (যেমন আপনার IP ও ব্রাউজারের তথ্য) পায়, তাদের নিজস্ব গোপনীয়তা নীতির অধীনে।</li><li><strong>AI সার্ভার</strong>: উপরের AI লিরিক্স অংশ দেখুন; এটি আলাদাভাবে (যেমন Render-এ) হোস্ট করা, যারা সাধারণ সার্ভার লগ রাখতে পারে।</li><li><strong>হোস্টিং</strong>: সাইটটি একটি স্ট্যাটিক হোস্ট (যেমন Vercel) থেকে পরিবেশিত, যারা সাধারণ সার্ভার লগ রাখতে পারে।</li><li>Facebook, Instagram, WhatsApp, ইমেইল ও ডেভেলপারের পোর্টফোলিওর লিংক এমন সেবায় নিয়ে যায় যাদের নিজস্ব নীতি আছে।</li></ul>
<h2>আপনার নিয়ন্ত্রণ</h2><p>স্টুডিও থেকে প্রজেক্ট, গান ও এক্সপোর্ট ইতিহাস মুছতে পারেন, অথবা ব্রাউজার সেটিংসে সব সাইট ডেটা মুছতে পারেন। এক্সপোর্ট করা ফাইল আপনার ব্রাউজার আপনার নিজের ডিভাইসে সেভ করে।</p>
<h2>যোগাযোগ</h2><p>প্রশ্ন: <a href="mailto:{DEV["mail"]}">{DEV["mail"]}</a>।</p>'''))

def terms():
    return page('Terms of Use', 'ব্যবহারের শর্ত', tb(f'''<p><em>Last updated: {UPDATED}</em></p>
<h2>1. Using LYRAVOX</h2><p>LYRAVOX is free to use. By using it you agree to these terms. The software is released under the MIT License (see <a href="../credits/">Credits &amp; licenses</a>); these terms cover use of the hosted website.</p>
<h2>2. Your content and your responsibility</h2><p>You own the videos and images you export. You are responsible for having the right to use the lyrics, music, fonts and any other material you put into a project. LYRAVOX does not check rights and does not claim any right in your content.</p>
<h2>2a. AI-generated lyrics</h2><p>Lyrics produced by AI Generate Lyrics are machine transcriptions. They can be wrong or incomplete (singing, accents, background music and Bangla or Hindi are especially hard), may contain words that are not in the recording, and must be checked by you. The transcription of copyrighted songs does not grant you any right to them.</p>
<h2>3. Acceptable use</h2><p>Do not use LYRAVOX to infringe other people's rights or to create unlawful content.</p>
<h2>4. No warranty</h2><p>The service is provided "as is", without warranty of any kind. Video export depends on your browser and device (Chrome or Edge recommended); very long or very high-resolution exports can run out of memory. Projects are stored only in your browser, so keep backups with the .json export.</p>
<h2>5. Liability</h2><p>To the extent permitted by law, {DEV["org"]} and the developer are not liable for any loss arising from the use of LYRAVOX, including lost projects.</p>
<h2>6. Changes and contact</h2><p>These terms may be updated; the date above shows the latest version. Contact: <a href="mailto:{DEV["mail"]}">{DEV["mail"]}</a>.</p>''', f'''<p><em>সর্বশেষ হালনাগাদ: {UPDATED}</em></p>
<h2>১. LYRAVOX ব্যবহার</h2><p>LYRAVOX ব্যবহার বিনামূল্যে। ব্যবহার করলে আপনি এই শর্তে সম্মত হচ্ছেন। সফটওয়্যারটি MIT লাইসেন্সে প্রকাশিত (দেখুন <a href="../credits/">ক্রেডিট ও লাইসেন্স</a>); এই শর্ত হোস্ট করা ওয়েবসাইট ব্যবহারের জন্য।</p>
<h2>২. আপনার কনটেন্ট ও দায়িত্ব</h2><p>আপনার এক্সপোর্ট করা ভিডিও ও ছবির মালিক আপনি। প্রজেক্টে যে লিরিক্স, গান, ফন্ট বা অন্য উপাদান দেন তা ব্যবহারের অধিকার আছে কিনা তা নিশ্চিত করা আপনার দায়িত্ব। LYRAVOX অধিকার যাচাই করে না এবং আপনার কনটেন্টে কোনো অধিকার দাবি করে না।</p>
<h2>২ক. AI-তৈরি লিরিক্স</h2><p>AI দিয়ে লিরিক্স ফিচারের তৈরি লিরিক্স যন্ত্রের করা লেখা। এতে ভুল বা ঘাটতি থাকতে পারে (গান, উচ্চারণ, ব্যাকগ্রাউন্ড মিউজিক এবং বিশেষত বাংলা বা হিন্দি কঠিন), রেকর্ডিংয়ে নেই এমন শব্দ আসতে পারে, এবং আপনাকেই তা যাচাই করতে হবে। কপিরাইটযুক্ত গানের লেখা বের করলেই তাতে আপনার কোনো অধিকার জন্মায় না।</p>
<h2>৩. গ্রহণযোগ্য ব্যবহার</h2><p>অন্যের অধিকার লঙ্ঘন বা বেআইনি কনটেন্ট বানাতে LYRAVOX ব্যবহার করবেন না।</p>
<h2>৪. কোনো ওয়ারেন্টি নেই</h2><p>সেবাটি "যেমন আছে" ভিত্তিতে দেওয়া, কোনো ধরনের ওয়ারেন্টি ছাড়া। ভিডিও এক্সপোর্ট আপনার ব্রাউজার ও ডিভাইসের উপর নির্ভর করে (Chrome বা Edge সুপারিশ করা হয়); খুব লম্বা বা খুব উচ্চ রেজোলিউশনের এক্সপোর্টে মেমরি শেষ হতে পারে। প্রজেক্ট শুধু আপনার ব্রাউজারে থাকে, তাই .json এক্সপোর্টে ব্যাকআপ রাখুন।</p>
<h2>৫. দায়বদ্ধতা</h2><p>আইনে যতটুকু অনুমোদিত, LYRAVOX ব্যবহারের ফলে কোনো ক্ষতির (হারানো প্রজেক্টসহ) জন্য {DEV["org"]} ও ডেভেলপার দায়ী নয়।</p>
<h2>৬. পরিবর্তন ও যোগাযোগ</h2><p>এই শর্ত হালনাগাদ হতে পারে; উপরের তারিখ সর্বশেষ সংস্করণ দেখায়। যোগাযোগ: <a href="mailto:{DEV["mail"]}">{DEV["mail"]}</a>।</p>'''))

def contact():
    items = [('✉️ Email', 'mailto:' + DEV['mail'], DEV['mail']), ('💬 WhatsApp', 'https://wa.me/' + DEV['wa_intl'], DEV['wa']), ('📞 ' + 'Phone', 'tel:' + DEV['phone'], DEV['phone']),
             ('🌐 Portfolio', DEV['portfolio'], DEV['portfolio']), ('📘 Facebook', DEV['fb'], DEV['fb']), ('📸 Instagram', DEV['ig'], DEV['ig'])]
    cards = ''.join(f'<a class="card" href="{u}"' + (' target="_blank" rel="noopener"' if u.startswith('http') else '') + f'><h3>{n}</h3><small>{s}</small></a>' for n, u, s in items)
    return f'''<div class="wrap page"><h1>{t("Contact", "যোগাযোগ")}</h1><p style="color:var(--muted);max-width:40em">{t("Bug reports, ideas or collaboration: reach the developer through any channel below. Email is best for bug reports; please mention your browser and device.", "বাগ রিপোর্ট, আইডিয়া বা সহযোগিতার জন্য নিচের যেকোনো মাধ্যমে ডেভেলপারের সাথে যোগাযোগ করুন। বাগ রিপোর্টে ইমেইল সবচেয়ে ভালো; ব্রাউজার ও ডিভাইসের নাম জানাবেন।")}</p>
<div class="ctc" style="margin-top:24px">{cards}</div><p style="margin-top:28px;color:var(--muted)">{DEV["name"]} · {DEV["org"]} · {t("Bangladesh", "বাংলাদেশ")}</p></div>'''

def nf(rel):
    return f'''<div class="wrap nf"><div><h1 class="grad">404</h1><h2>{t("This page drifted off the timeline.", "এই পেজটি টাইমলাইন থেকে হারিয়ে গেছে।")}</h2><p style="color:var(--muted)">{t("The page you are looking for does not exist or has moved.", "আপনি যে পেজ খুঁজছেন তা নেই বা সরে গেছে।")}</p><div class="cta" style="margin-top:20px"><a class="btn pri" href="{rel}">{t("Back to home", "হোমে ফিরুন")}</a><a class="btn" data-editor href="{rel}editor/">{t("Open Editor", "এডিটর খুলুন")}</a></div></div></div>'''

def build(public, ver, site, editions):
    def w(path, s):
        p = os.path.join(public, path); os.makedirs(os.path.dirname(p), exist_ok=True); open(p, 'w', encoding='utf-8').write(s)
    S = lambda rel, slug, te, tbn, de, dbn, body, **k: shell(rel, slug, te, tbn, de, dbn, body, site, ver, **k)
    w('index.html', S('', '', 'LYRAVOX — Lyric Motion Video Studio | Turn Every Lyric Into a Visual Story', 'LYRAVOX — লিরিক মোশন ভিডিও স্টুডিও | প্রতিটি লিরিক্সকে বানান দৃশ্যকাহিনি',
                      'Create lyric motion videos in your browser: beat detection, tap-to-sync timeline, 860 motion components, MP4 and PNG export, English and Bangla. Free, no account, no upload.', 'ব্রাউজারেই লিরিক মোশন ভিডিও বানান।', landing('', site, ver), cur=''))
    w('studio/index.html', S('../', 'studio', 'Studio — Projects, Audio Library, Lyrics Studio | LYRAVOX', 'স্টুডিও — প্রজেক্ট, অডিও লাইব্রেরি, লিরিক্স স্টুডিও | LYRAVOX',
                             'Your LYRAVOX Studio: recent projects, project import, audio library, lyrics studio and export history, all stored in your browser.', 'প্রজেক্ট, অডিও লাইব্রেরি, লিরিক্স স্টুডিও ও এক্সপোর্ট ইতিহাস।', studio('../', site, ver), cur='studio'))
    pages = [('about', 'About LYRAVOX', 'LYRAVOX সম্পর্কে', 'What LYRAVOX is, what it does and where it comes from.', 'LYRAVOX কী, কী করে ও কোথা থেকে এসেছে।', about()),
             ('developer', 'About the Developer — Prince AR Abdur Rahman', 'ডেভেলপার — প্রিন্স এআর আব্দুর রহমান', 'Prince AR Abdur Rahman, founder of NexVora Lab\'s Ofc, Bangladesh. Portfolio and contact links.', 'প্রিন্স এআর আব্দুর রহমান, NexVora Lab\'s Ofc-এর প্রতিষ্ঠাতা, বাংলাদেশ।', developer()),
             ('credits', 'Credits & Licenses', 'ক্রেডিট ও লাইসেন্স', 'About LYRAVOX, NexVora Lab\'s Ofc, original JIZURA attribution, MIT license and third-party notices.', 'LYRAVOX, NexVora Lab\'s Ofc, মূল JIZURA-র স্বীকৃতি, MIT লাইসেন্স ও থার্ড-পার্টি নোটিস।', credits(ver)),
             ('privacy', 'Privacy Policy', 'গোপনীয়তা নীতি', 'LYRAVOX keeps your lyrics, songs and projects in your browser. No accounts, no tracking.', 'LYRAVOX আপনার লিরিক্স, গান ও প্রজেক্ট ব্রাউজারেই রাখে।', privacy()),
             ('terms', 'Terms of Use', 'ব্যবহারের শর্ত', 'Terms for using the LYRAVOX website and editor.', 'LYRAVOX ওয়েবসাইট ও এডিটর ব্যবহারের শর্ত।', terms()),
             ('contact', 'Contact', 'যোগাযোগ', 'Contact the LYRAVOX developer by email, WhatsApp, phone or social media.', 'ইমেইল, WhatsApp, ফোন বা সোশ্যাল মিডিয়ায় যোগাযোগ করুন।', contact())]
    for slug, te, tbn, de, dbn, body in pages:
        w(f'{slug}/index.html', S('../', slug, te + ' | LYRAVOX', tbn + ' | LYRAVOX', de, dbn, body, cur=slug))
    w('404.html', S('/', '404', 'Page not found | LYRAVOX', 'পেজ পাওয়া যায়নি | LYRAVOX', 'The page you are looking for does not exist.', 'আপনি যে পেজ খুঁজছেন তা নেই।', nf('/')))
    # assets: css/js/png/svg
    os.makedirs(os.path.join(public, 'assets'), exist_ok=True)
    for f in os.listdir(os.path.join(HERE, 'assets')):
        dest = os.path.join(public, 'assets', f) if (f.endswith(('.css', '.js')) and f != 'config.js') else os.path.join(public, f)
        shutil.copy(os.path.join(HERE, 'assets', f), dest)
    env_api = os.environ.get('LYRAVOX_API_URL', '').strip().rstrip('/')
    if env_api:                                              # build-time override of the backend address
        with open(os.path.join(public, 'config.js'), 'w', encoding='utf-8') as fh:
            fh.write('window.LYRAVOX_CONFIG = { apiUrl: %s };\n' % json.dumps(env_api))
    for f in ('store.js', 'aigen.js', 'aigen.css'):
        shutil.copy(os.path.join(HERE, '..', 'app', f), os.path.join(public, 'assets', f))
    for f in ('LICENSE', 'THIRD_PARTY_NOTICES.md'):
        shutil.copy(os.path.join(HERE, '..', f), os.path.join(public, f if f != 'LICENSE' else 'LICENSE.txt'))
    w('manifest.webmanifest', json.dumps({"name": "LYRAVOX", "short_name": "LYRAVOX", "description": "Lyric motion video studio", "start_url": "/studio/", "scope": "/", "display": "standalone",
                                          "background_color": "#060913", "theme_color": "#060913", "icons": [{"src": "/icon-192.png", "sizes": "192x192", "type": "image/png"}, {"src": "/icon-512.png", "sizes": "512x512", "type": "image/png"}, {"src": "/favicon.svg", "sizes": "any", "type": "image/svg+xml"}]}, indent=1))
    urls = ['', 'studio/', 'about/', 'developer/', 'credits/', 'contact/', 'privacy/', 'terms/'] + ['editor/' + (f + '/' if f else '') for f, _, _ in editions]
    today = datetime.date.today().isoformat()
    w('sitemap.xml', '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + ''.join(f'  <url><loc>{site}{u}</loc><lastmod>{today}</lastmod><priority>{"1.0" if u == "" else "0.8" if u.startswith(("studio", "editor/")) and u in ("studio/", "editor/", "editor/bn/") else "0.5"}</priority></url>\n' for u in urls) + '</urlset>\n')
    w('robots.txt', f'User-agent: *\nAllow: /\nSitemap: {site}sitemap.xml\n')
