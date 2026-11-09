"""Refresh authorized Awin shop catalogs. Private download URLs never enter output files or logs."""
import argparse,base64,csv,gzip,hashlib,importlib.util,io,json,math,os,re,sys,tempfile
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import urlsplit,urlunsplit,parse_qs,quote,unquote
from urllib.request import Request,build_opener
from urllib.error import HTTPError
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('coolblue_prices',ROOT/'scripts/update-coolblue-prices.py');cb=importlib.util.module_from_spec(spec);spec.loader.exec_module(cb)
SHOPS={'smartphonehoesjes':{'mid':'8261','fid':'20671','hosts':{'www.smartphonehoesjes.nl'}},'coolblue':{'mid':'85161','fid':'96636','hosts':{'image.coolblue.nl','coolblue.bynder.com'}},'acer':{'mid':'17133','fid':'36289','hosts':{'static2-ecemea.acer.com'}}}
SHOPS['dutchplaza']={'mid':'127667','fid':'116143','hosts':{'cdn.webshopapp.com'},'optional':True}
SHOPS['mobielnl']={'mid':'8373','hosts':{'www.mobiel.nl','mobiel-product.imgix.net','product.mobiel.nl'},'optional':True}
COLUMNS=['aw_deep_link','product_name','aw_product_id','merchant_product_id','merchant_image_url','merchant_category','search_price','currency','delivery_cost','merchant_deep_link','merchant_id','brand_name','in_stock','condition','stock_status','product_type','large_image','alternate_image','merchant_thumb_url','ean','product_GTIN','upc','mpn']
MAX_BYTES=160_000_000
MOBIEL_COLUMNS=['merchant_id','merchant_deep_link','aw_deep_link','product_name','brand_name',
               'merchant_image_url','search_price','currency','delivery_cost','in_stock',
               'condition','ean','product_GTIN','upc','mpn']

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

def dutch_plaza_type(row):
 category=(row.get('merchant_category') or '').split(' > ',1)[0].strip()
 name=row['product_name']
 if category=='Computers & Laptops' and re.search(r'\b(?:laptop|macbook|galaxy book|notebook)',name,re.I):return 'Laptops'
 if category=='Beeld & Geluid':
  if re.search(r'\b(?:AirPods|Galaxy Buds)',name,re.I):return 'Oordopjes'
  if re.search(r'\b(?:monitor|ThinkVision|Dell Pro P P\d)',name,re.I):return 'Monitoren'
 return category or 'Overige producten'

def feed_url(base,shop,fid=None,columns=COLUMNS):
 cb.check_url(base)
 u=urlsplit(base);parts=u.path.split('/')
 if u.hostname!='productdata.awin.com' or not u.path.startswith('/datafeed/download/') or 'apikey' not in parts or 'fid' not in parts or 'columns' not in parts:raise ValueError('Unsupported configured feed format')
 for k,v in [('fid',fid or SHOPS[shop]['fid']),('language','nl'),('columns',','.join(columns)),('format','csv'),('compression','gzip')]:
  if k in parts:parts[parts.index(k)+1]=v
  else:parts.extend([k,v])
 return urlunsplit((u.scheme,u.netloc,'/'.join(parts),'',''))

def mobiel_feed_ids(raw):
 data=raw.decode('utf-8-sig')
 try: dialect=csv.Sniffer().sniff(data.splitlines()[0],delimiters=',;\t')
 except (csv.Error,IndexError):raise ValueError('Unrecognized Awin feed list')
 listing=csv.DictReader(io.StringIO(data),dialect=dialect)
 ids=[]
 for entry in listing:
  row={re.sub(r'[^a-z0-9]','',key.lower()):str(value or '').strip()
       for key,value in entry.items() if key is not None}
  if (row.get('advertiserid') or row.get('merchantid'))!=SHOPS['mobielnl']['mid']:continue
  if row.get('membershipstatus','').lower() not in {'active','joined'}:continue
  fmt=(row.get('datafeedformat') or '').lower()
  if fmt and fmt not in {'awin','legacy'}:continue
  fid=row.get('feedid') or row.get('datafeedid') or ''
  if re.fullmatch(r'[0-9]+',fid) and fid not in ids:ids.append(fid)
 if not ids:raise ValueError('No active Mobiel.nl Awin feed found')
 return ids

