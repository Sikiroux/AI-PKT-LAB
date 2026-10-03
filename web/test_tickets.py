import copy,json,tempfile,unittest
from pathlib import Path
from tickets_app import Tickets,LINK_JS
from console_tools import CLEAN_JS

def snapshot():
 def dev(name,model,serial,port='FastEthernet0'):
  return {'name':name,'model':model,'serial':serial,'ports':[{'name':port,'up':True,'protocol_up':True,'ip':'192.168.50.20','mask':'255.255.255.0','linked':True,'wireless':False}]}
 return {'devices':[dev('R1','2911','r'),dev('SW1','2960-24TT','s','FastEthernet0/1'),dev('AP1','AccessPoint-PT','a'),dev('PC-ADMIN','PC-PT','p'),dev('SRV-WEB','Server-PT','v')],'link_count':5}
class Fake:
 def __init__(self):self.s=snapshot();self.ok=True;self.inject_fail=False;self.calls=[];self.clean_ok=True;self.clean_calls=0;self.fail_after_injection=False
 def snapshot(self):return copy.deepcopy(self.s)
 def ping(self,*args):return {'label':'Ping depuis le poste','status':'valide' if self.ok else 'non satisfait','detail':''}
 def call(self,js,*args):
  self.calls.append(js)
  if js==LINK_JS:return json.dumps({'ends':[{'device':'SW1','port':'FastEthernet0/1'},{'device':'PC-ADMIN','port':'FastEthernet0'}]})
  if js==CLEAN_JS:
   self.clean_calls+=1;ok=self.clean_ok and not(self.fail_after_injection and self.clean_calls>1)
   return json.dumps({'display':ok,'history':ok})
  if self.inject_fail:raise RuntimeError('timeout')
  if 'configureIosDevice' in js:
   up='no shutdown' in js;self.s['devices'][1]['ports'][0]['up']=up;self.ok=up
  return 'ok'
class TestTickets(unittest.TestCase):
 def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.path=Path(self.tmp.name)/'state.json';self.e=Fake();self.t=Tickets(self.e,self.path);self.t.register()
 def tearDown(self):self.tmp.cleanup()
 def added(self,kind):
  d=copy.deepcopy(self.e.s['devices'][3]);d.update(name='PC-NOUVEAU' if kind=='pc' else 'LAPTOP-WIFI',serial='new')
  if kind=='wifi':d['ports'][0].update(name='Wireless0',wireless=True,linked=False)
  self.e.s['devices'].append(d)
 def test_hidden_cleanup_failure_blocks_mutation(self):
  self.e.clean_ok=False
  with self.assertRaises(ValueError):self.t.new('incident')
  self.assertFalse(any('configureIosDevice' in c for c in self.e.calls));self.assertFalse(self.t.state['tickets'])
 def test_technician_trace_mode_does_not_clean(self):
  self.e.clean_ok=False;self.t.new('incident','technician')
  self.assertTrue(self.t.state['tickets'][0]['cleanup']['intentional']);self.assertNotIn(CLEAN_JS,self.e.calls)
 def test_wait_and_severity_persist(self):
  self.t.new('pc');t=self.t.state['tickets'][0]
  self.t.action(t['id'],'wait',{});self.t.action(t['id'],'severity',{'severity':'elevee'})
  other=Tickets(self.e,self.path).state['tickets'][0];self.assertEqual(other['status'],'en_attente');self.assertEqual(other['severity'],'elevee')
 def test_saved_path_is_validated(self):
  with self.assertRaises(ValueError):self.t.attach('not-a-pkt.exe')
  p=Path(self.tmp.name)/'work.pkt';p.write_bytes(b'example');self.e.s['saved_filename']=str(p);self.t.attach(str(p));self.assertEqual(self.t.state['site']['file'],str(p))
 def test_ip_is_not_failed_only_because_link_down(self):
  from diagnostic import checks
  s=self.e.snapshot();s['devices'][3]['ports'][0]['up']=False
  c=checks(s,s,'PC-ADMIN','wired','192.168.50.0/24')
  self.assertEqual(next(x['status'] for x in c if x['label']=='Adresse dans le reseau attendu'),'valide')
 def test_wrong_opened_filename_is_rejected(self):
  self.t.open_target='C:/work/site.pkt';self.e.s['saved_filename']='C:/work/other.pkt'
  with self.assertRaises(ValueError):self.t.new('pc')
 def test_failed_cleanup_after_injection_restores_port(self):
  self.e.fail_after_injection=True
  with self.assertRaises(RuntimeError):self.t.new('incident')
  t=self.t.state['tickets'][0];self.assertEqual(t['injection']['state'],'restored');self.assertTrue(self.e.ok);self.assertEqual(t['status'],'a_controler')
 def test_open_wait_does_not_accept_missing_filename(self):
  self.t.open_target='C:/work/site.pkt'
  with self.assertRaises(ValueError):self.t.guard(self.e.snapshot())
 def test_persistence(self):
  self.t.new('pc');other=Tickets(self.e,self.path);self.assertEqual(other.public()['tickets'][0]['kind'],'pc');self.assertTrue(other.state['site'])
 def test_wrong_network_refuses_injection(self):
  self.e.s['devices'][0]['serial']='different'
  with self.assertRaises(ValueError):self.t.new('incident')
  self.assertFalse(self.e.calls)
 def test_incident_full_cycle(self):
  self.t.new('incident');t=self.t.state['tickets'][0];self.assertEqual(t['injection']['state'],'applied');self.t.verify(t);self.assertFalse(t['complete'])
  self.t.action(t['id'],'restore',{});self.assertTrue(t['complete']);self.t.action(t['id'],'close',{});self.assertEqual(t['status'],'clos')
 def test_duplicate_blocked(self):
  self.t.new('pc')
  with self.assertRaises(ValueError):self.t.new('pc')
 def test_stale_pass_does_not_close(self):
  self.t.new('pc');self.added('pc');t=self.t.state['tickets'][0];self.t.verify(t);self.assertTrue(t['complete']);self.e.ok=False
  with self.assertRaises(ValueError):self.t.action(t['id'],'close',{})
  self.assertNotEqual(t['status'],'clos')
 def test_wifi_needs_manual_confirmation(self):
  self.t.new('wifi');self.added('wifi');t=self.t.state['tickets'][0]
  with self.assertRaises(ValueError):self.t.action(t['id'],'close',{})
  self.t.action(t['id'],'close',{'manual_ssid':True});self.assertTrue(t['manual_ssid'])
 def test_wifi_manual_cannot_bypass_ping_failure(self):
  self.t.new('wifi');self.added('wifi');self.e.ok=False
  with self.assertRaises(ValueError):self.t.action(self.t.state['tickets'][0]['id'],'close',{'manual_ssid':True})
 def test_timeout_keeps_recoverable_ticket(self):
  self.e.inject_fail=True
  with self.assertRaises(RuntimeError):self.t.new('incident')
  t=Tickets(self.e,self.path).state['tickets'][0];self.assertEqual(t['status'],'a_controler');self.assertEqual(t['injection']['state'],'uncertain')
if __name__=='__main__':unittest.main()
