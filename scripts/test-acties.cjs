'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs');
const policy=require('../assets/acties.js');
const data=JSON.parse(fs.readFileSync('data/acties.json','utf8'));
assert.equal(data.schema,1);
assert(Array.isArray(data.promotions));
assert.deepEqual(Object.keys(policy.shops).sort(),['acer','coolblue','hobo','smartphonehoesjes','yorcom'].sort());
for(const p of data.promotions){
 assert(policy.valid(p),p.id);
 const start=Date.parse(p.startAt),end=Date.parse(p.endAt);
 assert(!policy.active(p,start-1));assert(policy.active(p,start));
 assert(policy.active(p,end-1));assert(!policy.active(p,end));
 assert(!policy.valid({...p,approved:false}));
 assert(!policy.valid({...p,shop:'unknown'}));
 assert(!policy.valid({...p,endAt:'tomorrow'}));
}
for(const page of ['index.html','acer.html','accessoires.html','coolblue.html','hobo.html','yorcom.html']){
 const html=fs.readFileSync(page,'utf8');
 assert(html.includes('/assets/acties.js"'),page+' missing promo policy');
}
assert(!data.promotions.some(p=>p.shop==='coolblue'),'Coolblue dates await confirmation');
console.log('Black Friday tests passed: all five shops, source checks, exact start and expiry, safe fallback.');