def mobiel_phone(row):
 destination=row.get('merchant_deep_link') or ''
 if '/los-toestel' not in destination:return False
 u=urlsplit(destination)
 if u.scheme!='https' or u.netloc not in {'www.mobiel.nl','mobiel.nl'}:return False
 if not re.fullmatch(r'/smartphone/[^/]+/[^/]+(?:/[^/]+)*/los-toestel/?',u.path):return False
 name=row.get('product_name') or ''
 if re.search(r'\b(?:abonnement|sim[ -]?only|refurbished|tweedehands|renewed|bundle|bundel)\b|\s\+\s',name,re.I):return False
 return True

def download(url,limit):
 with build_opener(cb.SafeRedirect()).open(Request(url,headers={'User-Agent':'KoopHelder catalog updater'}),timeout=90) as response:
  data=response.read(limit+1)
 if len(data)>limit:raise ValueError('Feed too large')
 return data

def mobiel_rows(base):
 cb.check_url(base)
 parts=urlsplit(base).path.split('/')
 if 'apikey' not in parts or parts.index('apikey')+1>=len(parts):raise ValueError('Unsupported configured feed format')
 key=quote(unquote(parts[parts.index('apikey')+1]),safe='')
 listing=download('https://ui.awin.com/productdata-darwin-download/publisher/3124230/'+key+'/1/feedList',20_000_000)
 rows=[]
 for fid in mobiel_feed_ids(listing):
  url=feed_url(base,'mobielnl',fid,MOBIEL_COLUMNS)
  with build_opener(cb.SafeRedirect()).open(Request(url,headers={'User-Agent':'KoopHelder catalog updater'}),timeout=90) as response:
   if int(response.headers.get('Content-Length') or 0)>650_000_000:raise ValueError('Feed too large')
   with io.BufferedReader(response) as payload:
    stream=gzip.GzipFile(fileobj=payload) if payload.peek(2).startswith(b'\x1f\x8b') else payload
    with io.TextIOWrapper(stream,encoding='utf-8-sig',newline='') as text:
     append_mobiel_phones(text,rows)
 print('Mobiel.nl: '+str(len(rows))+' standalone rows selected from Awin')
 return rows

