import copy,json,re,threading,time,unittest
from pathlib import Path
from unittest.mock import Mock,patch
import test_client_workspaces as fixtures
from tickets_app import Tickets
import enterprise_incidents as live
import enterprise_network_incidents as network
import ticket_arrivals

class Bridge:
 def __init__(self,s):
  self.lock=threading.Lock();self.fail=False;self.uncertain=False;self.changed_serial=False;self.calls=[]
  self.device=copy.deepcopy(s['devices']['client2'])
  self.device['ports']=[dict(name='FastEthernet0',dhcp_client=False,ip_editable=True,ip=self.device['ip'],mask='255.255.255.0')]
  self.baseline=self.device['ip']
 def snapshot(self):
  result=copy.deepcopy(self.device)
  if self.changed_serial:result['serial']='replacement'
  return dict(devices=[result])
 def call(self,code):
  self.calls.append(code)
  data=json.loads(re.search(r'var v=(\{.*?\}),d=',code).group(1))
  if self.fail:
   if self.uncertain:self.device['ports'][0]['ip']='192.168.222.5'
   raise RuntimeError('Pont indisponible')
  self.device['ports'][0].update(ip=data['ip'],mask=data['mask']);return 'ok'
 def quiet_pings(self,*args,**kwargs):pass

class NetworkTests(unittest.TestCase):
 def setUp(self):
  self.f=fixtures.ClientWorkspacesTests();self.f.setUp();self.addCleanup(self.f.doCleanups)
  self.c=self.f.c;self.s=self.f.s;self.s['staff_size']=30;self.bridge=Bridge(self.s);self.c.engine=self.bridge
  self.t=Tickets(self.bridge,Path(self.f.tmp.name)/'network-tickets.json');self.t.controller=self.c
  self.t.state['site']=dict(environment_id='env',devices=[dict(name=self.bridge.device['name'],serial='second')])
  def observe(**kwargs):
   serial=kwargs.get('client_serial','second')
   with self.c.client_scope(serial):
    self.f.proofs(self.c.workspace.state)
    for proof in self.c.workspace.state['observation']['probes'].values():proof['status']='passed' if self.bridge.device['ports'][0]['ip']==self.bridge.baseline else 'failed'
  self.c.observe=observe;self.c.on_change=lambda state,folder:self.t.append_workspace_incident(state)
 def receive(self,delay=0,fault='ip_wrong'):
  class Choice:
   def choice(self,items):
    preferred=('network',fault)
    if preferred in items:return preferred
    return items[0]
  with patch('enterprise_incidents.random.Random',return_value=Choice()):return ticket_arrivals.receive(self.t,'mixed','network',client_serial='second',discovery_delay=delay)

 def test_receive_mutates_real_endpoint_before_report_and_verify_requires_repair(self):
  self.receive();t=self.t.state['tickets'][0]
  self.assertEqual(t['live_family'],'network');self.assertNotEqual(self.bridge.device['ports'][0]['ip'],self.bridge.baseline)
  self.assertNotIn('192.168.250.',str(self.t.public()))
  self.assertNotIn('network_injections',self.c.public_snapshot())
  self.t.live_workspace_action(t,'verify');self.assertFalse(t['complete'])
  self.bridge.device['ports'][0]['ip']=self.bridge.baseline
  self.t.live_workspace_action(t,'verify');self.assertTrue(t['complete']);self.assertTrue(all(r['status']=='valide' for r in t['checks']))
 def test_discovery_delay_retains_network_failure(self):
  self.receive(20);self.assertFalse(self.t.state['tickets'])
  record=next(iter(self.s['live_incidents'].values()))
  self.assertEqual(record['lifecycle'],'awaiting_activity')
  live.discover(self.t,record['discovery_due']+1)
  self.assertEqual(len(self.t.state['tickets']),1);self.assertEqual(record['lifecycle'],'reported')
 def test_preexisting_failure_never_mutates(self):
  self.bridge.device['ports'][0]['ip']='10.9.9.2'
  with self.assertRaises(ValueError):self.receive()
  self.assertFalse(self.bridge.calls);self.assertFalse(self.t.state['tickets'])
 def test_wrong_identity_never_mutates(self):
  self.bridge.changed_serial=True
  with self.assertRaises(ValueError):self.receive()
  self.assertFalse(self.bridge.calls)
 def test_failed_apply_and_unknown_configuration_block_until_manual_repair(self):
  self.bridge.fail=True;self.bridge.uncertain=True
  with self.assertRaises(RuntimeError):self.receive()
  self.assertFalse(self.t.state['tickets']);self.assertEqual(next(iter(self.s['network_injections'].values()))['state'],'uncertain')
  with self.assertRaises(ValueError):live.receive(self.t,'ad',client_serial='client')
  self.bridge.fail=False;self.bridge.device['ports'][0]['ip']=self.bridge.baseline
  network.reconcile(self.t);network.guard_pending(self.s)
 def test_unsupported_engine_excludes_network_from_catalogue(self):
  self.c.engine=None
  with self.assertRaises(ValueError):self.receive()
  self.assertFalse(self.bridge.calls)
 def test_obsolete_verification_never_passes(self):
  self.receive();t=self.t.state['tickets'][0];record=self.s['network_injections'][t['id']]
  self.bridge.device['ports'][0]['ip']=self.bridge.baseline;self.t.live_workspace_action(t,'verify')
  rows=network.checks(self.s,t,time.time()+100)
  self.assertTrue(any(r['status']=='inconnu' for r in rows))
 def test_unconfirmed_effect_rolls_back_without_ticket(self):
  def healthy(**kwargs):
   with self.c.client_scope(kwargs.get('client_serial','second')):self.f.proofs(self.c.workspace.state)
  self.c.observe=healthy
  with self.assertRaises(ValueError):self.receive()
  self.assertFalse(self.t.state['tickets']);self.assertEqual(self.bridge.device['ports'][0]['ip'],self.bridge.baseline)
  self.assertEqual(next(iter(self.s['network_injections'].values()))['state'],'restored')
 def test_scheduler_applies_then_reports_network_incident(self):
  from service_desk import ServiceDesk
  self.t.desk=ServiceDesk(self.t,Mock(jobs=lambda:[]))
  self.t.desk.configure(dict(source='site',arrival_engine='mixed',mixed_target='network',max_open=1))
  now=time.time();self.t.desk.settings.update(active=True,next_at=now-1)
  class Choice:
   def choice(self,items):return 'second' if 'second' in items else items[0]
  with patch('enterprise_incidents.random.Random',return_value=Choice()):self.t.desk.tick(now)
  self.assertNotEqual(self.bridge.device['ports'][0]['ip'],self.bridge.baseline)
  self.assertFalse(self.t.state['tickets'])
  record=next(iter(self.s['live_incidents'].values()))
  self.t.desk.tick(record['discovery_due']+1)
  self.assertEqual(len(self.t.state['tickets']),1);self.assertEqual(self.t.state['tickets'][0]['live_family'],'network')

 def test_mask_fault_can_break_server_access_while_remote_stays_up(self):
  def observe(**kwargs):
   with self.c.client_scope(kwargs.get('client_serial','second')):
    self.f.proofs(self.c.workspace.state)
    if self.bridge.device['ports'][0]['mask']!='255.255.255.0':self.c.workspace.state['observation']['probes']['share']['status']='failed'
  self.c.observe=observe
  self.receive(fault='mask_wrong');t=self.t.state['tickets'][0]
  self.assertEqual(self.bridge.device['ports'][0]['ip'],self.bridge.baseline)
  self.assertNotEqual(self.bridge.device['ports'][0]['mask'],'255.255.255.0')
  self.t.live_workspace_action(t,'verify');self.assertFalse(t['complete'])
  self.bridge.device['ports'][0]['mask']='255.255.255.0'
  self.t.live_workspace_action(t,'verify');self.assertTrue(t['complete'])
 def test_wrong_mask_baseline_is_rejected_without_mutation(self):
  self.bridge.device['ports'][0]['mask']='255.255.0.0'
  with self.assertRaises(ValueError):self.receive()
  self.assertFalse(self.bridge.calls)

 def test_missing_or_replaced_configuration_is_unknown_not_a_failed_reading(self):
  self.receive();t=self.t.state['tickets'][0]
  self.bridge.changed_serial=True
  network.refresh(self.t,t)
  self.assertEqual(self.s['network_injections'][t['id']]['verification']['status'],'unknown')
  self.bridge.changed_serial=False
  self.bridge.device['ports'][0].pop('mask')
  network.refresh(self.t,t)
  self.assertEqual(self.s['network_injections'][t['id']]['verification']['status'],'unknown')

 def test_ambiguous_identity_cannot_validate_repair(self):
  self.receive();t=self.t.state['tickets'][0]
  self.bridge.device['ports'][0]['ip']=self.bridge.baseline
  snapshot=self.bridge.snapshot();snapshot['devices'].append(copy.deepcopy(snapshot['devices'][0]))
  with patch.object(self.bridge,'snapshot',return_value=snapshot):network.refresh(self.t,t)
  self.assertEqual(self.s['network_injections'][t['id']]['verification']['status'],'unknown')
  self.assertFalse(__import__('live_faults').matches(snapshot,self.s['network_injections'][t['id']]['mutation'],True))

 def test_begin_simulation_reports_first_incident_immediately(self):
  from service_desk import ServiceDesk
  self.t.desk=ServiceDesk(self.t,Mock(jobs=lambda:[]))
  self.t.desk.settings.update(source='site',preparing=True,active=False)
  class Choice:
   def choice(self,items):
    if ('network','ip_wrong') in items:return ('network','ip_wrong')
    if 'network' in items:return 'network'
    if 'ip_wrong' in items:return 'ip_wrong'
    return 'second' if 'second' in items else items[0]
  with patch('enterprise_incidents.random.Random',return_value=Choice()):self.t.desk.control(True)
  self.assertEqual(len(self.t.state['tickets']),1)
  ticket=self.t.state['tickets'][0]
  self.assertEqual(ticket['live_family'],'network')
  self.assertNotEqual(self.bridge.device['ports'][0]['ip'],self.bridge.baseline)
  self.assertTrue(self.t.desk.settings['active'])
  self.assertGreater(self.t.desk.settings['next_at'],time.time())
  self.t.desk.control(True)
  self.assertEqual(len(self.t.state['tickets']),1)
