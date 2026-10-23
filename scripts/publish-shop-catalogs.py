"""Publish validated catalog files in one Git tree/commit, without overwriting concurrent edits."""
import base64,json,os,subprocess,sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.error import HTTPError
ROOT=Path(__file__).resolve().parents[1]
def main():
 repo=os.environ['GITHUB_REPOSITORY'];token=os.environ['GH_TOKEN'];api='https://api.github.com/repos/'+repo
 def call(path,payload=None,method=None):
  req=Request(api+path,data=json.dumps(payload).encode() if payload is not None else None,method=method or ('POST' if payload is not None else 'GET'),headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28','Content-Type':'application/json'})
  with urlopen(req,timeout=60) as r:return json.load(r)
 files=[ROOT/'coolblue-prices.json',ROOT/'data/product-matches.json']+sorted((ROOT/'data/smartphonehoesjes').glob('*'))+sorted((ROOT/'data/coolblue').glob('*'))+sorted((ROOT/'data/acer').glob('*'))
 if subprocess.run(['git','diff','--quiet','--','coolblue-prices.json','data'],cwd=ROOT).returncode==0 and not subprocess.check_output(['git','ls-files','--others','--exclude-standard','data'],cwd=ROOT).strip():print('Catalog data unchanged');return
 def blob(p):return {'path':str(p.relative_to(ROOT)),'mode':'100644','type':'blob','sha':call('/git/blobs',{'content':base64.b64encode(p.read_bytes()).decode(),'encoding':'base64'})['sha']}
 with ThreadPoolExecutor(max_workers=4) as pool:entries=list(pool.map(blob,files))
 for attempt in range(3):
  head=call('/git/ref/heads/main')['object']['sha'];base=call('/git/commits/'+head)['tree']['sha'];tree=call('/git/trees',{'base_tree':base,'tree':entries})['sha'];commit=call('/git/commits',{'message':'Refresh Coolblue, Smartphonehoesjes and Acer catalogs, prices and photos','tree':tree,'parents':[head]})['sha']
  try:call('/git/refs/heads/main',{'sha':commit,'force':False},method='PATCH');break
  except HTTPError as e:
   if e.code!=422 or attempt==2:raise
 call('/pages/builds',{},method='POST');print('Published all three shop catalogs and requested website build')
if __name__=='__main__':
 try:main()
 except Exception as e:print('Publishing failed: '+type(e).__name__+'. Credentials and response bodies are not logged.',file=sys.stderr);raise SystemExit(1)


