'use strict';
// Alleen schriftelijk aangekondigde acties met een expliciete eindtijd verschijnen.
(function(root){
const shops=Object.freeze({
  acer:{name:'Acer',path:'/acer.html'},
  coolblue:{name:'Coolblue',path:'/coolblue.html'},
  smartphonehoesjes:{name:'Smartphonehoesjes.nl',path:'/accessoires.html'},
  hobo:{name:'Hobo.nl',path:'/hobo.html'},
  yorcom:{name:'Yorcom.nl',path:'/yorcom.html'}
});
function valid(p){
  if(!p||typeof p!=='object'||!Object.prototype.hasOwnProperty.call(shops,p.shop)||p.approved!==true||p.source!=='awin'&&p.source!=='tradetracker')return false;
  if(!['title','detail','startAt','endAt'].every(k=>typeof p[k]==='string'))return false;
  if(p.title.length>120||p.detail.length>260||p.title.length<4||p.detail.length<4)return false;
  if(p.code!==undefined&&(typeof p.code!=='string'||!/^[A-Z0-9_-]{1,30}$/.test(p.code)))return false;
  const s=Date.parse(p.startAt),e=Date.parse(p.endAt);
  return /(?:Z|[+-]\d\d:\d\d)$/.test(p.startAt)&&/(?:Z|[+-]\d\d:\d\d)$/.test(p.endAt)&&Number.isFinite(s)&&Number.isFinite(e)&&s<e&&e-s<=1000*60*60*24*100;
}
function active(p,now){return valid(p)&&Number.isFinite(now)&&Date.parse(p.startAt)<=now&&now<Date.parse(p.endAt);}
const api={shops,valid,active};
if(typeof module==='object'&&module.exports){module.exports=api;return;}
const locationKey=document.body.dataset.shop||'';
if(locationKey&&!Object.prototype.hasOwnProperty.call(shops,locationKey))return;
const host=locationKey?document.getElementById('catalog'):document.getElementById('homeContent');
if(!host)return;
let offers=[];
const style=document.createElement('style');
style.textContent='.khDeals{margin:22px 0;padding:18px 20px;border:1px solid #cbdcf1;border-radius:16px;background:#fff;box-shadow:0 4px 15px rgba(18,49,92,.05)}.khDeals h2{margin:4px 0 8px;color:#123c7c;font-size:clamp(20px,3vw,27px)}.khDeals .khDealIntro{color:#52627b;font-size:13px;line-height:1.6;margin:0 0 12px}.khDealGrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:12px}.khDeal{border:1px solid #d7e3f2;border-radius:12px;padding:14px;background:#f9fbff;display:flex;flex-direction:column;gap:8px}.khDeal b{color:#183b72}.khDeal p{font-size:13px;line-height:1.55;margin:0}.khDeal .khDealDate{font-weight:700;font-size:12px;color:#385b82}.khDeal a{font-size:13px;font-weight:700;color:#144b96;margin-top:auto}.khDeals .khDealFine{font-size:12px;line-height:1.5;color:#536781;margin:12px 0 0}';
document.head.append(style);
function render(){
 const now=Date.now();const eligible=offers.filter(p=>active(p,now)&&(!locationKey||p.shop===locationKey));
 let section=document.getElementById('kh-acties');
 if(!eligible.length){if(section)section.remove();return;}
 if(!section){section=document.createElement('section');section.id='kh-acties';section.className='khDeals';section.setAttribute('aria-label','Actuele winkelacties');if(locationKey)host.insertBefore(section,document.getElementById('catalogStatus')||host.firstChild);else {const strip=host.querySelector('.qualityStrip');if(strip)strip.insertAdjacentElement('afterend',section);else host.prepend(section);}}
 section.replaceChildren();
 const heading=document.createElement('h2');heading.textContent='Actuele Black Friday-acties';section.append(heading);
 const intro=document.createElement('p');intro.className='khDealIntro';intro.textContent='Alleen officieel aangekondigde acties binnen hun geldige periode. Aanbiedingen verdwijnen hier automatisch wanneer de eindtijd is bereikt.';section.append(intro);
 const grid=document.createElement('div');grid.className='khDealGrid';section.append(grid);
 for(const p of eligible){const card=document.createElement('article');card.className='khDeal';const title=document.createElement('b');title.textContent=p.title;card.append(title);const detail=document.createElement('p');detail.textContent=p.detail;card.append(detail);
 if(p.code){const code=document.createElement('p');code.textContent='Kortingscode: '+p.code;card.append(code);}
 const date=document.createElement('p');date.className='khDealDate';date.textContent='Geldig tot '+new Date(p.endAt).toLocaleString('nl-NL',{timeZone:'Europe/Amsterdam',day:'numeric',month:'long',year:'numeric',hour:'2-digit',minute:'2-digit'});card.append(date);
 const link=document.createElement('a');link.href=shops[p.shop].path;link.textContent='Bekijk '+shops[p.shop].name+'-producten →';card.append(link);grid.append(card);}
 const note=document.createElement('p');note.className='khDealFine';note.textContent='Acties gelden alleen voor deelnemende artikelen en volgens winkelvoorwaarden. Kortingen, prijzen en voorraad kunnen veranderen. Controleer de aanbieding en definitieve prijs altijd bij de winkel. KoopHelder kan commissie ontvangen via winkellinks; je betaalt niets extra.';section.append(note);
}
fetch('/data/acties.json',{cache:'no-store'}).then(r=>{if(!r.ok)throw Error('Actiedata niet beschikbaar');return r.json();}).then(data=>{if(data&&data.schema===1&&Array.isArray(data.promotions)&&data.promotions.length<=100){offers=data.promotions.filter(valid);render();setInterval(render,60*1000);document.addEventListener('visibilitychange',render);}}).catch(()=>{const section=document.getElementById('kh-acties');if(section)section.remove();});
})(globalThis);
