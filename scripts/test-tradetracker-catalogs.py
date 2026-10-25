import copy,gzip,importlib.util,json,unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location('tt',Path(__file__).with_name('update-tradetracker-catalogs.py'));tt=importlib.util.module_from_spec(spec);spec.loader.exec_module(tt)
def feed(shop):
 campaign,fid,host,path=tt.SHOPS[shop]
 return {'products':[{'ID':str(i),'campaignID':int(campaign),'name':'Test '+str(i),'price':{'currency':'EUR','amount':99.5},'URL':'https://'+host+path+'?tt='+campaign+'_'+fid+'_518245_&r=https%3A%2F%2F'+host+'%2Fproduct%2F'+str(i),'images':['https://'+host+'/photo.jpg'],'properties':{'brand':['Test'],'stock':['ja'],'deliveryCosts':['0'],'categoryPath':['Computers > Laptops']}} for i in range(100)]}
class FeedTests(unittest.TestCase):
 def test_tracking_prices_images_and_safe_stable_ids(self):
  ids=set()
  for shop in tt.SHOPS:
   data=feed(shop);out=tt.build(data,shop,'2026-10-25T17:00:00Z');rows=json.loads(gzip.decompress(out['catalog-00.json.gz']));manifest=json.loads(out['manifest.json'])
   self.assertEqual(manifest['publisherId'],'518245');self.assertEqual(manifest['count'],100);self.assertEqual(rows[0][5:8],[99.5,0,True]);self.assertEqual(rows[0][2],'Laptops')
   self.assertTrue(all(int(r[4])<2**53 for r in rows));self.assertTrue(ids.isdisjoint(r[4] for r in rows));ids.update(r[4] for r in rows)
   self.assertEqual(out,tt.build(copy.deepcopy(data),shop,'2026-10-25T17:00:00Z'))
 def test_wrong_tracking_or_merchant_rejected(self):
  for shop in tt.SHOPS:
   for field,value in [('campaignID',1),('URL','https://evil.example/'),('URL',feed(shop)['products'][0]['URL'].replace('518245','1')),('URL',feed(shop)['products'][0]['URL'].replace('r=https%3A','r=http%3A'))]:
    data=feed(shop);data['products'][0][field]=value
    with self.subTest(shop=shop,field=field),self.assertRaises(ValueError):tt.build(data,shop)
 def test_unknown_stock_prices_and_untrusted_images(self):
  data=feed('hobo');p=data['products'][0];p['price']['amount']='NaN';p['images']=['https://www.hobo.nl.evil.example/photo.jpg'];p['properties']['stock']=['unknown'];p['properties']['deliveryCosts']=['unknown']
  rows=json.loads(gzip.decompress(tt.build(data,'hobo')['catalog-00.json.gz']));self.assertEqual(rows[0][3],'');self.assertEqual(rows[0][5:8],[None,None,False])
 def test_incomplete_and_duplicate_feeds_rejected(self):
  with self.assertRaises(ValueError):tt.build({'products':[]},'hobo')
  data=feed('hobo');data['products'][1]['ID']=data['products'][0]['ID']
  with self.assertRaises(ValueError):tt.build(data,'hobo')
if __name__=='__main__':unittest.main()
