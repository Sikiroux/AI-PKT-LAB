import json,threading,unittest,urllib.request
from diagnostic import Engine,checks
from vendor.live_bridge import PTCommandBridge
class Test(unittest.TestCase):
 def test_added_device_and_wifi_unknown(self):
  d={'name':'NEW','serial':'2','ports':[{'name':'Wireless0','wireless':True,'up':True,'ip':'192.168.50.51','linked':False}]}
  c=checks({'devices':[d]}, {'devices':[{'serial':'1'}]},'NEW','wifi','192.168.50.0/24')
  self.assertEqual(c[1]['status'],'valide');self.assertEqual(c[-2]['status'],'inconnu');self.assertFalse(all(x['status']=='valide' for x in c))
  d['ports'].append({'name':'FastEthernet0','wireless':False,'up':True,'ip':'192.168.50.51','linked':True})
  c=checks({'devices':[d]}, {'devices':[{'serial':'1'}]},'NEW','wifi','192.168.50.0/24')
  self.assertEqual(c[4]['status'],'non satisfait')
 def test_rename_is_not_addition(self):
  c=checks({'devices':[{'name':'NEW','serial':'1','ports':[]}]},{'devices':[{'serial':'1'}]},'NEW','wired','192.168.50.0/24')
  self.assertEqual(c[1]['status'],'non satisfait')
 def test_bridge_exchange_and_auth(self):
  b=PTCommandBridge(port=0,token='a'*48);b.start();port=b._server.server_address[1];b.port=port
  def request(path,body=None,token='a'*48):
   req=urllib.request.Request('http://127.0.0.1:'+str(port)+path,data=body,headers={'X-PT-Token':token});return urllib.request.urlopen(req,timeout=5).read()
  try:
   from urllib.error import HTTPError
   with self.assertRaises(HTTPError):request('/next',token='wrong')
   request('/next');engine=Engine(b)
   def fake_pt():
    code=request('/next').decode()
    import re
    rid=re.search(r'rid=([0-9-]+)',code).group(1)
    request('/result?rid='+rid,b'{"devices":[],"link_count":0}')
   t=threading.Thread(target=fake_pt);t.start();self.assertEqual(engine.snapshot()['devices'],[]);t.join()
  finally:b.stop()
if __name__=='__main__':unittest.main()
