"""Réception sans mutation, seed, cadence et activation exclusive."""
import copy
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock
from tickets_app import Tickets
from test_tickets import Fake
from service_desk import ServiceDesk
from workspace_model import generate
import ticket_arrivals as arrivals

class ArrivalTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
  self.t=Tickets(Fake(),Path(self.tmp.name)/'tickets.json')
  self.s=generate('queue-test');self.s['environment_id']='env'
  self.s['devices']={k:dict(name=k,serial=k,ip=ip) for k,ip in [('client','192.168.1.2'),('server','192.168.1.10'),('technician','192.168.1.20')]}
  import company_registry
  company_registry.ensure(self.s)
  self.c=Mock();self.c.workspace.state=self.s;self.c.on_change=None
  self.c.workspace.path=Path(self.tmp.name)/'session.json';self.t.controller=self.c
  self.t.state['site']={'environment_id':'env','devices':[]};self.t.state['seed']='queue-test'
  self.d=ServiceDesk(self.t,Mock());self.t.desk=self.d;self.d.settings.update(source='site',arrival_engine='varied')
 def test_receipts_do_not_prepare_or_mutate_services(self):
  before=copy.deepcopy(self.s)
  for _ in range(3):self.d.create()
  # Registry receives references; all operational state remains unchanged.
  for key in before:
   if key!='company_registry':self.assertEqual(before[key],self.s[key],key)
  self.c.observe.assert_not_called();self.c.next_desktop_incident.assert_not_called();self.c.next_mixed_incident.assert_not_called()
  self.assertEqual(len({t['id'] for t in self.t.state['tickets']}),3)
  self.assertTrue(all(t['stage']=='queued' for t in self.t.state['tickets']))
 def test_seed_replays_and_first_ticket_varies(self):
  first=[]
  for seed in range(60):
   self.s['seed']=str(seed);self.t.state['tickets']=[];self.t.state['arrival_count']=0
   arrivals.receive(self.t);p=copy.deepcopy(self.t.state['tickets'][0]['arrival_plan']);first.append(p['target'])
   self.t.state['tickets']=[];self.t.state['arrival_count']=0;arrivals.receive(self.t)
   self.assertEqual(p,self.t.state['tickets'][0]['arrival_plan'])
  self.assertEqual(set(first),{x[1] for x in arrivals.VARIED})
 def test_varied_arrivals_never_repeat_family_consecutively(self):
  for _ in range(30):arrivals.receive(self.t)
  plans=[t['arrival_plan'] for t in self.t.state['tickets']]
  self.assertTrue(all(a['target']!=b['target'] for a,b in zip(plans,plans[1:])))
 def test_application_arrivals_alternate_available_workstations(self):
  self.s['client_workspaces']={serial:dict(device=dict(name=serial),requester=serial) for serial in ('client','other')}
  for _ in range(12):arrivals.receive(self.t,'apps','printing')
  plans=[t['arrival_plan'] for t in self.t.state['tickets']]
  self.assertTrue(all(a['client_serial']!=b['client_serial'] for a,b in zip(plans,plans[1:])))
 def test_varied_arrivals_alternate_available_workstations(self):
  self.s['client_workspaces']={serial:dict(device=dict(name=serial),requester=serial) for serial in ('client','other')}
  for _ in range(30):arrivals.receive(self.t)
  plans=[t['arrival_plan'] for t in self.t.state['tickets']]
  self.assertTrue(all(a['client_serial']!=b['client_serial'] for a,b in zip(plans,plans[1:])))
  self.assertTrue(all(a['target']!=b['target'] for a,b in zip(plans,plans[1:])))
 def test_clock_cap_pause_and_no_catchup_burst(self):
  self.d.settings.update(active=True,next_at=100,minimum=1,maximum=1,max_open=2)
  self.d.tick(99);self.assertFalse(self.t.state['tickets'])
  self.d.tick(100);self.assertEqual(len(self.t.state['tickets']),1)
  self.d.tick(10000);self.assertEqual(len(self.t.state['tickets']),2)
  self.d.tick(20000);self.assertEqual(len(self.t.state['tickets']),2)
  self.t.state['tickets'][0]['status']='clos';self.d.tick(30000);self.assertEqual(len(self.t.state['tickets']),3)
  self.d.control(False);self.d.tick(40000);self.assertEqual(len(self.t.state['tickets']),3)
 def test_queued_cannot_be_verified_or_closed(self):
  self.d.create();t=self.t.state['tickets'][0]
  for action in ('verify','close'):
   with self.assertRaises(ValueError):self.t.workspace_action(t,action,{})
 def test_only_one_prepared_intervention(self):
  self.d.create();self.d.create();first,second=self.t.state['tickets'];first['stage']='prepared'
  with self.assertRaises(ValueError):arrivals.activate(self.t,second)
  self.c.observe.assert_not_called()
 def test_wrong_environment_and_network_request_rejected(self):
  with self.assertRaises(ValueError):arrivals.receive(self.t,'mixed','network')
  self.t.state['site']['environment_id']='other'
  with self.assertRaises(ValueError):arrivals.receive(self.t)
  self.assertFalse(self.t.state['tickets'])
 def test_peripheral_activation_keeps_id_without_probe(self):
  arrivals.receive(self.t,'apps','peripherals');t=self.t.state['tickets'][0]
  def prepare(*args,**kwargs):self.s['desktop_incident']={'id':'temporary','title':'Écran','description':'Diagnostic écran','goal':'peripherals'}
  self.c.next_desktop_incident.side_effect=prepare
  arrivals.activate(self.t,t)
  self.assertEqual(t['stage'],'prepared');self.assertEqual(self.s['desktop_incident']['id'],t['id'])
  self.c.observe.assert_not_called();self.c.workspace.save.assert_called_once()
 def test_failed_activation_restores_callback_and_pending(self):
  arrivals.receive(self.t,'apps','ftp');t=self.t.state['tickets'][0];callback=Mock();self.c.on_change=callback
  self.c.observe.side_effect=ValueError('Pont absent')
  with self.assertRaises(ValueError):arrivals.activate(self.t,t)
  self.assertIs(self.c.on_change,callback);self.assertEqual(t['stage'],'queued')
  self.c.next_desktop_incident.assert_not_called()
 def test_wording_is_replayed_without_changing_plan_or_company_identity(self):
  arrivals.receive(self.t);first=copy.deepcopy(self.t.state['tickets'][0])
  self.t.state['tickets']=[];self.t.state['arrival_count']=0;arrivals.receive(self.t);again=self.t.state['tickets'][0]
  for key in ('arrival_plan','request_context','title','description','severity'):self.assertEqual(first[key],again[key])
  self.assertEqual(first['request_context']['requester'],self.s['requester'])
  self.assertEqual(first['request_context']['serial'],'client')
  self.assertEqual(first['request_context']['company'],self.s['company'])
 def test_selected_timer_duration_used_on_activation(self):
  for duration in (15,0):
   with self.subTest(duration=duration):
    self.t.state['tickets']=[];self.s.pop('desktop_incident',None)
    arrivals.receive(self.t,'apps','peripherals',minutes=30);t=self.t.state['tickets'][0];old_plan=copy.deepcopy(t['arrival_plan'])
    self.t.action(t['id'],'timer',dict(timer_action='configure',minutes=duration,mode='challenge'))
    def prepare(*args,**kwargs):self.s['desktop_incident']={'id':'temporary','title':'Écran','description':'Diagnostic écran','goal':'peripherals'}
    self.c.next_desktop_incident.side_effect=prepare
    self.t.action(t['id'],'take',{})
    self.assertEqual(self.c.next_desktop_incident.call_args.args[1],duration)
    self.assertEqual(self.s['desktop_incident']['timer_minutes'],duration)
    self.assertEqual(t['timer']['mode'],'challenge');self.assertEqual(t['timer']['limit'],duration*60)
    self.assertEqual(t['timer']['started'],bool(duration));self.assertEqual(t['arrival_plan'],old_plan)
    self.assertEqual(t['title'],self.s['desktop_incident']['title'])
 def test_restart_preserves_queue_and_pauses(self):
  self.d.create();self.d.control(True);saved=copy.deepcopy(self.t.state['tickets'])
  fresh=Tickets(Fake(),self.t.path);desk=ServiceDesk(fresh,Mock())
  self.assertEqual(fresh.state['tickets'],saved);self.assertFalse(desk.settings['active'])

