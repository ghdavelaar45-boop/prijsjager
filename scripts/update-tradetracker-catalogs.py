"""Import the approved Dutch TradeTracker feeds; publish only validated product data."""
import argparse,gzip,hashlib,json,math,re,sys
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import urlsplit,parse_qs
from urllib.request import urlopen
ROOT=Path(__file__).resolve().parents[1]
SHOPS={'hobo':('37535','2232033','www.hobo.nl','/tradetracker-redirect/'),'yorcom':('4837','253916','www.yorcom.nl','/shopping/')}
def money(v):
 try:
  n=float(v)
  return n if math.isfinite(n) and 0<=n<=1000000 else None
 except (ValueError,TypeError):return None
def prop(p,k,default=''):
 v=p.get('properties',{}).get(k,[])
 return str(v[0]).strip() if isinstance(v,list) and v else default
def valid_link(url,shop):
 campaign,fid,host,path=SHOPS[shop];u=urlsplit(url);q=parse_qs(u.query)
 if u.scheme!='https' or u.netloc!=host or u.path!=path or q.get('tt')!=[campaign+'_'+fid+'_518245_']:return False
 target=urlsplit(q.get('r',[''])[0])
 return target.scheme=='https' and target.netloc==host and not target.username and not target.password
def build(data,shop,stamp=None):
 campaign,fid,host,path=SHOPS[shop];products=data.get('products');items=[];seen=set()
 if not isinstance(products,list) or not 100<=len(products)<=100000:raise ValueError('Incomplete feed')
 for p in products:
  if str(p.get('campaignID'))!=campaign or not valid_link(p.get('URL',''),shop):raise ValueError('Unexpected product identity or tracking link')
  pid=str(1000000000000000+int(hashlib.sha256((shop+':'+str(p['ID'])).encode()).hexdigest()[:12],16))
  if pid in seen:raise ValueError('Duplicate product identity')
  seen.add(pid);image=''
  for candidate in p.get('images',[]):
   u=urlsplit(candidate)
   if u.scheme=='https' and u.netloc==host and not u.username and not u.password:image=candidate;break
  price=money(p.get('price',{}).get('amount')) if p.get('price',{}).get('currency')=='EUR' else None
  if price==0:price=None
  category=prop(p,'categoryPath') or prop(p,'subcategories') or 'Overige producten'
  # Merchant category paths retain actual product types rather than guessed specifications.
  category=re.split(r'\s*>\s*|\s*/\s*',category)[-1].strip() or 'Overige producten'
  stock=prop(p,'stock').lower() in {'ja','yes','1','in stock','op voorraad','true'}
  items.append([str(p.get('name','')).strip(),prop(p,'brand','Overige merken'),category,image,pid,price,money(prop(p,'deliveryCosts_NL') or prop(p,'deliveryCosts')),stock,p['URL']])
 if any(not p[0] for p in items):raise ValueError('Missing product name')
 items.sort(key=lambda p:p[0].casefold());out={};files=[]
 for start in range(0,len(items),1000):
  raw=gzip.compress(json.dumps(items[start:start+1000],ensure_ascii=False,separators=(',',':')).encode(),mtime=0);name='catalog-'+str(start//1000).zfill(2)+'.json.gz';out[name]=raw;files.append({'file':name,'count':len(items[start:start+1000]),'sha256':hashlib.sha256(raw).hexdigest()})
 stamp=stamp or datetime.now(timezone.utc).isoformat()
 out['manifest.json']=json.dumps({'schema':2,'network':'tradetracker','merchantId':campaign,'publisherId':'518245','fetchedAt':stamp,'maxAgeHours':48,'count':len(items),'withPrices':sum(p[5] is not None for p in items),'withImages':sum(bool(p[3]) for p in items),'files':files},separators=(',',':')).encode()
 return out
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--hobo-file');ap.add_argument('--yorcom-file');a=ap.parse_args();pending={};stamp=datetime.now(timezone.utc).isoformat()
 for shop,(_,fid,_,_) in SHOPS.items():
  local=getattr(a,shop+'_file')
  if local:raw=Path(local).read_bytes()
  else:
   with urlopen('https://pf.tradetracker.net/?aid=518245&encoding=utf-8&type=json&fid='+fid+'&categoryType=2&additionalType=2',timeout=90) as r:raw=r.read(50000001)
  if len(raw)>50000000:raise ValueError('Feed too large')
  pending[shop]=build(json.loads(raw),shop,stamp)
 for shop,outputs in pending.items():
  target=ROOT/'data'/shop;target.mkdir(parents=True,exist_ok=True)
  for name,raw in outputs.items():(target/name).write_bytes(raw)
  for p in target.glob('catalog-*.json.gz'):
   if p.name not in outputs:p.unlink()
  m=json.loads(outputs['manifest.json']);print(shop+': '+str(m['count'])+' products, '+str(m['withPrices'])+' prices, '+str(m['withImages'])+' photos')
if __name__=='__main__':main()
