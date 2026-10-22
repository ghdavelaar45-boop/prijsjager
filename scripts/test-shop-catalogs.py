import importlib.util,csv,io,gzip,json,unittest
from pathlib import Path
p=Path(__file__).with_name('update-shop-catalogs.py');spec=importlib.util.spec_from_file_location('shops',p);shops=importlib.util.module_from_spec(spec);spec.loader.exec_module(shops)
ROW={'merchant_id':'8261','product_name':'Example phone cover','aw_deep_link':'https://www.awin1.com/pclick.php?p=123&a=3124230&m=8261','merchant_image_url':'https://www.smartphonehoesjes.nl/media/a.jpg','search_price':'12.50','delivery_cost':'0','currency':'EUR','in_stock':'1','brand_name':'Example','merchant_category':'Phone Cover'}
def feed(row):
 s=io.StringIO();w=csv.DictWriter(s,fieldnames=list(row));w.writeheader()
 for i in range(100):w.writerow({**row,'aw_deep_link':row['aw_deep_link'].replace('p=123','p='+str(i))})
 return gzip.compress(s.getvalue().encode())
def rows(result):return json.loads(gzip.decompress(result['catalog-00.json.gz']))
class CatalogTests(unittest.TestCase):
 def test_price_and_official_photo(self):
  result=shops.build(feed(ROW),'smartphonehoesjes','2026-10-22T10:00:00+00:00');r=rows(result);self.assertEqual(r[0][5],12.5);self.assertEqual(r[0][6],0);self.assertTrue(r[0][7]);self.assertEqual(json.loads(result['manifest.json'])['schema'],2)
 def test_unsafe_images_removed(self):
  for url in ['https://www.smartphonehoesjes.nl.evil.com/a','javascript:alert(1)','http://www.smartphonehoesjes.nl/media/a.jpg','https://user@www.smartphonehoesjes.nl/a']:
   with self.subTest(url=url):self.assertEqual(rows(shops.build(feed({**ROW,'merchant_image_url':url}),'smartphonehoesjes'))[0][3],'')
 def test_wrong_shop_and_tracking_rejected(self):
  for change in [{'merchant_id':'2'},{'aw_deep_link':'https://evil.example/?p=123'}]:
   with self.subTest(change=change),self.assertRaises(ValueError):shops.build(feed({**ROW,**change}),'smartphonehoesjes')
 def test_invalid_prices_hidden(self):
  for price in ['NaN','Infinity','-1','0','']:
   with self.subTest(price=price):self.assertIsNone(rows(shops.build(feed({**ROW,'search_price':price}),'smartphonehoesjes'))[0][5])
 def test_source_url_scoped_to_official_feed(self):
  base='https://productdata.awin.com/datafeed/download/apikey/example/fid/96636/columns/product_name/format/csv/compression/gzip/'
  self.assertIn('/fid/20671/',shops.feed_url(base,'smartphonehoesjes'));self.assertIn('/fid/96636/',shops.feed_url(base,'coolblue'))
  for bad in ['https://evil.example/a','http://productdata.awin.com/a','https://productdata.awin.com@evil.example/a']:
   with self.assertRaises(ValueError):shops.feed_url(bad,'coolblue')
if __name__=='__main__':unittest.main()
