import copy,json,re,tempfile,unittest
from pathlib import Path
from test_tickets import Fake
from tickets_app import Tickets
import live_faults
class Static(Fake):
 def __init__(self):
  super().__init__();self.s['devices'][3]['ports'][0].update(dhcp_client=False,ip_editable=True)
 def ping(self,name,target):
  p=next(d for d in self.s['devices'] if d['name']==name)['ports'][0]
  valid=self.ok and p['ip']=='192.168.50.20' and p['mask']=='255.255.255.0'
  return dict(label='Ping depuis le poste',status='valide' if valid else 'non satisfait',detail='')
 def call(self,js,*args):
  if 'setIpSubnetMask' in js:
   self.calls.append(js);v=json.loads(re.search(r'var v=(\{.*?\}),d=',js).group(1))
   d=next(d for d in self.s['devices'] if d['name']==v['device'])
   self.assert_identity=d['serial']==v['serial']
   if not self.assert_identity:return json.dumps({'error':'identity'})
   d['ports'][0].update(ip=v['ip'],mask=v['mask']);return 'ok'
  return super().call(js,*args)
class LiveFaults(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.e=Static();self.t=Tickets(self.e,Path(self.tmp.name)/'state.json');self.t.register()
 def tearDown(self):self.tmp.cleanup()
 def test_static_variants_complete_cycle_without_ios_commands(self):
  for kind in ('ip_wrong','mask_wrong'):
   self.t.new('incident','hidden','PC-ADMIN',kind);t=self.t.state['tickets'][-1]
   self.assertEqual(t['injection']['kind'],kind);self.assertEqual(t['injection']['state'],'applied')
   self.assertFalse(self.t.verify(t)['tickets'][-1]['complete'])
   self.t.action(t['id'],'restore',{});self.t.action(t['id'],'close',{})
   self.assertEqual(self.e.s['devices'][3]['ports'][0]['ip'],'192.168.50.20')
   self.assertEqual(self.e.s['devices'][3]['ports'][0]['mask'],'255.255.255.0')
  self.assertFalse(any('configureIosDevice' in s for s in self.e.calls))
 def test_dhcp_or_missing_capabilities_refuse_before_mutation(self):
  for value in (True,None):
   self.e.s['devices'][3]['ports'][0]['dhcp_client']=value
   with self.assertRaises(ValueError):self.t.new('incident','hidden','PC-ADMIN','ip_wrong')
   self.assertFalse(self.t.state['tickets']);self.assertFalse(any('setIpSubnetMask' in c or 'configureIosDevice' in c for c in self.e.calls))
 def test_random_covers_only_compatible_variants(self):
  d=self.e.s['devices'][3]
  self.assertEqual({live_faults.plan(d,'random',self.e.s,i)['kind'] for i in range(50)},set(live_faults.KINDS))
  d['ports'][0].pop('ip_editable');self.assertEqual(live_faults.choices(d),['port_down'])
 def test_unconfirmed_symptom_rolls_back(self):
  self.e.ping=lambda *args:dict(label='Ping',status='valide',detail='')
  with self.assertRaises(RuntimeError):self.t.new('incident','hidden','PC-ADMIN','ip_wrong')
  t=self.t.state['tickets'][0];self.assertEqual(t['injection']['state'],'restored')
  self.assertEqual(self.e.s['devices'][3]['ports'][0]['ip'],'192.168.50.20')
 def test_repair_requires_original_address_and_mask(self):
  self.t.new('incident','hidden','PC-ADMIN','mask_wrong');t=self.t.state['tickets'][0]
  self.e.ping=lambda *args:dict(label='Ping',status='valide',detail='')
  with self.assertRaises(ValueError):self.t.action(t['id'],'close',{})
