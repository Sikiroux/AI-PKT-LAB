import copy,tempfile,unittest
from pathlib import Path
from tickets_app import Tickets
from test_inventory import Network
from test_service_desk import Jobs
from service_desk import ServiceDesk,site_choices
class Arrivals(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.e=Network();self.path=Path(self.tmp.name)/'state.json';self.t=Tickets(self.e,self.path);self.t.register()
  free=copy.deepcopy(self.e.s['devices'][1]['ports'][0]);free.update(name='FastEthernet0/3',linked=False,up=False,protocol_up=False);self.e.s['devices'][1]['ports'].append(free)
  self.g=Jobs();self.d=ServiceDesk(self.t,self.g);self.t.desk=self.d;self.d.configure(dict(source='site',trace_mode='technician',ticket_minutes=20))
 def tearDown(self):self.tmp.cleanup()
 def test_request_uses_site_without_generating_file(self):
  self.d.create('pc');ticket=self.t.state['tickets'][0]
  self.assertEqual(ticket['kind'],'pc');self.assertEqual(ticket['arrival']['source'],'site');self.assertEqual(ticket['timer']['limit'],1200)
  self.assertFalse(self.g.items)
 def test_scheduler_creates_site_request(self):
  self.d.settings.update(active=True,next_at=100);self.d.tick(100)
  self.assertEqual(len(self.t.state['tickets']),1);self.assertGreater(self.d.settings['next_at'],100)
  self.assertEqual(self.t.state['tickets'][0]['arrival']['source'],'site')
 def test_no_incident_during_unfinished_site_request(self):
  self.d.create('pc');calls=len(self.e.calls)
  with self.assertRaises(ValueError):self.d.create('incident')
  self.assertEqual(len(self.e.calls),calls)
 def test_no_free_port_no_pc_request(self):
  self.e.s['devices'][1]['ports'][-1]['linked']=True
  with self.assertRaises(ValueError):self.d.create('pc')
  self.assertFalse(self.t.state['tickets'])
 def test_wrong_site_defers_without_injection(self):
  self.e.s['devices'][0]['serial']='wrong';self.d.settings.update(active=True,next_at=100);self.d.tick(100)
  self.assertFalse(self.t.state['tickets']);self.assertFalse(self.e.calls);self.assertEqual(self.d.settings['next_at'],115)
 def test_site_incident_records_target_and_timer(self):
  self.d.create('incident');t=self.t.state['tickets'][0]
  self.assertEqual(t['name'],'PC-ADMIN');self.assertEqual(t['injection']['state'],'applied');self.assertEqual(t['timer']['limit'],1200)
 def test_trace_setting_and_source_survive_restart(self):
  other=Tickets(self.e,self.path);desk=ServiceDesk(other,self.g)
  self.assertEqual(desk.settings['source'],'site');self.assertEqual(desk.settings['trace_mode'],'technician')
 def test_start_requires_registered_site_and_invalid_config_atomic(self):
  before=copy.deepcopy(self.d.settings)
  with self.assertRaises(ValueError):self.d.configure(dict(source='unknown'))
  self.assertEqual(before,self.d.settings)
  self.t.state['site']=None
  with self.assertRaises(ValueError):self.d.control(True)
  self.assertFalse(self.d.settings['active'])
