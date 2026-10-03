import tempfile,unittest,time
from pathlib import Path
from tickets_app import Tickets
from test_tickets import Fake
from service_desk import ServiceDesk,CATALOGUE
class Jobs:
 def __init__(self):self.items=[]
 def start(self,data):
  j=dict(id=str(len(self.items)),status='done',files=['lab.pka'],created='today');self.items.append(j);return j
 def jobs(self):return self.items
class TestServiceDesk(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.path=Path(self.tmp.name)/'state.json';self.t=Tickets(Fake(),self.path);self.g=Jobs();self.d=ServiceDesk(self.t,self.g);self.t.desk=self.d
 def tearDown(self):self.tmp.cleanup()
 def test_create_without_bridge_or_registered_site(self):
  self.d.create(CATALOGUE[0][0]);self.assertEqual(self.t.state['tickets'][0]['kind'],'service');self.assertFalse(self.t.engine.calls)
 def test_duplicate_and_cap(self):
  self.d.settings['max_open']=1;self.d.create(CATALOGUE[0][0])
  with self.assertRaises(ValueError):self.d.create(CATALOGUE[1][0])
  self.d.settings['max_open']=3
  with self.assertRaises(ValueError):self.d.create(CATALOGUE[0][0])
 def test_arrival_waits_and_defers_at_cap(self):
  self.d.settings.update(active=True,next_at=100,max_open=1)
  self.d.tick(99);self.assertFalse(self.t.state['tickets'])
  self.d.tick(100);self.assertEqual(len(self.t.state['tickets']),1)
  self.d.tick(self.d.settings['next_at']);self.assertEqual(len(self.t.state['tickets']),1);self.assertIn('différée',self.d.settings['message'])
 def test_restart_pauses_arrivals(self):
  self.d.control(True);other=Tickets(Fake(),self.path);d=ServiceDesk(other,self.g);self.assertFalse(d.settings['active'])
 def test_manual_closure_requires_evidence(self):
  self.d.create(CATALOGUE[0][0]);t=self.t.state['tickets'][0]
  with self.assertRaises(ValueError):self.t.action(t['id'],'close',dict(manual_tests=True))
  self.t.action(t['id'],'notes',dict(notes='Résolution DNS restaurée et tests des noms et HTTP réussis.'))
  with self.assertRaises(ValueError):self.t.action(t['id'],'close',{})
  self.t.action(t['id'],'close',dict(manual_tests=True));self.assertEqual(t['status'],'clos');self.assertFalse(t['complete']);self.assertTrue(t['manual_tests'])
 def test_settings_validation(self):
  with self.assertRaises(ValueError):self.d.configure(dict(minimum=0))
  self.d.configure(dict(interval='random',minimum=2,maximum=3,max_open=4,ticket_minutes=15));self.d.control(True)
  remaining=self.d.settings['next_at']-time.time();self.assertTrue(119<=remaining<=180)
if __name__=='__main__':unittest.main()
