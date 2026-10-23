"""Refresh authorized Awin shop catalogs. Private download URLs never enter output files or logs."""
import argparse,base64,csv,gzip,hashlib,importlib.util,io,json,math,os,re,sys,tempfile
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import urlsplit,urlunsplit,parse_qs
from urllib.request import Request,build_opener
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('coolblue_prices',ROOT/'scripts/update-coolblue-prices.py');cb=importlib.util.module_from_spec(spec);spec.loader.exec_module(cb)
SHOPS={'smartphonehoesjes':{'mid':'8261','fid':'20671','hosts':{'www.smartphonehoesjes.nl'}},'coolblue':{'mid':'85161','fid':'96636','hosts':{'image.coolblue.nl','coolblue.bynder.com'}},'acer':{'mid':'17133','fid':'36289','hosts':{'static2-ecemea.acer.com'}}}
COLUMNS=['aw_deep_link','product_name','aw_product_id','merchant_product_id','merchant_image_url','merchant_category','search_price','currency','delivery_cost','merchant_deep_link','merchant_id','brand_name','in_stock','condition','stock_status','product_type','large_image','alternate_image','merchant_thumb_url','ean','product_GTIN','upc','mpn']
MAX_BYTES=160_000_000

def acer_type(row):
 name=row['product_name'].lower();category=(row.get('merchant_category') or '').strip()
 if category=='Accessories':return 'Accessoires'
 if re.search(r'\blaptop\b|\bnotebook\b',name):return 'Laptops'
 if category=='Desktops' or re.search(r'\bdesktop\b|all-in-one',name):return 'Desktopcomputers'
 if category=='Monitors' or re.search(r'\bmonitor\b',name):return 'Monitoren'
 if re.search(r'\btablet\b',name):return 'Tablets'
 if re.search(r'\bbeamer\b|\bprojector\b|home cinema|home entertainment|soho (?:laser|lamp)',name):return 'Projectoren'
 if re.search(r'\bwifi\b|\brouter\b',name):return 'Netwerkapparatuur'
 if re.search(r'\bssd\b|usb-stick',name):return 'Opslag'
 return {'Notebooks':'Laptops','Laptops':'Laptops','Tablets':'Tablets','Projectors':'Projectoren','Peripherals':'Randapparatuur'}.get(category,'Elektronica')

def feed_url(base,shop):
 cb.check_url(base)
 u=urlsplit(base);parts=u.path.split('/')
 if u.hostname!='productdata.awin.com' or not u.path.startswith('/datafeed/download/') or 'apikey' not in parts or 'fid' not in parts or 'columns' not in parts:raise ValueError('Unsupported configured feed format')
 for k,v in [('fid',SHOPS[shop]['fid']),('language','nl'),('columns',','.join(COLUMNS)),('format','csv'),('compression','gzip')]:
  if k in parts:parts[parts.index(k)+1]=v
  else:parts.extend([k,v])
 return urlunsplit((u.scheme,u.netloc,'/'.join(parts),'',''))

def read_rows(raw):
 if len(raw)>60_000_000:raise ValueError('Feed too large')
 if raw[:2]==b'\x1f\x8b':
  with gzip.GzipFile(fileobj=io.BytesIO(raw)) as f:raw=f.read(MAX_BYTES+1)
 if len(raw)>MAX_BYTES:raise ValueError('Feed too large')
 reader=csv.DictReader(io.StringIO(raw.decode('utf-8-sig')))
 if not {'merchant_id','product_name','aw_deep_link','search_price','currency'}.issubset(reader.fieldnames or []):raise ValueError('Missing feed columns')
 rows=[]
 for i,r in enumerate(reader):
  if i>=300_000:raise ValueError('Too many products')
  rows.append(r)
 return rows

