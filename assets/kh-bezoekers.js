'use strict';
(() => {
  // Bezoekersstatistieken zonder extra cookies. Alleen de beheerder kan zich per browser uitsluiten.
  const key='koophelder-eigen-bezoek-v1';
  function eigenBezoek(){try{return localStorage.getItem(key)==='1'}catch{return false}}
  const control=document.getElementById('kh-beheer-statistieken');
  if(control){
    const status=document.getElementById('kh-beheer-status');
    const uit=document.getElementById('kh-uitsluiten');
    const aan=document.getElementById('kh-meetellen');
    const toon=()=>{const eigen=eigenBezoek();status.textContent=eigen?'Deze browser is uitgesloten van nieuwe Cloudflare-bezoekmetingen.':'Deze browser wordt bij gewone websitebezoeken meegeteld.';uit.disabled=eigen;aan.disabled=!eigen};
    uit.addEventListener('click',()=>{try{localStorage.setItem(key,'1')}catch{status.textContent='Opslaan in deze browser is geblokkeerd.';return}toon()});
    aan.addEventListener('click',()=>{try{localStorage.removeItem(key)}catch{status.textContent='Browserinstelling kon niet worden veranderd.';return}toon()});
    toon();
    return;
  }
  if(!eigenBezoek()){
    const script=document.createElement('script');
    script.type='module';
    script.src='https://static.cloudflareinsights.com/beacon.min.js';
    script.setAttribute('data-cf-beacon',JSON.stringify({token:'a68784352ffc4a6c88bf4e51f4404e21',spa:true}));
    document.body.appendChild(script);
  }
  // Eigen testklikken blijven in Awin herkenbaar, maar kunnen daar niet uit de totale klikken worden verwijderd.
  document.addEventListener('click',event=>{
    if(!eigenBezoek())return;
    const target=event.target;
    const link=target instanceof Element?target.closest('a[href]'):null;
    if(!link)return;
    let u;try{u=new URL(link.href)}catch{return}
    if(u.protocol!=='https:'||u.username||u.password)return;
    if(u.hostname==='www.awin1.com'&&['/pclick.php','/cread.php'].includes(u.pathname)&&(u.searchParams.get('a')==='3124230'||u.searchParams.get('awinaffid')==='3124230')){
      u.searchParams.set('clickref','kh_eigen_test');link.href=u.href;
    }else if(['coolblue.nl','www.coolblue.nl'].includes(u.hostname)){
      const a=new URL('https://www.awin1.com/cread.php');
      a.searchParams.set('awinmid','85161');
      a.searchParams.set('awinaffid','3124230');
      a.searchParams.set('ued',u.href);
      a.searchParams.set('clickref','kh_eigen_test');
      link.href=a.href;
      link.rel='sponsored noopener noreferrer';
    }
  },true);
})();
