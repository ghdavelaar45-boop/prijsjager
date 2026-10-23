import importlib.util,unittest
from pathlib import Path
p=Path(__file__).with_name('match-shop-products.py');s=importlib.util.spec_from_file_location('matches',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
CFG={'coolblue':{'mid':'85161'},'acer':{'mid':'17133'},'smartphonehoesjes':{'mid':'8261'}}
def row(shop,pid,**values):
 return {'condition':'new','product_name':'Acer Laptop 16 GB','brand_name':'Acer','ean':'4006381333931','aw_deep_link':f'https://www.awin1.com/pclick.php?p={pid}&a=3124230&m={CFG[shop]["mid"]}',**values}
def match(a=None,b=None):
 return m.build({'coolblue':[row('coolblue','1',**(a or {}))],'acer':[row('acer','2',**(b or {}))]},CFG,'2026-10-24T00:00:00+00:00')['groups']
class Matches(unittest.TestCase):
 def test_same_gtin_new_product_across_shops(self):self.assertEqual(match()[0]['members'],[['acer','2'],['coolblue','1']])
 def test_leading_zero_gtin_formats(self):self.assertEqual(m.gtin('4006381333931'),m.gtin('04006381333931'))
 def test_invalid_checksums_and_placeholders(self):
  for code in ['4006381333932','0000000000000','123','4e12','4006381333931,123']:
   self.assertIsNone(m.gtin(code))
 def test_different_gtin_brand_condition_and_bundle_not_merged(self):
  for change in [{'ean':'5901234123457'},{'brand_name':'HP'},{'condition':'used'},{'condition':''},{'product_name':'Acer Laptop + muis'},{'product_name':'Acer Laptop Bundle'}]:
   self.assertEqual(match(b=change),[])
 def test_conflicting_mpn_and_gtin_fields(self):
  self.assertEqual(match(a={'mpn':'NX.ABC.001'},b={'mpn':'NX.ABC.002'}),[])
  self.assertEqual(match(b={'product_GTIN':'5901234123457'}),[])
 def test_ambiguous_same_shop_and_wrong_affiliate_identity(self):
  feeds={'coolblue':[row('coolblue','1'),row('coolblue','3')],'acer':[row('acer','2')]}
  self.assertEqual(m.build(feeds,CFG,'now')['groups'],[])
  self.assertEqual(match(b={'aw_deep_link':'https://www.awin1.com/pclick.php?p=2&a=999&m=17133'}),[])
 def test_three_shops_when_exact_item_exists(self):
  feeds={shop:[row(shop,str(i))] for i,shop in enumerate(CFG,1)}
  self.assertEqual(len(m.build(feeds,CFG,'now')['groups'][0]['members']),3)
if __name__=='__main__':unittest.main()
