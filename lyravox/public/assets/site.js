(function(){
'use strict';
var de=document.documentElement;
function lang(){return de.getAttribute('data-lang')==='bn'?'bn':'en';}
function root(){return (document.currentScript&&0)||window.LV_ROOT||'';}
function apply(l){
  de.setAttribute('data-lang',l);de.lang=l;
  try{localStorage.setItem('lyravox.lang',l);}catch(e){}
  var t=document.documentElement.getAttribute('data-title-'+l);if(t)document.title=t;
  [].forEach.call(document.querySelectorAll('.lang button'),function(b){b.setAttribute('aria-pressed',b.dataset.l===l?'true':'false');});
  [].forEach.call(document.querySelectorAll('[data-editor]'),function(a){a.href=root()+(l==='bn'?'editor/bn/':'editor/');});
  document.dispatchEvent(new CustomEvent('lv-lang',{detail:l}));
}
document.addEventListener('DOMContentLoaded',function(){
  [].forEach.call(document.querySelectorAll('.lang button'),function(b){b.addEventListener('click',function(){apply(b.dataset.l);});});
  var mb=document.querySelector('.menu-btn'),nv=document.querySelector('.nav');
  if(mb&&nv)mb.addEventListener('click',function(){var o=nv.classList.toggle('open');mb.setAttribute('aria-expanded',o);});
  apply(lang());
  var bg=document.getElementById('bgtype');
  if(bg&&!matchMedia('(prefers-reduced-motion: reduce)').matches){
    var words=['Turn Every Lyric','Beat','Motion','Kinetic','Typography','860 parts','ভালোবাসি','আকাশ','স্বপ্ন','সুর','ছন্দ','গান','Visual Story','Neon','Glitch','Rhythm','বাংলা','আলো'];
    var n=matchMedia('(max-width:700px)').matches?12:22;
    for(var i=0;i<n;i++){var s=document.createElement('span');s.textContent=words[i%words.length];
      var sz=28+Math.random()*90;s.style.cssText='font-size:'+sz+'px;top:'+(Math.random()*95)+'%;left:0;--x0:'+(Math.random()*60-10)+'vw;--x1:'+(40+Math.random()*60)+'vw;animation-duration:'+(14+Math.random()*22)+'s;animation-delay:'+(-Math.random()*30)+'s';
      bg.appendChild(s);}
  }
});
})();
