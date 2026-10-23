const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const html=fs.readFileSync('index.html','utf8'),script=html.match(/<script id="exactShopPrices">([\s\S]*?)<\/script>/)[1];
const document={createElement:tag=>({tag,children:[],append(...nodes){this.children.push(...nodes)},setAttribute(name,value){this[name]=value}})};const context={window:{},document,URL,Date,Map,Set,Intl};vm.createContext(context);vm.runInContext(script,context);const api=context.window.KHExactPrices;
const stamp=new Date().toISOString();
function item(source,id,price,delivery=0){return {fullFeedSource:source,id,brand:'Acer',shop:source,priceFetchedAt:stamp,rawFeedPrice:price,price,deliveryCost:delivery,inStock:true,url:`https://www.awin1.com/pclick.php?p=${id}&a=3124230&m=${{coolblue:'85161',acer:'17133',smartphonehoesjes:'8261'}[source]}`};}
function data(members=[['coolblue','1'],['acer','2']]){return {schema:1,publisherId:'3124230',fetchedAt:stamp,groups:[{gtin:'04006381333931',brand:'acer',condition:'new',members}]};}
let items=[item('coolblue',1,99,4.95),item('acer',2,109,null)];assert.equal(api.attach(items,data()),1);assert.equal(items[0].offers.length,2);assert.equal(items[0].offers[0].rawFeedPrice,99);assert.equal(items[0].offers[1].rawFeedPrice,109);
assert.equal(api.values(items[0].offers[0]).total,103.95);assert.equal(api.values(items[0].offers[1]).total,null);assert.equal(api.values(items[0].offers[1],Date.now()+49*3600000).price,null);const rendered=JSON.stringify(api.table(items[0]));assert.ok(rendered.includes('Onbekend'));assert.ok(rendered.includes('103,95'));assert.ok(rendered.includes('3124230'));assert.ok(rendered.includes('04006381333931'));
items=[item('coolblue',1,99),item('acer',2,89),item('smartphonehoesjes',3,95)];assert.equal(api.attach(items,data([['coolblue','1'],['acer','2'],['smartphonehoesjes','3']])),1);assert.equal(api.ordered(items[0])[0].price,89);
items=[item('coolblue',1,99),{...item('acer',2,89),brand:'HP'}];assert.equal(api.attach(items,data()),0);
items=[item('coolblue',1,99),{...item('acer',2,89),priceFetchedAt:'2020-01-01'}];assert.equal(api.attach(items,data()),0);
items=[item('coolblue',1,99),{...item('acer',2,89),url:'https://evil.example/'}];assert.equal(api.attach(items,data()),0);
assert.ok(html.includes('offer.rawFeedPrice:null'));assert.ok(!html.includes('offer.price=p.price;'));
console.log('Exact-price checks passed: separate prices, unknown delivery, stale prices, merchant identity, conflicting brands, synchronized data and three-shop matches.');
