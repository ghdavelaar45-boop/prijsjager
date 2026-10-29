"""Maintain the exact inline-script hashes in the static site's CSP.

Run after any JavaScript edit; --check fails rather than silently relaxing CSP.
GitHub Pages does not apply _headers or server directives from this repository.
"""
import argparse
import base64
import hashlib
import re
from html.parser import HTMLParser
from pathlib import Path

class Scripts(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.inline = []
        self.current = None
        self.external = []
        self.integrity = {}
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if any(k.lower().startswith('on') for k in attrs):
            raise ValueError('Inline event attributes are forbidden')
        if tag == 'script':
            if attrs.get('src'):
                self.external.append(attrs['src'])
                self.integrity[attrs['src']] = attrs.get('integrity')
            else:
                self.current = []
    def handle_data(self, data):
        if self.current is not None:
            self.current.append(data)
    def handle_endtag(self, tag):
        if tag == 'script' and self.current is not None:
            self.inline.append(''.join(self.current))
            self.current = None

def policy(source):
    parsed = Scripts()
    parsed.feed(source)
    beacon = 'https://static.cloudflareinsights.com/beacon.min.js'
    local_scripts = ['/assets/awin-clickref.js', '/assets/kh-bezoekers.js']
    if parsed.external != local_scripts:
        raise ValueError('Review new external scripts before allowing them')
    hashes = ["'sha256-" + base64.b64encode(hashlib.sha256(s.encode()).digest()).decode() + "'" for s in parsed.inline]
    for src in local_scripts:
        digest = 'sha256-' + base64.b64encode(hashlib.sha256((Path(__file__).resolve().parents[1] / src.lstrip('/')).read_bytes()).digest()).decode()
        if parsed.integrity[src] != digest:
            raise ValueError('Local script integrity does not match: ' + src)
        hashes.append("'" + digest + "'")
    return '; '.join([
        "default-src 'none'",
        "base-uri 'none'",
        "object-src 'none'",
        "script-src " + ' '.join(hashes + [beacon]),
        "script-src-attr 'none'",
        "style-src 'self' 'unsafe-inline'",
        "img-src 'self' data: https://image.coolblue.nl https://coolblue.bynder.com https://www.smartphonehoesjes.nl https://static2-ecemea.acer.com https://www.hobo.nl https://www.yorcom.nl",
        "connect-src 'self' https://cloudflareinsights.com",
        "form-action 'none'",
        "upgrade-insecure-requests",
    ])

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--check', action='store_true')
    ap.add_argument('--html', default='index.html')
    args = ap.parse_args()
    path = Path(args.html)
    source = path.read_text(encoding='utf-8')
    # Keep charset first and the policy before all executable content/resources.
    source = re.sub(r'\n?<meta http-equiv="Content-Security-Policy"[^>]*>', '', source)
    source = re.sub(r'\n?<meta name="referrer"[^>]*>', '', source)
    marker = '<meta charset="utf-8"/>'
    if source.count(marker) != 1:
        raise ValueError('Expected one UTF-8 charset marker')
    replacement = marker + '\n<meta http-equiv="Content-Security-Policy" content="' + policy(source) + '">\n<meta name="referrer" content="no-referrer">'
    updated = source.replace(marker, replacement, 1)
    if args.check:
        if updated != path.read_text(encoding='utf-8'):
            raise SystemExit('CSP differs: run python3 scripts/update-security-policy.py')
        print('CSP verified: only exact site scripts and the analytics beacon are allowed')
    else:
        path.write_text(updated, encoding='utf-8')

if __name__ == '__main__':
    main()


