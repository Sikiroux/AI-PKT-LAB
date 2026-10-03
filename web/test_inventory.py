import copy,json,re,tempfile,unittest
from pathlib import Path
from tickets_app import Tickets,LINK_JS
from test_tickets import Fake
class Network(Fake):
 def call(self,js,*args):
  if 'getDevice("PC-NOUVEAU")' in js and 'getLink' in js:
   self.calls.append(js);return json.dumps({'ends':[{'device':'SW1','port':'FastEthernet0/2'},{'device':'PC-NOUVEAU','port':'FastEthernet0'}]})
  if 'configureIosDevice' in js and 'FastEthernet0/2' in js:
   self.calls.append(js);up='no shutdown' in js;self.s['devices'][1]['ports'][1]['up']=up;self.ok=up;return 'ok'
  return super().call(js,*args)
class Inventory(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.path=Path(self.tmp.name)/'state.json';self.e=Network();self.t=Tickets(self.e,self.path);self.t.register()
 def tearDown(self):self.tmp.cleanup()
 def add_pc(self):
  d=copy.deepcopy(self.e.s['devices'][3]);d.update(name='PC-NOUVEAU',serial='added');self.e.s['devices'].append(d)
  p=copy.deepcopy(self.e.s['devices'][1]['ports'][0]);p['name']='FastEthernet0/2';self.e.s['devices'][1]['ports'].append(p)
 def test_add_close_then_incident_on_same_pc(self):
  self.t.new('pc');self.add_pc();t=self.t.state['tickets'][0];self.t.action(t['id'],'close',{})
  inv=self.t.public()['site']['inventory'];self.assertTrue(any(d['serial']=='added' for d in inv))
  self.t.new('incident','technician','PC-NOUVEAU');incident=self.t.state['tickets'][-1]
  self.assertEqual(incident['injection']['port'],'FastEthernet0/2')
  self.assertTrue(self.e.s['devices'][1]['ports'][0]['up']);self.assertFalse(self.e.s['devices'][1]['ports'][1]['up'])
  self.t.action(incident['id'],'restore',{});self.t.action(incident['id'],'close',{})
  self.t.new('pc');self.assertEqual(self.t.state['tickets'][-1]['name'],'PC-NOUVEAU-02')
 def test_absence_and_rename_preserve_serial_history(self):
  self.add_pc();self.t.sync_inventory();self.e.s['devices'][-1]['name']='PC-COMPTA';self.t.sync_inventory()
  self.assertEqual(next(d for d in self.t.state['site']['inventory'] if d['serial']=='added')['name'],'PC-COMPTA')
  self.e.s['devices'].pop();self.t.sync_inventory()
  item=next(d for d in self.t.state['site']['inventory'] if d['serial']=='added');self.assertFalse(item['present'])
  self.assertEqual(Tickets(self.e,self.path).state['site']['inventory'],self.t.state['site']['inventory'])
 def test_wrong_network_cannot_refresh_inventory(self):
  before=copy.deepcopy(self.t.state['site']['inventory']);self.e.s['devices'][0]['serial']='wrong'
  with self.assertRaises(ValueError):self.t.sync_inventory()
  self.assertEqual(before,self.t.state['site']['inventory'])
 def test_missing_saved_filename_is_rejected(self):
  self.t.state['site']['file']='C:/site.pkt'
  with self.assertRaises(ValueError):self.t.sync_inventory()
 def test_replacement_and_collateral_damage_refuse_closure(self):
  self.add_pc();self.t.new('incident','technician','PC-NOUVEAU');incident=self.t.state['tickets'][-1]
  self.t.action(incident['id'],'restore',{});self.e.s['devices'][-1]['serial']='replacement'
  with self.assertRaises(ValueError):self.t.action(incident['id'],'close',{})
  self.e.s['devices'][-1]['serial']='added';self.e.s['devices'][1]['ports'][0]['up']=False
  with self.assertRaises(ValueError):self.t.action(incident['id'],'close',{})
 def test_legacy_state_gains_inventory_without_reset(self):
  self.t.state['site'].pop('inventory');self.t.state['site'].pop('inventory_at');self.t.save()
  other=Tickets(self.e,self.path);other.sync_inventory();self.assertEqual(len(other.state['site']['inventory']),5)
