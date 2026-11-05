'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs');
const zlib=require('node:zlib');
const C=require('../assets/pastcheck-core.js');
assert.deepEqual(C.models('Hoesje voor iPhone 16 Pro Max - zwart'),['iphone 16 pro max']);
assert(!C.models('Hoesje iPhone 16 Pro Max').includes('iphone 16'));
assert.deepEqual(C.models('Hoesje iPhone 16e'),['iphone 16e']);
assert.deepEqual(C.models('Samsung Galaxy S25 Ultra hoesje'),['galaxy s25 ultra']);
assert.deepEqual(C.models('Samsung Galaxy S25 FE hoesje'),['galaxy s25 fe']);
assert.deepEqual(C.models('Galaxy A55 (5G) hoesje'),['galaxy a55 5g']);
assert(!C.models('Galaxy A55 (5G) hoesje').includes('galaxy a55'));
assert.deepEqual(C.models('Google Pixel 9 Pro XL hoesje'),['pixel 9 pro xl']);
assert.deepEqual(C.models('iPhone 16/17 hoesje'),[]);
assert.deepEqual(C.models('iPhone 16 / Pro hoesje'),[]);
assert.deepEqual(C.models('iPhone 16 / iPhone 17 hoesje'),['iphone 16','iphone 17']);
assert.deepEqual(C.models('Galaxy S25 Edge hoesje'),[]);
assert.deepEqual(C.models('Universeel hoesje'),[]);
assert.deepEqual(C.models('iPhone 16 ProMax'),[]);
assert(C.fresh('2026-10-30T00:00:00Z',Date.parse('2026-10-31T23:59:00Z')));
assert(!C.fresh('2026-10-30T00:00:00Z',Date.parse('2026-11-01T00:01:00Z')));
assert(!C.fresh('bad'));assert(!C.fresh('2027-01-01',Date.parse('2026-10-30')));
for(const url of ['javascript:alert(1)','https://www.smartphonehoesjes.nl.evil.test/a','https://user@www.smartphonehoesjes.nl/a','https://image.coolblue.nl:444/a','http://image.coolblue.nl/a'])assert.equal(C.imageURL(url,'coolblue'),'');
assert.equal(C.imageURL('https://image.coolblue.nl/a','coolblue'),'https://image.coolblue.nl/a');
const input={purchase:55,pages:100,years:3,blackPrice:28.99,blackYield:180,colorShare:20,colorPrice:38.99,colorYield:180,includedBlack:0,includedColor:0};
assert.deepEqual(C.calculate(input),{totalPages:3600,colorPages:720,blackPacks:20,colorPacks:4,ink:735.76,total:790.76});
assert.equal(C.calculate({...input,blackYield:0}),null);
assert.equal(C.calculate({...input,colorPrice:NaN}),null);
assert.equal(C.calculate({...input,blackPrice:NaN}),null);
assert.equal(C.calculate({...input,purchase:-5}),null);
assert.equal(C.calculate({...input,colorShare:101}),null);
assert.equal(C.calculate({...input,colorShare:0,colorPrice:NaN,colorYield:NaN}).colorPacks,0);
assert.equal(C.calculate({...input,includedBlack:3600}).blackPacks,0);
assert.equal(C.calculate({...input,pages:1,years:1}).blackPacks,1);
assert.equal(C.calculate({...input,pages:0}).ink,0);
// Every exact printer/ink title must resolve to the intended category in today's real catalog.
const data=JSON.parse(fs.readFileSync('assets/pastcheck-models.json'));
const rows=fs.readdirSync('data/coolblue').filter(f=>f.endsWith('.gz')).flatMap(f=>JSON.parse(zlib.gunzipSync(fs.readFileSync('data/coolblue/'+f))));
// Catalog availability changes between feed refreshes. Missing products are reported,
 // never fabricated or treated as a matching product.
let availablePrinters=0, verifiedInks=0;
for(const p of data.printers){
 const printerMatches=rows.filter(r=>r[0]===p.name&&r[2]==='printers');
 assert(printerMatches.length<=1,'Duplicate printer: '+p.name);
 if(printerMatches.length===0){console.warn('PastCheck unavailable printer: '+p.name);continue;}
 availablePrinters++;
 for(const title of p.inks){
  const matches=rows.filter(r=>r[0]===title);
  assert(matches.length<=1,'Duplicate ink: '+title);
  if(matches.length===0){console.warn('PastCheck unavailable ink for '+p.name+': '+title);continue;}
  assert(['cartridges','toners','inktflesjes'].includes(matches[0][2]),title);
  verifiedInks++;
 }
 assert(!p.inks.some(t=>t.includes('PG-585')));
 assert(p.source.startsWith('https://'));
}
assert(availablePrinters>0,'No configured PastCheck printers available in catalog');
assert(verifiedInks>0,'No configured PastCheck ink or toner available in catalog');
console.log('PastCheck catalog availability: '+availablePrinters+' printers and '+verifiedInks+' ink/toner items verified.');
console.log('PastCheck: variant isolation, incomplete names, stale prices, unsafe images, whole-pack costs and real catalog mappings passed.');
