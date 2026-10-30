'use strict';
// Merchant identity, image sources and tracking stay separate for each network.
(function(root){
const shops={
 smartphonehoesjes:{dir:'smartphonehoesjes',name:'Smartphonehoesjes.nl',merchant:'8261',publisher:'3124230',network:'awin',prefix:'sh',images:['www.smartphonehoesjes.nl']},
 coolblue:{dir:'coolblue',name:'Coolblue',merchant:'85161',publisher:'3124230',network:'awin',prefix:'cb',images:['image.coolblue.nl','coolblue.bynder.com']},
 acer:{dir:'acer',name:'Acer',merchant:'17133',publisher:'3124230',network:'awin',prefix:'ac',images:['static2-ecemea.acer.com']},
 hobo:{dir:'hobo',name:'Hobo.nl',merchant:'37535',publisher:'518245',network:'tradetracker',host:'www.hobo.nl',path:'/tradetracker-redirect/',feed:'2232033',images:['www.hobo.nl']},
 yorcom:{dir:'yorcom',name:'Yorcom.nl',merchant:'4837',publisher:'518245',network:'tradetracker',host:'www.yorcom.nl',path:'/shopping/',feed:'253916',images:['www.yorcom.nl']}
};
function validManifest(m,c){return [1,2].includes(m.schema)&&m.merchantId===c.merchant&&m.publisherId===c.publisher&&(c.network==='tradetracker'?m.network==='tradetracker'&&m.schema===2:!m.network||m.network==='awin')&&Array.isArray(m.files)&&m.files.length>0&&m.files.length<=100;}
function validTracking(value,c){
 try{const u=new URL(value),q=u.searchParams;if(c.network!=='tradetracker'||u.protocol!=='https:'||u.host!==c.host||u.username||u.password||u.pathname!==c.path||q.getAll('tt').length!==1||q.get('tt')!==c.merchant+'_'+c.feed+'_'+c.publisher+'_'||q.getAll('r').length!==1)return false;
 const target=new URL(q.get('r'));return target.protocol==='https:'&&target.host===c.host&&!target.username&&!target.password;
 }catch{return false;}
}
function productLink(p,c,norm){
 if(c.network==='tradetracker')return validTracking(p.url,c)?p.url:'';
 if(!/^\d+$/.test(p.id))return '';
 return 'https://www.awin1.com/pclick.php?p='+p.id+'&a='+c.publisher+'&m='+c.merchant+'&clickref='+encodeURIComponent('kh_'+c.prefix+'_shop_'+norm(p.type).replace(/ /g,'_').slice(0,26));
}
function imageURL(value,c){try{const u=new URL(value);return u.protocol==='https:'&&c.images.includes(u.host)&&!u.username&&!u.password&&(c.dir!=='smartphonehoesjes'||u.pathname.startsWith('/media/'))?u.href:'';}catch{return '';}}
function validRow(r,c){return Array.isArray(r)&&(c.network==='tradetracker'?r.length===9:[5,8].includes(r.length))&&r.slice(0,5).every(v=>typeof v==='string')&&/^\d+$/.test(r[4])&&(c.network!=='tradetracker'||validTracking(r[8],c));}
const api={shops,validManifest,validTracking,productLink,imageURL,validRow};
if(typeof module==='object'&&module.exports)module.exports=api;else root.KHCatalogShops=api;
})(globalThis);