def build(raw,shop,stamp=None):
 cfg=SHOPS[shop];rows=read_rows(raw);items=[];seen=set()
 for r in rows:
  if r['merchant_id']!=cfg['mid']:raise ValueError('Unexpected merchant')
  u=urlsplit(r['aw_deep_link']);q=parse_qs(u.query)
  if u.scheme!='https' or u.netloc!='www.awin1.com' or u.path!='/pclick.php' or q.get('a')!=['3124230'] or q.get('m')!=[cfg['mid']] or not re.fullmatch(r'\d+',q.get('p',[''])[0]):raise ValueError('Unexpected affiliate link')
  pid=q['p'][0]
  if pid in seen:continue
  seen.add(pid);image=''
  for key in ['merchant_image_url','large_image','alternate_image','merchant_thumb_url']:
   candidate=(r.get(key) or '').strip();v=urlsplit(candidate)
   if v.scheme=='https' and v.hostname in cfg['hosts'] and not v.username and not v.password and v.port in (None,443):image=candidate;break
  price=cb.money(r.get('search_price'));delivery=cb.money(r.get('delivery_cost'))
  if r.get('currency')!='EUR' or price is None or price<=0:price=None
  stock=r.get('in_stock')=='1'
  category=acer_type(r) if shop=='acer' else ((r.get('product_type') or r.get('merchant_category')) if shop=='coolblue' else r.get('merchant_category') or '').strip() or 'Overige producten'
  items.append([r['product_name'].strip(),(r.get('brand_name') or '').strip() or ('Acer' if shop=='acer' else 'Overige merken'),category,image,pid,price,delivery,stock])
 if len(items)<100:raise ValueError('Incomplete feed')
 items.sort(key=lambda p:p[0].casefold());out={};parts=[]
 for start in range(0,len(items),1000):
  payload=gzip.compress(json.dumps(items[start:start+1000],ensure_ascii=False,separators=(',',':')).encode(),mtime=0);name='catalog-'+str(start//1000).zfill(2)+'.json.gz';out[name]=payload;parts.append({'file':name,'count':len(items[start:start+1000]),'sha256':hashlib.sha256(payload).hexdigest()})
 stamp=stamp or datetime.now(timezone.utc).isoformat()
 manifest={'schema':2,'merchantId':cfg['mid'],'publisherId':'3124230','date':stamp[:10],'fetchedAt':stamp,'maxAgeHours':48,'count':len(items),'withImages':sum(bool(p[3]) for p in items),'withPrices':sum(p[5] is not None for p in items),'files':parts}
 out['manifest.json']=json.dumps(manifest,separators=(',',':')).encode()
 return out

def write(outputs,shop):
 target=ROOT/'data'/shop;target.mkdir(parents=True,exist_ok=True)
 for name,raw in outputs.items():(target/name).write_bytes(raw)
 for path in target.glob('catalog-*.json.gz'):
  if path.name not in outputs:path.unlink()

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--smartphonehoesjes-file');ap.add_argument('--coolblue-file');ap.add_argument('--acer-file');a=ap.parse_args();pending={};raws={};stamp=datetime.now(timezone.utc).isoformat()
 try:
  for shop in SHOPS:
   local=getattr(a,shop+'_file')
   if local:raw=Path(local).read_bytes()
   else:
    base=(os.environ.get('AWIN_FEED_URL') or os.environ.get('AWIN_COOLBLUE_FEED_URL') or '').strip()
    if not base:raise ValueError('Feed secret is not configured')
    url=feed_url(base,shop)
    with build_opener(cb.SafeRedirect()).open(Request(url,headers={'User-Agent':'KoopHelder catalog updater'}),timeout=90) as response:raw=response.read(60_000_001)
   pending[shop]=build(raw,shop,stamp);raws[shop]=raw
  # Validate all downloads before changing any published catalog.
  prices=cb.build(raws['coolblue'],(ROOT/'index.html').read_text(),datetime.fromisoformat(stamp))
  matcher_spec=importlib.util.spec_from_file_location('matcher',ROOT/'scripts/match-shop-products.py');matcher=importlib.util.module_from_spec(matcher_spec);matcher_spec.loader.exec_module(matcher)
  matches=matcher.build({shop:read_rows(raw) for shop,raw in raws.items()},SHOPS,stamp)
  for shop,outputs in pending.items():write(outputs,shop);m=json.loads(outputs['manifest.json']);print(shop+': '+str(m['count'])+' products, '+str(m['withPrices'])+' prices, '+str(m['withImages'])+' photos')
  (ROOT/'coolblue-prices.json').write_text(json.dumps(prices,ensure_ascii=False,separators=(',',':'))+'\n')
  (ROOT/'data/product-matches.json').write_text(json.dumps(matches,separators=(',',':'))+'\n')
  print('Exact GTIN product groups across shops: '+str(len(matches['groups'])))
 except Exception as exc:
  safe={'Unsupported configured feed format','Feed too large','Missing feed columns','Too many products','Unexpected merchant','Unexpected affiliate link','Incomplete feed','Feed secret is not configured'}
  print('Catalog refresh failed: '+(str(exc) if isinstance(exc,ValueError) and str(exc) in safe else type(exc).__name__)+'. Existing published data retained. Private URLs are not logged.',file=sys.stderr);raise SystemExit(1)
if __name__=='__main__':main()


