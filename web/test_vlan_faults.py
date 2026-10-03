import json,re,tempfile,unittest
from pathlib import Path
from tickets_app import Tickets
from test_tickets import Fake
import vlan_faults

def output(port,vlan=1,admin='dynamic auto',operational='static access'):
 return f'Name: {port}\nSwitchport: Enabled\nAdministrative Mode: {admin}\nOperational Mode: {operational}\nAccess Mode VLAN: {vlan} (default)\n'
class VlanEngine(Fake):
 def __init__(self):super().__init__();self.vlan=1;self.vlans={1,1002,1003,1004,1005};self.output='SW1#';self.admin='dynamic auto'
 def call(self,js,*args):
  if 'VlanManager' in js:self.calls.append(js);return json.dumps(sorted(self.vlans))
  if 'var c=ipc.network()' in js and 'show vlan brief' in js:
   self.calls.append(js);old=self.output;rows='\n'.join(str(n)+' '+('NETOPS_ISO_'+str(n) if n>=900 else 'default')+' active' for n in sorted(self.vlans));self.output+='\nshow vlan brief\nVLAN Name Status Ports\n'+rows+'\nSW1#';return old
  if 'no vlan ' in js:
   self.calls.append(js);self.vlans.discard(int(re.search(r'no vlan (\d+)',js).group(1)));return 'ok'
  if 'var c=ipc.network()' in js and 'show interfaces' in js:
   self.calls.append(js);old=self.output;self.output+='\nshow interfaces FastEthernet0/1 switchport\n'+output('Fa0/1',self.vlan,self.admin)+'SW1#';return old
  if js.startswith('reportResult(String('):return self.output
  if 'configureIosDevice' in js and 'switchport access vlan' in js:
   self.calls.append(js);self.vlan=int(re.search(r'switchport access vlan (\d+)',js).group(1));self.vlans.add(self.vlan);self.ok=self.vlan==1;return 'ok'
  return super().call(js,*args)
class VLAN(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.e=VlanEngine();self.t=Tickets(self.e,Path(self.tmp.name)/'state.json');self.t.register()
 def tearDown(self):self.tmp.cleanup()
 def test_wrong_vlan_full_cycle(self):
  self.t.new('incident','technician','PC-ADMIN','vlan_wrong');t=self.t.state['tickets'][0]
  self.assertEqual(t['injection']['before_vlan'],1);self.assertEqual(self.e.vlan,999)
  self.assertFalse(self.t.verify(t)['tickets'][0]['complete'])
  self.t.action(t['id'],'restore',{});self.assertEqual(self.e.vlan,1)
  self.t.action(t['id'],'close',{});self.assertEqual(t['status'],'clos');self.assertNotIn(999,self.e.vlans);self.assertTrue(t['vlan_cleanup']['removed'])
 def test_hidden_refused_before_cli(self):
  with self.assertRaises(ValueError):self.t.new('incident','hidden','PC-ADMIN','vlan_wrong')
  self.assertFalse(self.e.calls);self.assertFalse(self.t.state['tickets'])
 def test_occupied_isolation_vlan_not_reused(self):
  self.e.vlans.add(999);plan=vlan_faults.plan(self.e,'FastEthernet0/1');self.assertEqual(plan['after_vlan'],998)
 def test_changed_admin_blocks_restore(self):
  self.t.new('incident','technician','PC-ADMIN','vlan_wrong');t=self.t.state['tickets'][0];self.e.admin='static access'
  with self.assertRaises(ValueError):self.t.action(t['id'],'restore',{})
  self.assertEqual(self.e.vlan,999)
 def test_ping_alone_does_not_validate_vlan(self):
  self.t.new('incident','technician','PC-ADMIN','vlan_wrong');t=self.t.state['tickets'][0];self.e.ok=True
  with self.assertRaises(ValueError):self.t.action(t['id'],'close',{})
 def test_parser_rejects_trunk_wrong_port_and_missing_data(self):
  for text in (output('Fa0/2'),output('Fa0/1',operational='trunk'),'Access Mode VLAN: 1'):
   with self.assertRaises(ValueError):vlan_faults.parse_switchport(text,'FastEthernet0/1')
 def test_read_does_not_accept_old_output(self):
  class Stale:
   def call(self,js):return output('Fa0/1')+'SW1#'
  # A reset/shortened output must fail immediately, not use the old VLAN.
  class Reset:
   def call(self,js):return 'old output' if 'var c=' in js else output('Fa0/1')+'SW1#'
  with self.assertRaises(ValueError):vlan_faults.read(Reset(),'FastEthernet0/1')

class Cleanup(unittest.TestCase):
 def test_used_or_renamed_vlan_is_preserved(self):
  class Engine:
   def __init__(self,row):self.row=row;self.output='SW1#';self.mutated=False
   def call(self,js):
    if 'VlanManager' in js:return '[1,999]'
    if 'var c=' in js:
     before=self.output;self.output+='\nshow vlan brief\n'+self.row+'\nSW1#';return before
    if 'configureIosDevice' in js:self.mutated=True;return 'ok'
    return self.output
  for row in ('999 NETOPS_ISO_999 active Fa0/2','999 VLAN-PRODUCTION active'):
   engine=Engine(row);result=vlan_faults.remove_unused(engine,{'after_vlan':999})
   self.assertFalse(result['removed']);self.assertFalse(engine.mutated)
