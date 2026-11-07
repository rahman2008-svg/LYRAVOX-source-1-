(function(){
'use strict';
var LV=window.LVStore,$=function(i){return document.getElementById(i);};
var D={en:{
 untitled:'Untitled',open:'Open',rename:'Rename',dup:'Duplicate',exp:'Export .json',del:'Delete',lines:'lines',noProj:'No projects yet. Create one or import a project file.',
 newName:'Project name',confirmDel:'Delete this project? This cannot be undone.',copy:' (copy)',imported:'Project imported',badFile:'This is not a LYRAVOX / JIZURA project file',
 updated:'Updated',noAudio:'No songs yet. Upload one or open a project that has a song.',play:'Play',use:'New project with this song',dl:'Download',audioAdded:'Song added',confirmAudio:'Remove this song from the library? Projects keep working but must load the song again.',
 noExp:'No exports yet. Export a video, PNG ZIP, LRC or AE data from the editor and it appears here.',clear:'Clear history',confirmClear:'Clear the whole export history? (Your downloaded files are not touched.)',
 date:'Date',project:'Project',format:'Format',size:'Size',details:'Details',
 lrcRead:'LRC file loaded',cleaned:'Cleaned',stamped:'Timestamps added',stripped:'Timestamps removed',noLyrics:'Write or paste some lyrics first',draftSaved:'Draft saved',noDrafts:'No drafts yet',
 chars:'characters',detected:'Detected language',auto:'Auto',saved:'Saved',deleted:'Deleted',err:'Something went wrong: ',noStore:'This browser blocks local storage, so projects cannot be kept. Try a normal (non-private) window.',
 secsPerLine:'Seconds between lines',min:'min',sec:'s',load:'Load',drafts:'Drafts'
},bn:{
 untitled:'নামহীন',open:'খুলুন',rename:'নাম বদলান',dup:'ডুপ্লিকেট',exp:'.json এক্সপোর্ট',del:'মুছুন',lines:'লাইন',noProj:'এখনও কোনো প্রজেক্ট নেই। নতুন বানান অথবা প্রজেক্ট ফাইল ইমপোর্ট করুন।',
 newName:'প্রজেক্টের নাম',confirmDel:'এই প্রজেক্ট মুছবেন? এটি ফেরানো যাবে না।',copy:' (কপি)',imported:'প্রজেক্ট ইমপোর্ট হয়েছে',badFile:'এটি LYRAVOX / JIZURA প্রজেক্ট ফাইল নয়',
 updated:'হালনাগাদ',noAudio:'এখনও কোনো গান নেই। গান আপলোড করুন বা গানসহ প্রজেক্ট খুলুন।',play:'চালান',use:'এই গান দিয়ে নতুন প্রজেক্ট',dl:'ডাউনলোড',audioAdded:'গান যোগ হয়েছে',confirmAudio:'লাইব্রেরি থেকে এই গান সরাবেন? প্রজেক্ট চলবে, তবে গান আবার লোড করতে হবে।',
 noExp:'এখনও কোনো এক্সপোর্ট নেই। এডিটর থেকে ভিডিও, PNG ZIP, LRC বা AE ডেটা এক্সপোর্ট করলে এখানে দেখা যাবে।',clear:'ইতিহাস মুছুন',confirmClear:'পুরো এক্সপোর্ট ইতিহাস মুছবেন? (ডাউনলোড করা ফাইল অক্ষত থাকবে।)',
 date:'তারিখ',project:'প্রজেক্ট',format:'ফরম্যাট',size:'আকার',details:'বিবরণ',
 lrcRead:'LRC ফাইল লোড হয়েছে',cleaned:'পরিষ্কার হয়েছে',stamped:'টাইমস্ট্যাম্প যোগ হয়েছে',stripped:'টাইমস্ট্যাম্প সরানো হয়েছে',noLyrics:'আগে কিছু লিরিক্স লিখুন বা পেস্ট করুন',draftSaved:'ড্রাফট সেভ হয়েছে',noDrafts:'এখনও কোনো ড্রাফট নেই',
 chars:'অক্ষর',detected:'শনাক্ত ভাষা',auto:'স্বয়ংক্রিয়',saved:'সেভ হয়েছে',deleted:'মুছে গেছে',err:'সমস্যা হয়েছে: ',noStore:'এই ব্রাউজার লোকাল স্টোরেজ আটকে দিচ্ছে, তাই প্রজেক্ট রাখা যাচ্ছে না। সাধারণ (প্রাইভেট নয়) উইন্ডো চেষ্টা করুন।',
 secsPerLine:'দুই লাইনের মাঝে সেকেন্ড',min:'মি.',sec:'সে.',load:'লোড',drafts:'ড্রাফট'
}};
function L(){return document.documentElement.getAttribute('data-lang')==='bn'?'bn':'en';}
function t(k){return D[L()][k]||D.en[k]||k;}
function esc(s){return String(s==null?'':s).replace(/[&<>"']/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c];});}
var toastT;function toast(m){var e=$('toast');e.textContent=m;e.classList.add('on');clearTimeout(toastT);toastT=setTimeout(function(){e.classList.remove('on');},3200);}
function fmtDate(ts){try{return new Date(ts).toLocaleString(L()==='bn'?'bn-BD':'en-GB',{dateStyle:'medium',timeStyle:'short'});}catch(e){return new Date(ts).toLocaleString();}}
function dl(name,blob){var u=URL.createObjectURL(blob),a=document.createElement('a');a.href=u;a.download=name;document.body.appendChild(a);a.click();a.remove();setTimeout(function(){URL.revokeObjectURL(u);},20000);}
function safe(n){return String(n||'lyravox').replace(/[\\/:*?"<>|]+/g,'_').slice(0,60)||'lyravox';}
function fail(e){console.error(e);toast(t('err')+(e&&e.message?e.message:e));}

/* ---- tabs ---- */
var tabs=['projects','audio','lyrics','exports'];
function show(name){
  if(tabs.indexOf(name)<0)name='projects';
  tabs.forEach(function(n){$('pane-'+n).hidden=n!==name;$('tab-'+n).setAttribute('aria-selected',n===name?'true':'false');});
  if(location.hash.slice(1)!==name)history.replaceState(null,'','#'+name);
  if(name==='projects')renderProjects();if(name==='audio')renderAudio();if(name==='exports')renderExports();if(name==='lyrics')renderDrafts();
}

/* ---- projects ---- */
var projCache=[];
async function renderProjects(){
  var list=await LV.projects.list();projCache=list;
  $('cnt-projects').textContent=list.length;
  var q=($('pq').value||'').toLowerCase(),sort=$('psort').value;
  list=list.filter(function(r){return !q||((r.title||'')+' '+(r.artist||'')).toLowerCase().indexOf(q)>=0;});
  list.sort(function(a,b){return sort==='name'?String(a.title).localeCompare(String(b.title)):b.updated-a.updated;});
  var h='<button class="new" id="newCard" type="button"><span><b>+</b>'+esc(L()==='bn'?'নতুন প্রজেক্ট':'Create New Project')+'</span></button>';
  list.forEach(function(r){
    var th=r.thumb?'style="background-image:url('+esc(r.thumb)+')"':'';
    h+='<article class="proj" data-id="'+esc(r.id)+'"><div class="th" '+th+' data-act="open">'+(r.thumb?'':'♪')+'</div><div class="b"><h4>'+esc(r.title||t('untitled'))+'</h4>'+
      '<div class="m">'+esc(r.artist?r.artist+' · ':'')+(r.lines||0)+' '+t('lines')+(r.duration?' · '+LV.fmtTime(r.duration):'')+(r.lang&&r.lang!=='auto'?' · '+esc(r.lang):'')+'</div>'+
      '<div class="m">'+t('updated')+' '+esc(fmtDate(r.updated))+'</div><div class="a">'+
      '<button class="btn sm pri" data-act="open">'+t('open')+'</button><button class="btn sm" data-act="rename">'+t('rename')+'</button><button class="btn sm" data-act="dup">'+t('dup')+'</button><button class="btn sm" data-act="exp">'+t('exp')+'</button><button class="btn sm danger" data-act="del">'+t('del')+'</button></div></div></article>';
  });
  $('pgrid').innerHTML=h;
  if(!projCache.length)$('pempty').hidden=false;else $('pempty').hidden=true;
}
async function projAction(act,id){
  var r=await LV.projects.get(id);if(!r)return;
  if(act==='open')return LV.openInEditor(id);
  if(act==='rename'){var n=prompt(t('newName'),r.title||'');if(n==null)return;r.title=n.trim();r.project.title=r.title;await LV.projects.put(r);toast(t('saved'));return renderProjects();}
  if(act==='dup'){var c=JSON.parse(JSON.stringify(r));c.id=LV.uid();c.title=(r.title||t('untitled'))+t('copy');c.project.title=c.title;c.created=c.updated=Date.now();await LV.projects.put(c);toast(t('saved'));return renderProjects();}
  if(act==='exp'){var p=Object.assign({},r.project);dl(safe(r.title)+'.lyravox.json',new Blob([JSON.stringify(p,null,1)],{type:'application/json'}));return;}
  if(act==='del'){if(!confirm(t('confirmDel')))return;await LV.projects.delete(id);toast(t('deleted'));return renderProjects();}
}
async function importFile(f){
  try{
    if(f.size>20*1048576)throw new Error('File too large');
    var j=JSON.parse(await f.text());
    if(j&&j.project&&typeof j.project==='object'&&typeof j.project.lyrics==='string')j=j.project;
    if(!j||typeof j!=='object'||Array.isArray(j)||typeof j.lyrics!=='string'){toast(t('badFile'));return;}
    var rec=LV.makeRecord(j,{title:j.title||f.name.replace(/\.(lyravox|jizura)?\.?json$/i,'')});
    await LV.projects.put(rec);toast(t('imported'));await renderProjects();
  }catch(e){toast(t('badFile'));console.warn(e);}
}

/* ---- audio ---- */
function audioDuration(file){return new Promise(function(res){var a=new Audio(),u=URL.createObjectURL(file);a.preload='metadata';a.onloadedmetadata=function(){var d=a.duration;URL.revokeObjectURL(u);res(isFinite(d)?d:0);};a.onerror=function(){URL.revokeObjectURL(u);res(0);};a.src=u;});}
async function renderAudio(){
  var list=await LV.audio.list();list.sort(function(a,b){return (b.added||0)-(a.added||0);});
  $('cnt-audio').textContent=list.length;
  var h='';
  list.forEach(function(a){
    h+='<div class="row" data-id="'+esc(a.id)+'"><span class="nm" title="'+esc(a.name)+'">♪ '+esc(a.name)+'</span><span class="mt">'+LV.fmtTime(a.duration)+' · '+LV.fmtBytes(a.size)+(a.bpm?' · '+Math.round(a.bpm)+' BPM':'')+'</span>'+
     '<button class="btn sm" data-act="play">'+t('play')+'</button><button class="btn sm pri" data-act="ai">✨ '+esc(LVAI.t('btn'))+'</button><button class="btn sm" data-act="use">'+t('use')+'</button><button class="btn sm" data-act="dl">'+t('dl')+'</button><button class="btn sm danger" data-act="del">'+t('del')+'</button></div>';
  });
  $('alist').innerHTML=h;$('aempty').hidden=list.length>0;
}
var player=null,playerUrl='';
async function audioAction(act,id){
  var a=await LV.audio.get(id);if(!a)return;
  if(act==='play'){if(player){player.pause();URL.revokeObjectURL(playerUrl);}playerUrl=URL.createObjectURL(a.data);player=new Audio(playerUrl);player.play().catch(fail);return;}
  if(act==='ai')return openAI(new File([a.data],a.name,{type:a.type}),id);
  if(act==='use')return LV.createAndOpen({audioId:id,title:a.name.replace(/\.[^.]+$/,'')});
  if(act==='dl')return dl(a.name,a.data);
  if(act==='del'){if(!confirm(t('confirmAudio')))return;await LV.audio.delete(id);toast(t('deleted'));renderAudio();}
}
async function addAudio(f){
  if(!f)return '';
  var id='a_'+Math.abs([].reduce.call(f.name+'|'+f.size,function(h,c){return ((h<<5)-h+c.charCodeAt(0))|0;},0)).toString(36);
  var d=await audioDuration(f);
  await LV.audio.put({id:id,name:f.name,type:f.type,size:f.size,duration:d,bpm:0,added:Date.now(),data:f});
  toast(t('audioAdded'));renderAudio();return id;
}

/* ---- export history ---- */
var FMT={mp4:'MP4','png-zip':'PNG ZIP','png-alpha-zip':'PNG ZIP (alpha)','png-layers-zip':'PNG ZIP (layers)',lrc:'LRC','ae-json':'AE JSON'};
async function renderExports(){
  var list=await LV.exports.list();list.sort(function(a,b){return b.at-a.at;});
  $('cnt-exports').textContent=list.length;
  var h='';
  list.forEach(function(e){
    var det=[e.res&&(e.format==='mp4'||/png/.test(e.format))?e.res+'p':'',e.aspect||'',e.fps&&e.format==='mp4'?e.fps+' fps':'',e.codec||'',e.audio?e.audio.toUpperCase():'',e.secs?Math.round(e.secs)+t('sec'):'',e.direct?'direct-to-file':''].filter(Boolean).join(' · ');
    h+='<tr><td>'+esc(fmtDate(e.at))+'</td><td>'+esc(e.title||e.name||'')+'</td><td>'+esc(FMT[e.format]||e.format)+'</td><td>'+LV.fmtBytes(e.size)+'</td><td>'+esc(det)+'</td><td><button class="btn sm danger" data-id="'+esc(e.id)+'">'+t('del')+'</button></td></tr>';
  });
  $('ebody').innerHTML=h;$('eempty').hidden=list.length>0;$('etable').hidden=!list.length;$('eclear').hidden=!list.length;
}

/* ---- lyrics studio ---- */
var TS=/\[\d{1,3}:\d{2}(?:[.:]\d{1,3})?\]/g;
function detect(s){var bn=0,la=0,cjk=0;for(var i=0;i<s.length;i++){var c=s.charCodeAt(i);if(c>=0x980&&c<=0x9ff)bn++;else if((c>=65&&c<=90)||(c>=97&&c<=122))la++;else if(c>=0x3040&&c<=0x9fff||c>=0xac00&&c<=0xd7a3)cjk++;}
  if(!bn&&!la&&!cjk)return '—';if(bn>=la&&bn>=cjk)return 'বাংলা';if(cjk>la)return 'CJK';return 'English';}
function stats(){var s=$('lyr').value;var lines=s.split('\n').filter(function(l){return l.replace(TS,'').trim();}).length;
  $('lstats').textContent=lines+' '+t('lines')+' · '+s.length+' '+t('chars')+' · '+t('detected')+': '+detect(s);
  try{localStorage.setItem('lyravox.studio.lyrics',s);}catch(e){}}
function mmss(sec){var m=Math.floor(sec/60),s=sec-m*60;return '['+String(m).padStart(2,'0')+':'+(s<10?'0':'')+s.toFixed(2)+']';}
function drafts(){try{return JSON.parse(localStorage.getItem('lyravox.studio.drafts')||'[]');}catch(e){return [];}}
function renderDrafts(){var d=drafts(),h='';d.forEach(function(x,i){h+='<div class="draft"><span>'+esc(x.title||t('untitled'))+' · '+esc(fmtDate(x.at))+'</span><button class="btn sm" data-i="'+i+'" data-a="load">'+t('load')+'</button><button class="btn sm danger" data-i="'+i+'" data-a="del">'+t('del')+'</button></div>';});$('drafts').innerHTML=h||'<p class="mt" style="color:var(--muted)">'+t('noDrafts')+'</p>';}

/* ---- AI Generate Lyrics ---- */
function openAI(file,audioId){
  if(!window.LVAI)return toast('AI module not loaded');
  var ly=$('lyr');
  var title=file.name.replace(/\.[^.]+$/,'');
  LVAI.open({file:file,host:{
    title:title,toast:toast,hasLyrics:function(){return false;},
    apply:async function(r){
      if(r.mode==='replace'){
        var aid=audioId||await addAudio(file);
        await LV.createAndOpen({lyrics:r.text,title:title,audioId:aid});return true;
      }
      ly.value=(ly.value.replace(/\s+$/,'')+'\n'+r.text).replace(/^\n/,'');$('ltitle').value=$('ltitle').value||title;stats();return true;
    },
    studio:function(r){show('lyrics');ly.value=r.text;$('ltitle').value=$('ltitle').value||title;stats();toast(t('saved'));}
  }});
}
async function boot(){
  if(!LV){document.body.insertAdjacentHTML('afterbegin','<p style="padding:20px">Library unavailable</p>');return;}
  try{await LV.open();}catch(e){toast(t('noStore'));}
  tabs.forEach(function(n){$('tab-'+n).addEventListener('click',function(){show(n);});});
  $('pq').addEventListener('input',renderProjects);$('psort').addEventListener('change',renderProjects);
  $('pgrid').addEventListener('click',function(e){
    if(e.target.closest('#newCard'))return LV.createAndOpen({}).catch(fail);
    var b=e.target.closest('[data-act]');if(!b)return;var card=b.closest('.proj');projAction(b.dataset.act,card.dataset.id).catch(fail);});
  $('btnNew').addEventListener('click',function(){LV.createAndOpen({}).catch(fail);});
  $('pimport').addEventListener('change',function(e){[].forEach.call(e.target.files,importFile);e.target.value='';});
  var dz=$('drop');['dragenter','dragover'].forEach(function(n){dz.addEventListener(n,function(e){e.preventDefault();dz.classList.add('on');});});
  ['dragleave','drop'].forEach(function(n){dz.addEventListener(n,function(e){e.preventDefault();dz.classList.remove('on');});});
  dz.addEventListener('drop',function(e){[].forEach.call(e.dataTransfer.files,importFile);});
  $('alist').addEventListener('click',function(e){var b=e.target.closest('[data-act]');if(b)audioAction(b.dataset.act,b.closest('.row').dataset.id).catch(fail);});
  ['aifile','aifile2'].forEach(function(id){var e=$(id);if(e)e.addEventListener('change',function(ev){var f=ev.target.files[0];ev.target.value='';if(f)openAI(f,'');});});
  $('afile').addEventListener('change',function(e){[].forEach.call(e.target.files,function(f){addAudio(f).catch(fail);});e.target.value='';});
  $('ebody').addEventListener('click',function(e){var b=e.target.closest('button[data-id]');if(b)LV.exports.delete(b.dataset.id).then(renderExports);});
  $('eclear').addEventListener('click',function(){if(confirm(t('confirmClear')))LV.exports.clear().then(renderExports);});
  // lyrics studio
  var ly=$('lyr');try{ly.value=localStorage.getItem('lyravox.studio.lyrics')||'';}catch(e){}
  ly.addEventListener('input',stats);stats();
  $('lclean').addEventListener('click',function(){ly.value=ly.value.replace(/\r/g,'').split('\n').map(function(l){return l.replace(/[ \t\u00a0]+/g,' ').trim();}).join('\n').replace(/\n{3,}/g,'\n\n').trim();stats();toast(t('cleaned'));});
  $('lstrip').addEventListener('click',function(){ly.value=ly.value.replace(TS,'').split('\n').map(function(l){return l.trim();}).join('\n');stats();toast(t('stripped'));});
  $('lstamp').addEventListener('click',function(){var step=Math.max(0.5,parseFloat($('lstep').value)||4),i=0;
    ly.value=ly.value.replace(TS,'').split('\n').map(function(l){l=l.trim();if(!l)return l;return mmss(i++*step)+l;}).join('\n');stats();toast(t('stamped'));});
  $('lfile').addEventListener('change',async function(e){var f=e.target.files[0];e.target.value='';if(!f)return;if(f.size>2*1048576)return toast('File too large');ly.value=(await f.text()).replace(/^\uFEFF/,'');if(!$('ltitle').value)$('ltitle').value=f.name.replace(/\.[^.]+$/,'');stats();toast(t('lrcRead'));});
  $('ltxt').addEventListener('click',function(){dl(safe($('ltitle').value)+'.txt',new Blob([ly.value.replace(TS,'')],{type:'text/plain;charset=utf-8'}));});
  $('llrc').addEventListener('click',function(){dl(safe($('ltitle').value)+'.lrc',new Blob([ly.value],{type:'text/plain;charset=utf-8'}));});
  $('lsave').addEventListener('click',function(){if(!ly.value.trim())return toast(t('noLyrics'));var d=drafts();d.unshift({title:$('ltitle').value,text:ly.value,at:Date.now()});try{localStorage.setItem('lyravox.studio.drafts',JSON.stringify(d.slice(0,20)));}catch(e){return toast(t('noStore'));}renderDrafts();toast(t('draftSaved'));});
  $('drafts').addEventListener('click',function(e){var b=e.target.closest('button[data-i]');if(!b)return;var d=drafts(),x=d[+b.dataset.i];if(!x)return;if(b.dataset.a==='load'){ly.value=x.text;$('ltitle').value=x.title||'';stats();}else{d.splice(+b.dataset.i,1);localStorage.setItem('lyravox.studio.drafts',JSON.stringify(d));renderDrafts();}});
  $('lopen').addEventListener('click',function(){if(!ly.value.trim())return toast(t('noLyrics'));LV.createAndOpen({lyrics:ly.value,title:$('ltitle').value}).catch(fail);});
  document.addEventListener('lv-lang',function(){stats();var n=location.hash.slice(1);show(tabs.indexOf(n)>=0?n:'projects');});
  show(location.hash.slice(1));
  var o=await LV.projects.list().catch(function(){return [];});$('cnt-projects').textContent=o.length;
  LV.audio.list().then(function(l){$('cnt-audio').textContent=l.length;});LV.exports.list().then(function(l){$('cnt-exports').textContent=l.length;});
}
document.addEventListener('DOMContentLoaded',boot);
})();
