'use strict';
// Shared pure rules: used by the page and the offline regression checks.
(function(root){
const norm=s=>String(s).toLowerCase().replace(/\s+/g,' ').trim();
function models(title){
  const out=[];
  const re=/\b(iPhone\s+\d{1,2}[a-z]?(?:\s+Pro\s+Max|\s+Pro|\s+Plus|\s+mini|\s+Air)?|Galaxy\s+[AS]\d{1,3}(?:\s*(?:Ultra|Plus|FE|Lite|\+))?(?:\s*\(?[45]G\)?)?|Pixel\s+\d{1,2}[a-z]?(?:\s+Pro\s+XL|\s+Pro|\s+XL)?)(?![a-z0-9])/gi;
  // Shorthand lists don't unambiguously state the full name of each model.
  if (/\/\s*(?:\d|Pro\b|Plus\b|Ultra\b)/i.test(title)) return [];
  for(const m of title.matchAll(re)){
    const tail=title.slice(m.index+m[0].length);
    if(/^\s*(?:Pro|Max|Plus|Ultra|FE|Lite|Edge|Fold|Flip|XL|Air|mini|[45]G|\+)/i.test(tail))continue;
    out.push(norm(m[0].replace(/[()]/g,'').replace(/\+/g,' Plus').replace(/(\d)([45]G)\b/gi,'$1 $2')));
  }
  return [...new Set(out)];
}
function fresh(date,now=Date.now()){const age=now-Date.parse(date);return Number.isFinite(age)&&age>=-300000&&age<=48*3600000;}
function imageURL(value,shop){try{const u=new URL(value);return u.protocol==='https:'&&!u.username&&!u.password&&!u.port&&(shop==='coolblue'?['image.coolblue.nl','coolblue.bynder.com']:['www.smartphonehoesjes.nl']).includes(u.hostname)?u.href:'';}catch{return '';}}
function calculate({purchase,pages,years,blackPrice,blackYield,colorShare=0,colorPrice,colorYield,includedBlack=0,includedColor=0}){
  const nonnegative=[purchase,pages,blackPrice,colorShare,includedBlack,includedColor];
  if(nonnegative.some(x=>typeof x!=='number'||!Number.isFinite(x)||x<0)||!Number.isFinite(years)||years<=0||years>10||!Number.isFinite(blackYield)||blackYield<=0||colorShare>100)return null;
  if(colorShare>0&&(!Number.isFinite(colorPrice)||colorPrice<0||!Number.isFinite(colorYield)||colorYield<=0))return null;
  const totalPages=Math.ceil(pages*12*years),colorPages=Math.ceil(totalPages*colorShare/100);
  const blackPacks=Math.ceil(Math.max(0,totalPages-includedBlack)/blackYield);
  const colorPacks=colorShare?Math.ceil(Math.max(0,colorPages-includedColor)/colorYield):0;
  const inkCents=blackPacks*Math.round(blackPrice*100)+colorPacks*Math.round((colorPrice||0)*100);
  return {totalPages,colorPages,blackPacks,colorPacks,ink:inkCents/100,total:(Math.round(purchase*100)+inkCents)/100};
}
const api={models,norm,fresh,imageURL,calculate};
if(typeof module==='object'&&module.exports)module.exports=api;else root.KHPast=api;
})(globalThis);
