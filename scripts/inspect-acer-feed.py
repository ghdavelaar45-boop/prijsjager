"""Inspect the authorized Acer feed without logging private URLs or API keys."""
import csv,gzip,io,os,json,re
from collections import Counter
from urllib.parse import urlsplit,parse_qs
from urllib.request import build_opener,Request
import importlib.util
from pathlib import Path
spec=importlib.util.spec_from_file_location('shops',Path(__file__).with_name('update-shop-catalogs.py'));shops=importlib.util.module_from_spec(spec);spec.loader.exec_module(shops)
def main():
 base=os.environ['AWIN_FEED_URL'];shops.cb.check_url(base);parts=urlsplit(base).path.split('/');key=parts[parts.index('apikey')+1]
 opener=build_opener(shops.cb.SafeRedirect())
 with opener.open(Request('https://productdata.awin.com/datafeed/list/apikey/'+key),timeout=90) as res:raw=res.read(15_000_001)
 if len(raw)>15_000_000:raise ValueError('List too large')
 rows=list(csv.DictReader(io.StringIO(raw.decode('utf-8-sig'))))
 norm=lambda s:re.sub('[^a-z0-9]','',s.lower())
 selected=[]
 for row in rows:
  r={norm(k):v for k,v in row.items() if k}
  if r.get('advertiserid')=='17133':selected.append(r)
 print('Acer accessible feeds:',json.dumps([{k:v for k,v in r.items() if k not in {'url','downloadurl'}} for r in selected]))
 for r in selected:
  fid=r.get('feedid','');status=r.get('membershipstatus','').lower()
  if not fid.isdigit() or status not in {'joined','active'} or fid!='36289':continue
  shops.SHOPS['acer']={'mid':'17133','fid':fid,'hosts':set()}
  with opener.open(Request(shops.feed_url(base,'acer')),timeout=90) as res:data=res.read(60_000_001)
  items=shops.read_rows(data)
  print('Acer feed metadata:',json.dumps({'feedId':fid,'count':len(items),'merchants':dict(Counter(x.get('merchant_id') for x in items)),'imageHosts':dict(Counter(urlsplit(x.get('merchant_image_url','')).hostname for x in items)),'linkHosts':dict(Counter(urlsplit(x.get('aw_deep_link','')).hostname for x in items)),'linkPaths':dict(Counter(urlsplit(x.get('aw_deep_link','')).path for x in items)),'types':dict(Counter(x.get('product_type','') for x in items)),'samples':[{k:x.get(k) for k in ['product_name','brand_name','merchant_category','search_price','in_stock']} for x in items[:3]]}))
if __name__=='__main__':
 try:main()
 except Exception as e:print('Acer inspection failed: '+type(e).__name__);raise SystemExit(1)
