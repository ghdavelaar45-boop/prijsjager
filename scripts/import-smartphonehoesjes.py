"""Import an official Awin CSV download; never store its private download URL."""
import csv,gzip,json,re,sys,hashlib
from pathlib import Path
from urllib.parse import urlsplit,parse_qs
root=Path(__file__).resolve().parents[1]
coolblue=len(sys.argv)>2 and sys.argv[2]=='coolblue'
merchant='85161' if coolblue else '8261'
dirname='coolblue' if coolblue else 'smartphonehoesjes'
items=[];seen=set()
with gzip.open(sys.argv[1],'rt',encoding='utf-8-sig') as f:
 for row in csv.DictReader(f):
  if row['merchant_id']!=merchant: raise ValueError('Unexpected merchant')
  u=urlsplit(row['aw_deep_link']);q=parse_qs(u.query)
  if u.scheme!='https' or u.netloc!='www.awin1.com' or u.path!='/pclick.php' or q.get('a')!=['3124230'] or q.get('m')!=[merchant] or not re.fullmatch(r'\d+',q.get('p',[''])[0]):raise ValueError('Unexpected affiliate link')
  pid=q['p'][0]
  if pid in seen:continue
  seen.add(pid)
  image=row['merchant_image_url']; im=urlsplit(image)
  if not(im.scheme=='https' and (im.netloc in {'image.coolblue.nl','coolblue.bynder.com'} if coolblue else im.netloc=='www.smartphonehoesjes.nl' and im.path.startswith('/media/'))):image=''
  items.append([row['product_name'].strip(),row['brand_name'].strip() or 'Overige merken',(row.get('product_type','') if coolblue else row['merchant_category']).strip(),image,pid])
items.sort(key=lambda p:p[0].casefold())
out=root/'data'/dirname;out.mkdir(parents=True,exist_ok=True)
files=[]
for start in range(0,len(items),1000):
 name=f'catalog-{start//1000:02d}.json.gz';raw=json.dumps(items[start:start+1000],ensure_ascii=False,separators=(',',':')).encode();payload=gzip.compress(raw,mtime=0)
 (out/name).write_bytes(payload);files.append({'file':name,'count':len(items[start:start+1000]),'sha256':hashlib.sha256(payload).hexdigest()})
(out/'manifest.json').write_text(json.dumps({'schema':1,'merchantId':merchant,'publisherId':'3124230','date':'2026-10-22','count':len(items),'files':files},separators=(',',':')))
print(json.dumps({'count':len(items),'parts':len(files),'compressedBytes':sum((out/x['file']).stat().st_size for x in files)}))
