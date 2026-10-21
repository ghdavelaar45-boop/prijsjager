"""Publish only exact, in-stock, new Coolblue product prices; never publish the feed URL."""
import argparse, csv, gzip, io, json, os, re, sys
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from urllib.parse import urlparse
from urllib.error import HTTPError, URLError
from urllib.request import urlopen, Request, HTTPRedirectHandler, build_opener

ALLOWED = {'productdata.awin.com', 'ui.awin.com'}
class SafeRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        check_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)
def check_url(url):
    u = urlparse(url)
    if u.scheme != 'https' or u.hostname not in ALLOWED or u.username or u.password:
        raise ValueError('Unsupported feed host')
def configured_feed_url(url):
    """Request the validation columns without logging or changing the feed key."""
    url = url.strip()
    check_url(url)
    u = urlparse(url)
    parts = u.path.split('/')
    if u.hostname == 'productdata.awin.com' and u.path.startswith('/datafeed/download/'):
        if 'columns' not in parts:
            raise ValueError('Missing required feed columns')
        pos = parts.index('columns') + 1
        if pos >= len(parts):
            raise ValueError('Missing required feed columns')
        columns = [x for x in parts[pos].split(',') if x]
        for name in ['merchant_id','merchant_product_id','merchant_deep_link','search_price','currency','condition','in_stock','stock_status','delivery_cost','ean','merchant_image_url']:
            if name not in columns: columns.append(name)
        parts[pos] = ','.join(columns)
        return u._replace(path='/'.join(parts)).geturl()
    return url
def money(value):
    try:
        n = Decimal(value)
        return float(n) if n.is_finite() and 0 <= n <= 1000000 else None
    except (InvalidOperation, TypeError):
        return None
def product_id(url):
    u = urlparse(url)
    return re.match(r'^/product/(\d+)(?:/|$)', u.path).group(1) if u.hostname in {'coolblue.nl','www.coolblue.nl'} and re.match(r'^/product/(\d+)(?:/|$)',u.path) else None
def build(raw, html, now=None):
    if raw[:2] == b'\x1f\x8b': raw = gzip.decompress(raw)
    products = json.loads(re.search(r'const products=(\[[\s\S]*?\]);',html).group(1))
    wanted = {i for p in products for o in p.get('offers',[{'url':p['url']}]) if (i:=product_id(o['url']))}
    rows = csv.DictReader(io.StringIO(raw.decode('utf-8-sig')))
    required={'merchant_id','merchant_product_id','merchant_deep_link','search_price','currency','condition','in_stock'}
    if not required.issubset(rows.fieldnames or []): raise ValueError('Missing required feed columns')
    result={}; conflicts=set(); count=0
    for r in rows:
        count+=1; pid=r['merchant_product_id'].strip()
        if pid not in wanted or r['merchant_id']!='85161' or product_id(r['merchant_deep_link'])!=pid: continue
        price=money(r['search_price'])
        if r['currency']!='EUR' or r['condition'].lower()!='new' or r['in_stock']!='1' or price is None or price<=0: continue
        item={'price':price,'currency':'EUR','deliveryCost':money(r.get('delivery_cost','')),'inStock':True}
        image_url=(r.get('merchant_image_url') or '').strip()
        image=urlparse(image_url)
        if image.scheme=='https' and image.hostname in {'image.coolblue.nl','coolblue.bynder.com'} and not image.username and not image.password:
            item['imageUrl']=image_url
        if pid in result and result[pid]!=item: conflicts.add(pid)
        result[pid]=item
    for pid in conflicts: result.pop(pid,None)
    if count<100 or not result: raise ValueError('Feed incomplete or no exact matches')
    return {'schema':1,'imageSource':'Awin Coolblue productfeed','merchant':'Coolblue','merchantId':'85161','fetchedAt':(now or datetime.now(timezone.utc)).isoformat(),'maxAgeHours':48,'prices':dict(sorted(result.items()))}
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--feed-file');ap.add_argument('--html',default='index.html');ap.add_argument('--output',default='coolblue-prices.json');a=ap.parse_args()
    stage='feed configuration'
    try:
        if a.feed_file: raw=Path(a.feed_file).read_bytes()
        else:
            url=configured_feed_url(os.environ.get('AWIN_COOLBLUE_FEED_URL',''))
            stage='feed download'
            with build_opener(SafeRedirect()).open(Request(url,headers={'User-Agent':'KoopHelder feed updater'}),timeout=90) as response: raw=response.read(60000001)
        if len(raw)>60000000: raise ValueError('Feed too large')
        stage='feed validation'
        data=build(raw,Path(a.html).read_text());target=Path(a.output);tmp=target.with_suffix('.tmp');tmp.write_text(json.dumps(data,ensure_ascii=False,separators=(',',':'))+'\n');tmp.replace(target)
        print('Published',len(data['prices']),'exact Coolblue prices')
    except Exception as exc:
        safe_reasons={'Unsupported feed host','Missing required feed columns','Feed incomplete or no exact matches','Feed too large'}
        if isinstance(exc, HTTPError): reason='HTTP status '+str(exc.code)
        elif isinstance(exc, ValueError) and str(exc) in safe_reasons: reason=str(exc)
        elif isinstance(exc, URLError): reason='Network connection failed'
        else: reason=type(exc).__name__
        print('Price refresh failed at '+stage+': '+reason+'. Previous data retained. Feed URLs are never logged.',file=sys.stderr);sys.exit(1)
if __name__=='__main__': main()

