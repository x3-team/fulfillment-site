/* Плавные аккордеоны (услуги и FAQ): высота и отступы анимируются вместе, без рывка в конце */
(function(){
const reduce=matchMedia('(prefers-reduced-motion: reduce)').matches,EASE='cubic-bezier(.22,.8,.24,1)';
const slide=(d,open)=>{const b=d.querySelector('summary').nextElementSibling;d.classList.toggle('on',open);
  if(reduce||!b){d.open=open;return}
  const cs=getComputedStyle(b),h0=d.open?b.offsetHeight:0,t0=d.open?cs.paddingTop:'0px',b0=d.open?cs.paddingBottom:'0px';
  if(d._a){d._a.cancel();d._a=null}
  d.open=true;const nat=getComputedStyle(b),pt=nat.paddingTop,pb=nat.paddingBottom,h1=open?b.offsetHeight:0;
  b.style.overflow='hidden';const a=d._a=b.animate([{height:h0+'px',paddingTop:t0,paddingBottom:b0},{height:h1+'px',paddingTop:open?pt:'0px',paddingBottom:open?pb:'0px'}],{duration:open?460:360,easing:open?EASE:'cubic-bezier(.4,0,.2,1)'});
  a.onfinish=()=>{b.style.overflow='';d._a=null;if(!open)d.open=false};
  a.oncancel=()=>{b.style.overflow=''};};
// single: открыт только один пункт (услуги); иначе пункты независимы (FAQ, чтобы страница не прыгала)
const init=(c,single)=>{if(!c)return;c.querySelectorAll('details').forEach(d=>{d.classList.toggle('on',d.open);d.querySelector('summary').addEventListener('click',e=>{e.preventDefault();
  const open=!d.classList.contains('on');slide(d,open);if(single&&open)c.querySelectorAll('details.on').forEach(o=>{if(o!==d)slide(o,false)})})})};
window.initAccordions=()=>{init(document.getElementById('acc'),true);init(document.getElementById('faqList'),false)};
})();
