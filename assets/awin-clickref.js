'use strict';
(() => {
  // Privacyvriendelijke indeling van bestaande Awin-klikken; geen extra trackingverzoeken.
  const merchants = { '85161': 'coolblue', '8261': 'hoesjes', '17133': 'acer' };
  const ownHosts = ['mijnkoophelder.nl','www.mijnkoophelder.nl','prijsjager-nl.nl','www.prijsjager-nl.nl'];
  if (!ownHosts.includes(location.hostname)) return;
  document.addEventListener('click', event => {
    const el = event.target;
    const link = el instanceof Element ? el.closest('a[href]') : null;
    if (!link) return;
    let url;
    try { url = new URL(link.href); } catch { return; }
    if (url.protocol !== 'https:' || url.username || url.password || (url.port && url.port !== '443')) return;
    const place = link.closest('#guideCards,#guideResults') ? 'keuzehulp' :
      link.closest('.exactOffers,#comparison') ? 'vergelijken' :
      link.closest('#detailModal') ? 'details' :
      link.closest('#producten') ? 'catalogus' : 'overig';
    const ref = (shop) => 'kh_' + place + '_' + shop;
    if (url.hostname === 'www.awin1.com' && ['/pclick.php','/cread.php'].includes(url.pathname)) {
      const id = url.searchParams.get('m') || url.searchParams.get('awinmid');
      const account = url.searchParams.get('a') || url.searchParams.get('awinaffid');
      if (account !== '3124230' || !merchants[id] || url.searchParams.has('clickref')) return;
      url.searchParams.set('clickref', ref(merchants[id]));
      link.href = url.href;
    } else if (['www.coolblue.nl','coolblue.nl'].includes(url.hostname)) {
      const awin = new URL('https://www.awin1.com/cread.php');
      awin.searchParams.set('awinmid','85161');
      awin.searchParams.set('awinaffid','3124230');
      awin.searchParams.set('ued', url.href);
      awin.searchParams.set('clickref', ref('coolblue'));
      link.href = awin.href;
      link.rel = 'sponsored noopener noreferrer';
    }
  }, true);
})();
