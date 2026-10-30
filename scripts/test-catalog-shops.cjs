'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),zlib=require('node:zlib');
const P=require('../assets/catalog-shops.js');
const norm=s=>s.toLowerCase().replace(/[^a-z0-9]+/g,' ').trim();
let count=0;
for(const shop of Object.values(P.shops)){
 const m=JSON.parse(fs.readFileSync('data/'+shop.dir+'/manifest.json'));assert(P.validManifest(m,shop),shop.dir);
 assert(!P.validManifest({...m,publisherId:'1'},shop));assert(!P.validManifest({...m,merchantId:'1'},shop));
 for(const part of m.files){
  const rows=JSON.parse(zlib.gunzipSync(fs.readFileSync('data/'+shop.dir+'/'+part.file)));
  for(const r of rows){assert(P.validRow(r,shop),shop.dir+': '+r[0]);const link=P.productLink({id:r[4],url:r[8],type:r[2]},shop,norm);assert(link.startsWith('https://'));
   if(shop.network==='tradetracker'){count++;assert.equal(link,r[8]);assert(!link.includes('awin1.com'));assert(!P.validRow(r.slice(0,8),shop));}
   else {const u=new URL(link);assert.equal(u.hostname,'www.awin1.com');assert.equal(u.searchParams.get('a'),shop.publisher);assert.equal(u.searchParams.get('m'),shop.merchant);assert.equal(u.searchParams.get('p'),r[4]);}
  }
 }
 for(const url of ['javascript:alert(1)','https://user@'+shop.images[0]+'/a','https://'+shop.images[0]+'.evil.test/a','https://'+shop.images[0]+':444/a'])assert.equal(P.imageURL(url,shop),'');
}
for(const key of ['hobo','yorcom']){
 const c=P.shops[key],good='https://'+c.host+c.path+'?tt='+c.merchant+'_'+c.feed+'_'+c.publisher+'_&r='+encodeURIComponent('https://'+c.host+'/artikel/test');assert(P.validTracking(good,c));
 for(const bad of [good.replace(c.publisher,'1'),good.replace(c.feed,'1'),good.replace('https://','http://'),good.replace(c.host,c.host+'.evil.test'),good+'&tt=1',good+'&r='+encodeURIComponent('https://evil.test'),good.replace(encodeURIComponent('https://'+c.host+'/artikel/test'),encodeURIComponent('javascript:alert(1)')),good.replace(encodeURIComponent('https://'+c.host+'/artikel/test'),encodeURIComponent('https://user@'+c.host+'/x'))]){
  assert(!P.validTracking(bad,c));assert.equal(P.productLink({url:bad},c,norm),'');
 }
 assert(!P.validManifest({...JSON.parse(fs.readFileSync('data/'+key+'/manifest.json')),network:'awin'},c));
 const html=fs.readFileSync(key+'.html','utf8');assert(html.includes('data-shop="'+key+'"'));assert(html.includes('/assets/catalog-shops.js?v=1'));assert(html.includes('/assets/accessoires-catalog.js?v=6'));assert(html.includes('https://'+c.host));
}
console.log('Catalog checks passed: '+count+' TradeTracker product links, three existing Awin shops, merchant/publisher isolation, unsafe images and unsafe/ambiguous redirects.');
