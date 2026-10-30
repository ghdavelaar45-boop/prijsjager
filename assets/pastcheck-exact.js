'use strict';
(()=>{
const $=id=>document.getElementById(id),C=KHPast,euro=n=>new Intl.NumberFormat('nl-NL',{style:'currency',currency:'EUR'}).format(n);
let phones=[],phoneManifest,phoneFiltered=[],shown=12,printerManifest,printers=[],printerRows=[];
function el(tag,value,cls){const e=document.createElement(tag);if(value!==undefined)e.textContent=value;if(cls)e.className=cls;return e;}
function sourceLink(url,label){const a=el('a',label);a.href=url;a.target='_blank';a.rel='noopener noreferrer';return a;}
const date=s=>new Date(s).toLocaleString('nl-NL',{dateStyle:'short',timeStyle:'short'});
async function catalog(dir,merchant,status){
 const res=await fetch('/data/'+dir+'/manifest.json',{cache:'no-cache'});if(!res.ok)throw Error('Winkelgegevens zijn tijdelijk niet bereikbaar.');
 const m=await res.json();if(m.schema!==2||m.merchantId!==merchant||m.publisherId!=='3124230'||!Array.isArray(m.files)||!m.files.length||m.files.length>100||!Number.isInteger(m.count)||m.count<0)throw Error('Winkelgegevens konden niet worden gecontroleerd.');
 const chunks=new Array(m.files.length);let next=0,done=0;
 await Promise.all(Array.from({length:4},async()=>{while(next<m.files.length){const i=next++,p=m.files[i];if(!/^catalog-\d{2}\.json\.gz$/.test(p.file)||!/^[a-f0-9]{64}$/.test(p.sha256)||!Number.isInteger(p.count)||p.count<0||p.count>2000)throw Error('Ongeldig catalogusbestand.');
 const r=await fetch('/data/'+dir+'/'+p.file+'?v='+p.sha256);if(!r.ok)throw Error('Een deel van de winkelgegevens ontbreekt.');const bytes=await r.arrayBuffer();if(bytes.byteLength>5e6)throw Error('Catalogusbestand is te groot.');
 const hash=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes)),b=>b.toString(16).padStart(2,'0')).join('');if(hash!==p.sha256)throw Error('De bestandscontrole is mislukt.');
 const rows=await new Response(new Blob([bytes]).stream().pipeThrough(new DecompressionStream('gzip'))).json();if(!Array.isArray(rows)||rows.length!==p.count)throw Error('Onvolledige winkelgegevens.');chunks[i]=rows;status.textContent='Winkelgegevens laden: '+Math.round(++done/m.files.length*100)+'%';}}));
 const rows=chunks.flat();if(rows.length!==m.count)throw Error('Onvolledige catalogus.');return {manifest:m,rows:rows.filter(r=>Array.isArray(r)&&r.length===8&&r.slice(0,5).every(x=>typeof x==='string')&&/^\d{1,20}$/.test(r[4])&&(r[5]===null||(typeof r[5]==='number'&&Number.isFinite(r[5])&&r[5]>0))&&(r[6]===null||(typeof r[6]==='number'&&Number.isFinite(r[6])&&r[6]>=0))&&typeof r[7]==='boolean')};
}
function product(row,shop,m){
 const card=el('article',undefined,'card'),img=el('img');img.src=C.imageURL(row[3],shop)||'/assets/productfoto-ontbreekt.svg';img.alt=row[0];img.loading='lazy';img.width=240;img.height=160;img.addEventListener('error',()=>{img.src='/assets/productfoto-ontbreekt.svg'},{once:true});card.append(img,el('h3',row[0]));
 const fresh=C.fresh(m.fetchedAt);card.append(el('p',fresh&&row[5]!==null?euro(row[5]):'Actuele prijs: zie winkel','price'));
 card.append(el('p',fresh?(row[6]===null?'Bezorgkosten: zie winkel':row[6]===0?'Geen bezorgkosten volgens winkelgegevens':euro(row[6])+' bezorgkosten'):'Gegevens ouder dan 48 uur of datum onbekend; controleer de winkel.'));
 if(fresh)card.append(el('p',row[7]?'Volgens winkelgegevens op voorraad':'Voorraad: controleer de winkel'));
 card.append(el('p','Advertentielink · commissie mogelijk.'));
 const a=el('a','Bekijk bij '+(shop==='coolblue'?'Coolblue':'Smartphonehoesjes.nl')+' ↗','button');a.href='https://www.awin1.com/pclick.php?p='+row[4]+'&a=3124230&m='+(shop==='coolblue'?'85161':'8261')+'&clickref=kh_pastcheck_exact';a.target='_blank';a.rel='sponsored noopener noreferrer';card.append(a);return card;
}
function modelOptions(){
 const query=C.norm($('phoneSearch').value),selected=$('phoneModel').value;
 const models=[...new Set(phones.flatMap(p=>p.models))].filter(m=>query.split(' ').every(w=>m.includes(w))).sort((a,b)=>a.localeCompare(b,'nl',{numeric:true}));
 $('phoneModel').replaceChildren(new Option(models.length?'Kies het volledige model…':'Geen herkend model gevonden',''),...models.map(m=>new Option(m,m)));
 if(models.includes(selected))$('phoneModel').value=selected;
 $('phoneStatus').textContent=models.length+' modelnamen gevonden. Bron: Smartphonehoesjes.nl · winkelgegevens '+date(phoneManifest.fetchedAt)+'.';renderPhones();
}
function renderPhones(){
 const model=$('phoneModel').value;phoneFiltered=phones.filter(p=>p.models.includes(model));$('phoneResults').replaceChildren(...phoneFiltered.slice(0,shown).map(p=>product(p.row,'phone',phoneManifest)));
 $('phoneReason').hidden=!model;$('phoneMore').hidden=!model||shown>=phoneFiltered.length;
 if(model){$('phoneReason').replaceChildren(el('strong','Volgens de winkeltitel voor: '+model),el('p',phoneFiltered.length+' hoesjes met deze volledige herkende modelnaam. '+Math.min(shown,phoneFiltered.length)+' getoond. Controleer de compatibiliteitslijst bij de winkel vóór je bestelt.'),el('p','Waarom deze selectie? De variant in de producttitel komt overeen met jouw keuze. De alfabetische volgorde is geen beoordeling of prijsranglijst.'));
 }
}
$('phoneSearch').addEventListener('input',()=>{shown=12;if(phoneManifest)modelOptions();});$('phoneModel').addEventListener('change',()=>{shown=12;renderPhones();});$('phoneMore').addEventListener('click',()=>{shown+=12;renderPhones();});
async function loadPhones(){try{const c=await catalog('smartphonehoesjes','8261',$('phoneStatus'));phoneManifest=c.manifest;phones=c.rows.filter(r=>r[2]==='Phone Cover').map(row=>({row,models:C.models(row[0])})).filter(p=>p.models.length);$('phoneModel').disabled=false;modelOptions();}catch(e){$('phoneStatus').textContent=e.message+' Probeer de pagina opnieuw te laden.';$('phoneModel').replaceChildren(new Option('Modelcheck nu niet beschikbaar',''));}}
const form=$('costForm'),field=name=>form.elements.namedItem(name);
function setField(name,value){field(name).value=value===undefined||value===null?'':value;}
function selectPrinter(){
 const p=printers.find(p=>p.name===$('printerModel').value);$('printerInfo').hidden=!p;if(!p)return;
 const fresh=C.fresh(printerManifest.fetchedAt),row=printerRows.find(r=>r[0]===p.name&&r[2]==='printers'),ink=printerRows.filter(r=>p.inks.includes(r[0])&&['cartridges','toners','inktflesjes'].includes(r[2]));
 $('printerReason').replaceChildren(el('strong',p.family),el('p',p.note),sourceLink(p.source,p.sourceLabel+' ↗'),el('p','Modelkoppeling gecontroleerd op '+p.checkedAt+'. Winkelgegevens: '+date(printerManifest.fetchedAt)+'. Deze check gaat over de inktcode, niet over alle printerfuncties.'));
 if(row)$('printerReason').append(product(row,'coolblue',printerManifest));
 $('inkResults').replaceChildren(...ink.map(r=>product(r,'coolblue',printerManifest)));if(!ink.length)$('inkResults').append(el('p','Geen geselecteerde inkt in het huidige assortiment gevonden. De inktcode hierboven blijft je controlepunt; beschikbaarheid is onbekend.'));
 form.reset();for(const name of ['colorPrice','colorYield'])field(name).required=false;const black=ink.find(r=>r[0]===p.black),color=ink.find(r=>r[0]===p.colorInk);
 setField('purchase',fresh?row?.[5]:null);setField('blackPrice',fresh?black?.[5]:null);setField('blackYield',p.blackYield);setField('colorPrice',fresh?color?.[5]:null);setField('colorYield',p.colorYield);
 for(const name of ['colorShare','colorPrice','colorYield','includedColor'])field(name).disabled=!p.color;
 $('costSource').replaceChildren(el('span','Prijsvelden: '+(fresh?'huidige winkelgegevens waar beschikbaar':'geen recente prijs; vul zelf in')+'. Opbrengst: '+(p.blackYield?'fabrieksopgave voor de genoemde standaardcartridge':'nog invullen volgens jouw verpakking')+'. Na aanpassing rekenen we met jouw invoer. '));if(p.yieldSource)$('costSource').append(sourceLink(p.yieldSource,'Bron paginaopbrengst ↗'));
 $('costResult').textContent='Vul ontbrekende waarden in en bereken jouw gebruikskosten. Standaard is het kleuraandeel 0% en trekken we geen meegeleverde inkt af.';
}
$('printerModel').addEventListener('change',selectPrinter);
form.addEventListener('input',()=>{for(const name of ['colorPrice','colorYield'])field(name).required=Number(field('colorShare').value)>0;$('costResult').textContent='Je invoer is gewijzigd. Bereken opnieuw om de schatting bij te werken.';});
form.addEventListener('submit',e=>{e.preventDefault();const v={};for(const name of ['purchase','pages','years','blackPrice','blackYield','colorShare','colorPrice','colorYield','includedBlack','includedColor'])v[name]=field(name).disabled?0:field(name).value===''?NaN:Number(field(name).value);
 const color=v.colorShare>0;for(const name of ['colorPrice','colorYield'])field(name).required=color;
 const r=C.calculate(v);if(!r){$('costResult').textContent='Vul geldige prijzen en paginaopbrengsten in. Bij kleurenpagina’s zijn ook de prijs en opbrengst van de complete kleurset nodig.';return;}
 $('costResult').replaceChildren(el('p','Aanschaf + vervangende inkt / toner'),el('p',euro(r.total),'resultTotal'),el('p',r.totalPages.toLocaleString('nl-NL')+' pagina’s in '+v.years+' jaar · '+r.colorPages.toLocaleString('nl-NL')+' met kleur.'),el('p',r.blackPacks+' zwarte verpakkingen + '+r.colorPacks+' complete kleurverpakkingen = '+euro(r.ink)+' vervangende inkt/toner.'),el('p','Aanschaf '+euro(v.purchase)+'. Hele verpakkingen naar boven afgerond; resterende inkt kan na deze periode overblijven. Zie de uitgesloten kosten hieronder.'));
});
async function loadPrinters(){try{const [res,c]=await Promise.all([fetch('/assets/pastcheck-models.json'),catalog('coolblue','85161',$('printerStatus'))]);if(!res.ok)throw Error('Modelcontrole tijdelijk niet beschikbaar.');const d=await res.json();printers=d.printers.map(p=>({...p,checkedAt:d.checkedAt}));printerManifest=c.manifest;printerRows=c.rows;$('printerModel').replaceChildren(new Option('Kies je exacte printer…',''),...printers.map(p=>new Option(p.name,p.name)));$('printerModel').disabled=false;$('printerStatus').textContent='5 modelkoppelingen gecontroleerd op '+d.checkedAt+'. Staat jouw model er niet bij? Dan kunnen we de passende inkt nog niet bevestigen.';}catch(e){$('printerStatus').textContent=e.message+' Probeer de pagina opnieuw te laden.';}}
loadPhones();loadPrinters();
})();
