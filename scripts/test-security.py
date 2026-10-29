"""Offline security regressions: never fetch feeds or follow affiliate links."""
import csv
import gzip
import importlib.util
import io
import json
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent
def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

feed = load('feed', 'update-coolblue-prices.py')
security = load('security', 'update-security-policy.py')

HTML = 'const products=' + json.dumps([{'url':'https://www.coolblue.nl/product/123/test.html'}]) + ';'
ROW = {'merchant_id':'85161','merchant_product_id':'123','merchant_deep_link':'https://www.coolblue.nl/product/123/test.html','search_price':'99.95','currency':'EUR','condition':'new','in_stock':'1','merchant_image_url':'https://coolblue.bynder.com/test.jpg'}

def csv_bytes(row):
    out = io.StringIO()
    writer = csv.DictWriter(out, fieldnames=list(ROW))
    writer.writeheader()
    writer.writerows([row] * 100)
    return out.getvalue().encode()

class SecurityTests(unittest.TestCase):
    def test_expected_price_and_official_image(self):
        result = feed.build(gzip.compress(csv_bytes(ROW)), HTML)
        self.assertEqual(result['prices']['123']['price'], 99.95)
        self.assertEqual(result['prices']['123']['imageUrl'], ROW['merchant_image_url'])
    def test_invalid_prices_and_identity_fail_closed(self):
        for field, value in [('merchant_id','1'),('merchant_product_id','456'),('merchant_deep_link','https://www.coolblue.nl/product/456/'),('merchant_deep_link','http://www.coolblue.nl/product/123/'),('merchant_deep_link','https://user@www.coolblue.nl/product/123/'),('merchant_deep_link','https://www.coolblue.nl:444/product/123/'),('search_price','NaN'),('search_price','Infinity'),('search_price','-1'),('currency','USD'),('condition','used'),('in_stock','0')]:
            with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                feed.build(csv_bytes({**ROW,field:value}), HTML)
    def test_untrusted_images_are_removed(self):
        for url in ['javascript:alert(1)','data:text/html,test','http://image.coolblue.nl/a','https://image.coolblue.nl.evil.example/a','https://user@image.coolblue.nl/a','https://coolblue.bynder.com:444/a']:
            with self.subTest(url=url):
                self.assertNotIn('imageUrl',feed.build(csv_bytes({**ROW,'merchant_image_url':url}),HTML)['prices']['123'])
    def test_feed_hosts_are_exact_https_only(self):
        for url in ['http://productdata.awin.com/a','https://productdata.awin.com.evil.example/a','https://key@productdata.awin.com/a','https://productdata.awin.com:444/a','file:///etc/passwd']:
            with self.subTest(url=url), self.assertRaises(ValueError):feed.check_url(url)
    def test_redirects_revalidate_host(self):
        with self.assertRaises(ValueError):
            feed.SafeRedirect().redirect_request(None,None,302,'',{},'https://evil.example/')
    def test_decompression_and_row_limits(self):
        with patch.object(feed,'MAX_FEED_BYTES',20), self.assertRaises(ValueError):
            feed.build(gzip.compress(b'x'*1000),HTML)
        with patch.object(feed,'MAX_FEED_ROWS',10), self.assertRaises(ValueError):
            feed.build(csv_bytes(ROW),HTML)
    def test_csp_hashes_match_exact_scripts(self):
        source=(ROOT.parent/'index.html').read_text() if (ROOT.parent/'index.html').exists() else (ROOT/'index.html').read_text()
        expected=security.policy(source)
        self.assertIn('content="'+expected+'"', source)
        self.assertNotIn("'unsafe-inline'", expected.split('script-src ')[1].split(';')[0])
        self.assertIn("script-src-attr 'none'", expected)
        self.assertIn("base-uri 'none'", expected)
        self.assertIn("form-action 'none'", expected)
        self.assertNotEqual(expected,security.policy(source.replace('<script>', '<script>/* changed */',1)))
    def test_inline_handlers_and_new_external_scripts_rejected(self):
        for source in ['<img onerror="alert(1)">','<script src="https://evil.example/a.js"></script>']:
            with self.subTest(source=source), self.assertRaises(ValueError):security.policy(source)
    def test_local_script_integrity_is_required(self):
        source=(ROOT.parent/'index.html').read_text()
        for changed in [source.replace('integrity="sha256-', 'integrity="sha256-invalid', 1),
                        source.replace('/assets/awin-clickref.js', '/assets/unreviewed.js', 1)]:
            with self.subTest(source=changed[:80]), self.assertRaises(ValueError):
                security.policy(changed)

if __name__=='__main__': unittest.main()