def append_mobiel_phones(text,rows):
 reader=csv.DictReader(text)
 if not {'merchant_id','merchant_deep_link','product_name','aw_deep_link','search_price','currency'}.issubset(reader.fieldnames or []):
  raise ValueError('Missing feed columns')
 for i,row in enumerate(reader):
  if i>=8_000_000 or len(rows)>=50_000:raise ValueError('Too many products')
  if mobiel_phone(row):rows.append(row)

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
 cfg=SHOPS[shop];rows=read_rows(raw) if isinstance(raw,bytes) else raw;items=[];seen=set()
 for r in rows:
  if r['merchant_id']!=cfg['mid']:raise ValueError('Unexpected merchant')
  if shop=='mobielnl' and not mobiel_phone(r):continue
  u=urlsplit(r['aw_deep_link']);q=parse_qs(u.query)
  if u.scheme!='https' or u.netloc!='www.awin1.com' or u.path!='/pclick.php' or q.get('a')!=['3124230'] or q.get('m')!=[cfg['mid']] or not re.fullmatch(r'\d+',q.get('p',[''])[0]):raise ValueError('Unexpected affiliate link')
  pid=q['p'][0]
  if pid in seen:continue
  seen.add(pid);image=''
  for key in ['merchant_image_url','large_image','alternate_image','merchant_thumb_url']:
   candidate=(r.get(key) or '').strip();v=urlsplit(candidate)
   if v.scheme=='https' and v.hostname in cfg['hosts'] and not v.username and not v.password and v.port in (None,443) and (shop!='dutchplaza' or v.path.startswith('/shops/328120/files/')):image=candidate;break
  price=cb.money(r.get('search_price'));delivery=cb.money(r.get('delivery_cost'))
  if r.get('currency')!='EUR' or price is None or price<=0:price=None
  stock=r.get('in_stock')=='1'
  category='Smartphones' if shop=='mobielnl' else dutch_plaza_type(r) if shop=='dutchplaza' else acer_type(r) if shop=='acer' else ((r.get('product_type') or r.get('merchant_category')) if shop=='coolblue' else r.get('merchant_category') or '').strip() or 'Overige producten'
  items.append([r['product_name'].strip(),(r.get('brand_name') or '').strip() or ('Acer' if shop=='acer' else 'Overige merken'),category,image,pid,price,delivery,stock])
 if len(items)<(1 if cfg.get('optional') else 100):raise ValueError('Incomplete feed')
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
 ap=argparse.ArgumentParser()
 for shop in SHOPS:ap.add_argument('--'+shop+'-file',dest=shop+'_file')
 ap.add_argument('--tradetracker-match-file');a=ap.parse_args();pending={};raws={};stamp=os.environ.get('KOOPHELDER_CATALOG_STAMP') or datetime.now(timezone.utc).isoformat()
 try:
  for shop in SHOPS:
   try:
    local=getattr(a,shop+'_file')
    if local:raw=Path(local).read_bytes()
    else:
     base=(os.environ.get('AWIN_FEED_URL') or os.environ.get('AWIN_COOLBLUE_FEED_URL') or '').strip()
     if not base:raise ValueError('Feed secret is not configured')
     raw=mobiel_rows(base) if shop=='mobielnl' else download(feed_url(base,shop),60_000_000)
    pending[shop]=build(raw,shop,stamp)
    raws[shop]=raw
   except Exception as exc:
    safe_reasons={'Unsupported configured feed format','Feed too large','Missing feed columns',
                  'Too many products','Unexpected merchant','Unexpected affiliate link','Incomplete feed',
                  'Feed secret is not configured','Unrecognized Awin feed list','No active Mobiel.nl Awin feed found'}
    if isinstance(exc,HTTPError):
     print('Awin feed download failed for '+shop+': HTTP '+str(exc.code)+'. No private URL or token logged.',file=sys.stderr)
    else:
     reason=str(exc) if isinstance(exc,ValueError) and str(exc) in safe_reasons else type(exc).__name__
     print('Catalog processing failed for '+shop+': '+reason+'. No private URL or token logged.',file=sys.stderr)
    if not SHOPS[shop].get('optional'):raise
    print(shop+' feed unavailable; retained the previous catalog.',file=sys.stderr)
  # Validate all downloads before changing any published catalog.
  prices=cb.build(raws['coolblue'],(ROOT/'index.html').read_text(),datetime.fromisoformat(stamp))
  matcher_spec=importlib.util.spec_from_file_location('matcher',ROOT/'scripts/match-shop-products.py');matcher=importlib.util.module_from_spec(matcher_spec);matcher_spec.loader.exec_module(matcher)
  feeds={shop:read_rows(raw) if isinstance(raw,bytes) else raw for shop,raw in raws.items()}
  if 'mobielnl' in feeds:feeds['mobielnl']=[r for r in feeds['mobielnl'] if mobiel_phone(r)]
  matches=matcher.build({shop:rows for shop,rows in feeds.items() if not SHOPS[shop].get('optional')},SHOPS,stamp)
  groups={(g['gtin'],g['brand']):g for g in matches['groups']}
  if any(SHOPS[shop].get('optional') for shop in feeds):
   groups.update(((g['gtin'],g['brand']),g) for g in matcher.build(feeds,SHOPS,stamp)['groups'])
  if a.tradetracker_match_file:
   tt_spec=importlib.util.spec_from_file_location('trade_catalogs',ROOT/'scripts/update-tradetracker-catalogs.py');trade=importlib.util.module_from_spec(tt_spec);tt_spec.loader.exec_module(trade)
   candidates=json.loads(Path(a.tradetracker_match_file).read_text())
   feeds.update({shop:candidates[shop] for shop in trade.SHOPS})
   groups.update(((g['gtin'],g['brand']),g) for g in matcher.build(feeds,SHOPS,stamp,trade.valid_link)['groups'])
  matches['groups']=[groups[k] for k in sorted(groups)]
  for shop,outputs in pending.items():write(outputs,shop);m=json.loads(outputs['manifest.json']);print(shop+': '+str(m['count'])+' products, '+str(m['withPrices'])+' prices, '+str(m['withImages'])+' photos')
  (ROOT/'coolblue-prices.json').write_text(json.dumps(prices,ensure_ascii=False,separators=(',',':'))+'\n')
  (ROOT/'data/product-matches.json').write_text(json.dumps(matches,separators=(',',':'))+'\n')
  print('Exact GTIN product groups across shops: '+str(len(matches['groups'])))
 except Exception as exc:
  safe={'Unsupported configured feed format','Feed too large','Missing feed columns','Too many products','Unexpected merchant','Unexpected affiliate link','Incomplete feed','Feed secret is not configured'}
  print('Catalog refresh failed: '+(str(exc) if isinstance(exc,ValueError) and str(exc) in safe else type(exc).__name__)+'. Existing published data retained. Private URLs are not logged.',file=sys.stderr);raise SystemExit(1)
if __name__=='__main__':main()


