"""Notify Bing/IndexNow of the public canonical URLs after deployment.

The verification key is intentionally public and grants no site/account access.
Google sitemap submission remains a Search Console operation.
"""
import argparse
import json
from pathlib import Path
import time
from urllib.request import Request, urlopen
from urllib.parse import urlsplit
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent.parent
BASE = 'https://www.prijsjager-nl.nl'
ENDPOINT = 'https://www.bing.com/indexnow'


def payload():
    key = (ROOT / 'indexnow-key.txt').read_text().strip()
    urls = [el.text for el in ET.parse(ROOT / 'sitemap.xml').iter(
        '{http://www.sitemaps.org/schemas/sitemap/0.9}loc')]
    assert len(key) == 32 and all(c in '0123456789abcdef' for c in key)
    assert urls and len(urls) == len(set(urls))
    assert all(urlsplit(u).scheme == 'https' and
               urlsplit(u).netloc == urlsplit(BASE).netloc and
               not urlsplit(u).fragment for u in urls)
    return {'host': urlsplit(BASE).netloc, 'key': key,
            'keyLocation': BASE + '/indexnow-key.txt', 'urlList': urls}


def fetch(url):
    with urlopen(Request(url, headers={'User-Agent': 'KoopHelder-IndexNow/1.0'}), timeout=30) as response:
        return response.read()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--check', action='store_true')
    ap.add_argument('--wait-for-deploy', action='store_true')
    args = ap.parse_args()
    data = payload()
    if args.check:
        print(f'IndexNow configuration valid: {len(data["urlList"])} canonical URLs')
        return
    attempts = 12 if args.wait_for_deploy else 1
    for attempt in range(attempts):
        try:
            assert fetch(data['keyLocation']).decode().strip() == data['key'], 'Key not deployed yet'
            live = ET.fromstring(fetch(BASE + '/sitemap.xml'))
            urls = [el.text for el in live.iter('{http://www.sitemaps.org/schemas/sitemap/0.9}loc')]
            assert urls == data['urlList'], 'Sitemap not deployed yet'
            break
        except Exception:
            if attempt == attempts - 1:
                raise
            time.sleep(20)
    request = Request(ENDPOINT, data=json.dumps(data).encode(), method='POST',
                      headers={'Content-Type': 'application/json; charset=utf-8',
                               'User-Agent': 'KoopHelder-IndexNow/1.0'})
    with urlopen(request, timeout=45) as response:
        assert response.status in (200, 202), response.status
        print(f'IndexNow accepted {len(data["urlList"])} URLs: HTTP {response.status}')
        print('Receipt is not a guarantee of indexing or ranking.')


if __name__ == '__main__':
    main()
