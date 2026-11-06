'use strict';
(async()=>{
const status=document.getElementById('actieStatus'),list=document.getElementById('actieLijst');
const shops=['Acer','Smartphonehoesjes.nl','Coolblue','Hobo.nl','Yorcom.nl'];
const links={'Acer':'/acer.html','Smartphonehoesjes.nl':'/accessoires.html','Coolblue':'/coolblue.html','Hobo.nl':'/hobo.html','Yorcom.nl':'/yorcom.html'};
const el=(tag,text,cls)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;if(cls)n.className=cls;return n};
function valid(x){return x&&typeof x.shop==='string'&&shops.includes(x.shop)&&typeof x.title==='string'&&x.title.length>0&&typeof x.detail==='string'&&typeof x.from==='string'&&typeof x.until==='string'&&Number.isFinite(Date.parse(x.from))&&Number.isFinite(Date.parse(x.until))&&Date.parse(x.from)<Date.parse(x.until)&&x.href===links[x.shop]&&typeof x.code==='string'&&typeof x.source==='string'}
function render(data){if(!data||data.schema!==1||!Array.isArray(data.offers)||data.offers.length>100||!data.offers.every(valid))throw Error('Actiegegevens zijn ongeldig.');
const now=Date.now(),active=data.offers.filter(x=>Date.parse(x.from)<=now&&now<Date.parse(x.until));
const upcoming=data.offers.filter(x=>now<Date.parse(x.from));
list.replaceChildren();
for(const shop of shops){const section=el('section',undefined,'shop');section.append(el('h2',shop));
const current=active.filter(x=>x.shop===shop),soon=upcoming.filter(x=>x.shop===shop);
if(!current.length&&!soon.length)section.append(el('p','Er is momenteel geen actie met een bevestigde, geldige looptijd bekend. Bekijk eventueel het gewone assortiment.','muted'));
for(const [group,arr] of [['Actief',current],['Binnenkort',soon]])for(const offer of arr){const card=el('article',undefined,'deal');card.append(el('span',group,'state'),el('h3',offer.title),el('p',offer.detail));
const fmt=d=>new Intl.DateTimeFormat('nl-NL',{timeZone:'Europe/Amsterdam',day:'2-digit',month:'2-digit',year:'numeric',hour:'2-digit',minute:'2-digit'}).format(new Date(d));
card.append(el('p','Geldig: '+fmt(offer.from)+' t/m '+fmt(new Date(Date.parse(offer.until)-60000))+' (Nederlandse tijd)','period'));
if(offer.code)card.append(el('p','Kortingscode: '+offer.code,'code'));
card.append(el('p','Bron: '+offer.source,'source'));
const a=el('a','Bekijk het assortiment bij '+shop);a.href=offer.href;a.className='button';card.append(a);section.append(card)}
const back=el('a','Gewoon assortiment bekijken');back.href=links[shop];back.className='plain';section.append(back);list.append(section)}
status.textContent=active.length+' actuele '+(active.length===1?'actie':'acties')+' · '+upcoming.length+' aangekondigd. Verlopen acties worden automatisch verborgen.';
}
try{const res=await fetch('/data/black-friday-acties.json',{cache:'no-store'});if(!res.ok)throw Error('Het actiebestand is niet bereikbaar.');const data=await res.json();render(data);
// Check periodically: a deal never remains labelled active after its end.
setInterval(()=>render(data),60000);
}catch(e){status.textContent='Acties zijn tijdelijk niet beschikbaar. Raadpleeg de winkels voor de actuele voorwaarden.';list.replaceChildren()}
})();