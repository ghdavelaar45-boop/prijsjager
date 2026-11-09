'use strict';
// The Black Friday page and shop banners share /data/acties.json.
// Only manually approved Awin/TradeTracker promotions with exact start/end are shown.
(async()=>{
const status=document.getElementById('actieStatus'),list=document.getElementById('actieLijst');
const shops={
 acer:{name:'Acer',href:'/acer.html'},
 smartphonehoesjes:{name:'Smartphonehoesjes.nl',href:'/accessoires.html'},
 coolblue:{name:'Coolblue',href:'/coolblue.html'},
 hobo:{name:'Hobo.nl',href:'/hobo.html'},
 yorcom:{name:'Yorcom.nl',href:'/yorcom.html'},
 dutchplaza:{name:'Dutch Plaza',href:'/?winkel=dutchplaza&pagina=producten'},
 mobielnl:{name:'Mobiel.nl',href:'/?winkel=mobielnl&pagina=producten'}
};
const el=(tag,text,cls)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;if(cls)n.className=cls;return n};
function valid(x){
 if(!x||!Object.prototype.hasOwnProperty.call(shops,x.shop)||x.approved!==true||!['awin','tradetracker'].includes(x.source)||typeof x.title!=='string'||typeof x.detail!=='string'||typeof x.startAt!=='string'||typeof x.endAt!=='string')return false;
 if(x.title.length<4||x.title.length>120||x.detail.length<4||x.detail.length>260)return false;
 if(!/(?:Z|[+-]\d\d:\d\d)$/.test(x.startAt)||!/(?:Z|[+-]\d\d:\d\d)$/.test(x.endAt))return false;
 const a=Date.parse(x.startAt),b=Date.parse(x.endAt);
 return Number.isFinite(a)&&Number.isFinite(b)&&a<b&&b-a<=100*24*3600000&&(x.code===undefined||typeof x.code==='string'&&/^[A-Z0-9_-]{1,30}$/.test(x.code));
}
const fmt=date=>new Intl.DateTimeFormat('nl-NL',{timeZone:'Europe/Amsterdam',day:'2-digit',month:'2-digit',year:'numeric',hour:'2-digit',minute:'2-digit'}).format(new Date(date));
function render(promotions){
 const now=Date.now(),active=promotions.filter(x=>Date.parse(x.startAt)<=now&&now<Date.parse(x.endAt)),upcoming=promotions.filter(x=>now<Date.parse(x.startAt));
 list.replaceChildren();
 for(const [key,shop] of Object.entries(shops)){
  const section=el('section',undefined,'shop');section.append(el('h2',shop.name));
  const current=active.filter(x=>x.shop===key),soon=upcoming.filter(x=>x.shop===key);
  if(!current.length&&!soon.length)section.append(el('p','Er is momenteel geen officieel bevestigde actie met een geldige looptijd bekend. Bekijk eventueel het gewone assortiment.','muted'));
  for(const [group,arr] of [['Actief',current],['Binnenkort',soon]])for(const offer of arr){
   const card=el('article',undefined,'deal');
   card.append(el('span',group,'state'),el('h3',offer.title),el('p',offer.detail));
   card.append(el('p','Geldig: '+fmt(offer.startAt)+' t/m '+fmt(Date.parse(offer.endAt)-60000)+' (Nederlandse tijd)','period'));
   if(offer.code)card.append(el('p','Kortingscode: '+offer.code,'code'));
   card.append(el('p','Bron: officiële '+(offer.source==='awin'?'Awin':'TradeTracker')+'-melding','source'));
   const a=el('a','Bekijk het assortiment bij '+shop.name);a.href=shop.href;a.className='button';card.append(a);section.append(card);
  }
  const back=el('a','Gewoon assortiment bekijken');back.href=shop.href;back.className='plain';section.append(back);list.append(section);
 }
 status.textContent=active.length+' actuele '+(active.length===1?'actie':'acties')+' · '+upcoming.length+' aangekondigd. Verlopen acties worden automatisch verborgen. Controleer altijd de voorwaarden bij de winkel.';
}
try{
 const res=await fetch('/data/acties.json',{cache:'no-store'});if(!res.ok)throw Error('Actiebestand niet bereikbaar');
 const data=await res.json();
 if(!data||data.schema!==1||!Array.isArray(data.promotions)||data.promotions.length>100||!data.promotions.every(valid))throw Error('Ongeldige actiegegevens');
 render(data.promotions);
 setInterval(()=>render(data.promotions),60000);
 document.addEventListener('visibilitychange',()=>render(data.promotions));
}catch{status.textContent='Acties zijn tijdelijk niet beschikbaar. Raadpleeg de winkels voor actuele voorwaarden.';list.replaceChildren();}
})();
