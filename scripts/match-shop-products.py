"""Match new, single products using validated GTINs; never guess from titles."""
import re,json,unicodedata
from collections import defaultdict
from urllib.parse import urlsplit,parse_qs

def gtin(value):
 value=str(value or '').strip()
 if not re.fullmatch(r'\d{8}|\d{12,14}',value) or len(set(value))==1:return None
 digits=list(map(int,value))
 if (sum(n*(3 if i%2==0 else 1) for i,n in enumerate(reversed(digits[:-1])))+digits[-1])%10:return None
 return value.zfill(14)

def brand(value):
 return re.sub(r'[^a-z0-9]','',unicodedata.normalize('NFKD',str(value)).encode('ascii','ignore').decode().lower())

def build(feeds,configs,stamp):
 groups=defaultdict(dict)
 for source,rows in feeds.items():
  for row in rows:
   if str(row.get('condition','')).strip().lower() not in {'new','nieuw','neu'}:continue
   name=row.get('product_name','')
   if re.search(r'\bbundle\b|\bbundel\b|\bcombo\b|\bset met\b|\s\+\s',name,re.I):continue
   values={v for k in ['ean','product_GTIN','upc'] if (v:=gtin(row.get(k)))}
   if len(values)!=1:continue
   maker=brand(row.get('brand_name') or ('Acer' if source=='acer' else ''))
   if not maker or maker in {'overigemerken','unknown','generic'}:continue
   u=urlsplit(row.get('aw_deep_link',''));q=parse_qs(u.query)
   if u.scheme!='https' or u.netloc!='www.awin1.com' or u.path!='/pclick.php' or q.get('a')!=['3124230'] or q.get('m')!=[configs[source]['mid']]:continue
   pid=q.get('p',[''])[0]
   if not pid.isdigit():continue
   key=(next(iter(values)),maker);groups[key][(source,pid)]={'source':source,'id':pid,'mpn':str(row.get('mpn') or '').strip().upper()}
 out=[]
 for (code,maker),members in sorted(groups.items()):
  items=list(members.values());sources={x['source'] for x in items}
  # Ambiguous same-shop variants and conflicting manufacturer codes are not merged.
  if len(sources)<2 or len(sources)!=len(items):continue
  mpns={x['mpn'] for x in items if x['mpn']}
  if len(mpns)>1:continue
  out.append({'gtin':code,'brand':maker,'condition':'new','members':[[x['source'],x['id']] for x in sorted(items,key=lambda x:x['source'])]})
 return {'schema':1,'publisherId':'3124230','fetchedAt':stamp,'method':'validated-gtin-brand-new','groups':out}