import test_client_workspaces as fixtures
class ActualActivationTests(unittest.TestCase):
 setUp=fixtures.ClientWorkspacesTests.setUp
 proofs=fixtures.ClientWorkspacesTests.proofs
 def test_second_station_activation_uses_real_engine_and_stable_id(self):
  self.c.workspace.save()
  t=Tickets(Fake(),Path(self.tmp.name)/'queue.json');t.controller=self.c
  t.state['site']={'environment_id':'env','devices':[]}
  t.desk=ServiceDesk(t,Mock());t.desk.settings['source']='site'
  arrivals.receive(t,'apps','peripherals',client_serial='second');ident=t.state['tickets'][0]['id']
  self.c.observe=Mock();self.c.on_change=lambda state,folder:t.append_workspace_incident(state)
  t.action(ident,'take',{})
  self.assertEqual(t.state['tickets'][0]['status'],'en_cours')
  self.assertTrue(t.state['tickets'][0]['timer']['started'])
  self.assertEqual(len(t.state['tickets']),1)
  self.assertEqual(self.c.workspace.state['desktop_incident']['id'],ident)
  self.assertEqual(self.c.workspace.state['desktop_incident']['target_serial'],'second')
  self.assertEqual(t.state['tickets'][0]['request_context']['serial'],'second')
  self.assertEqual(t.state['tickets'][0]['request_context']['requester'],self.s['client_workspaces']['second']['requester'])
  self.assertEqual(self.c.workspace.state['devices']['client']['serial'],'client')
  self.c.observe.assert_not_called()

 def test_new_company_starts_with_connected_reference_and_varied_queue(self):
  import workspace_network
  import xml.etree.ElementTree as ET
  with tempfile.TemporaryDirectory() as folder:
   # Real topology builder; encryption is covered by the mandatory core suite.
   with __import__('unittest').mock.patch('workspace_network.ptexplorer.ptfile_encode'):
    state=workspace_network.build('queue-healthy',folder,initial_fault=False)
   self.assertEqual(state['arrival_queue_version'],1)
   self.assertTrue(state['read_allowed']);self.assertTrue(state['write_allowed'])
   def links(name):return ET.tostring(ET.parse(Path(folder)/name).getroot().find('NETWORK/LINKS'))
   self.assertEqual(links('initial.xml'),links('reference.xml'))
