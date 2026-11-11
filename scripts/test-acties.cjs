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
const coolblueCampaign = data.promotions.find(p => p.id === 'coolblue-black-friday-2026');
assert(coolblueCampaign, 'Expected the announced Coolblue Black Friday campaign');
assert.equal(coolblueCampaign.shop, 'coolblue');
assert.equal(coolblueCampaign.source, 'awin');
assert.equal(coolblueCampaign.startAt, '2026-11-09T00:00:00+01:00');
assert.equal(coolblueCampaign.endAt, '2026-12-01T00:00:00+01:00');
const blackFridayPage=fs.readFileSync('assets/black-friday-acties.js','utf8');
assert(blackFridayPage.includes("fetch('/data/acties.json'"),'Black Friday page should use the same approved action feed');
assert(!blackFridayPage.includes("fetch('/data/black-friday-acties.json'"),'Legacy action feed must not power live pages');
for(const shop of ['dutchplaza','mobielnl'])assert(blackFridayPage.includes(shop+':{name:'),'Black Friday page must list '+shop);
for(const code of ['BF3','SAVE10','GPU10'])assert(data.promotions.some(p=>p.code===code),'Expected already-announced Acer promotion '+code);
console.log('Black Friday tests passed: all five shops, source checks, exact start and expiry, safe fallback.');
