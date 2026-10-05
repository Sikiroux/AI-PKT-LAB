import copy, json, tempfile, time, unittest
from unittest.mock import patch, Mock
from workspace_model import generate, evaluate
from workspace_app import Controller
from workspace_routes import WorkspaceRoutes
import directory_adapter as ad
import files_adapter as fa
import dns_adapter as da
import mixed_incidents as mi
import technician_model as tm
import client_dialogue as cd
import workspace_links as wl

class MixedTests(unittest.TestCase):
 def setUp(self):
  self.now=time.time();self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
  self.c=Controller(None,self.tmp.name);self.s=generate('mixed-test');self.s['environment_id']='env'
  self.s['devices']={k:dict(name=k,ip=ip,serial=k) for k,ip in [('client','192.168.1.2'),('server','192.168.1.10'),('technician','192.168.1.20')]}
  ad.ensure(self.s);fa.ensure(self.s);da.ensure(self.s);self.auth(self.s);self.c.workspace.state=self.s
 def auth(self,s):
  s['remote_session']=True;s['directory_auth']=dict(user_id=s['directory_user_id'],status='authenticated',environment_id='env',source_device_id='client',expires_at=self.now+1000)
  s['observation']={'probes':{key:dict(at=self.now,status='passed',source_device=source,target=target) for key,source,target in [('remote','technician','192.168.1.2'),('share','client','192.168.1.10'),('directory','technician','192.168.1.10')]}}
 def repair(self,s):
  uid=s['directory_user_id'];d=s['directory'];d['users'][uid].update(enabled=True,locked_until=None,must_change_password=False,password_expires_at=self.now+1000)
  fs=s['file_service'];fs.update(service_status='running',firewall_tcp445_allowed=True);fs['volume']['capacity_bytes']=10000000
  share=fs['shares'][s['documents_share_id']];share.update(enabled=True,quota=dict(mode='off',limit_bytes=None))
  for right,actions in [('read',('list','read')),('write',('write','delete'))]:
   gid=s['directory_resource']['allowed_group_ids'][right][0]
   if uid not in d['groups'][gid]['member_user_ids']:d['groups'][gid]['member_user_ids'].append(uid)
   for layer in ('share_acl','folder_acl'):
    for action in actions:share[layer][action]['group_ids']=list(dict.fromkeys(share[layer][action]['group_ids']+[gid]))
  fs['files'][s['mixed_incident']['target_file_id']]['read_only']=False
  dns=s['dns_service'];dns.update(service_status='running',transport_allowed=True);dns['clients']['client']['dns_server_ip']=dns['server']['ip'];dns['cache']['client']={}
  for rec in dns['records'].values():
   if rec['name']==s['documents_dns_name'] and rec['type']=='A':rec.update(enabled=True,value=fs['server']['ip'])
  s['mixed_incident']['injection_state']='applied';self.auth(s)
 def test_planner_reproducible_and_layer_count(self):
  for index in range(30):
   for level in (1,2,3):
    result=mi.choose('seed',index,level);self.assertEqual(result,mi.choose('seed',index,level));self.assertEqual(len(result),level);self.assertEqual(len(set(x[0] for x in result)),level)
  self.assertNotEqual(mi.choose('seed',1,3),mi.choose('seed',2,3))
 def test_target_and_invalid_inputs(self):
  for target in mi.CATALOGUE:self.assertEqual(mi.choose('seed',1,2,target)[0][0],target)
  for level in (True,0,4,'2'):
   with self.assertRaises(ValueError):mi.choose('seed',0,level)
  with self.assertRaises(ValueError):mi.choose('seed',0,1,'unknown')
 def test_all_service_causes_fail_then_repair(self):
  for layer,causes in mi.CATALOGUE.items():
   if layer=='network':continue
   for cause in causes:
    with self.subTest(layer=layer,cause=cause),patch.object(mi,'choose',return_value=[(layer,cause)]):s=mi.prepare(self.s,self.now)
    self.auth(s);action=s['mixed_incident']['goal'];self.assertFalse(mi.access(s,action,self.now)['allowed'],(layer,cause))
    self.repair(s);self.assertTrue(all(c['status']=='valide' for c in mi.checks(s,self.now)),(layer,cause,mi.checks(s,self.now)))
 def test_partial_repair_does_not_complete_mixture(self):
  with patch.object(mi,'choose',return_value=[('ad','account_disabled'),('files','service_stopped'),('dns','missing_record')]):s=mi.prepare(self.s,self.now,3)
  self.auth(s);s['directory']['users'][s['directory_user_id']]['enabled']=True
  self.assertFalse(mi.access(s,'read',self.now)['allowed']);s['file_service']['service_status']='running'
  self.assertFalse(mi.access(s,'read',self.now)['allowed']);self.repair(s);self.assertTrue(mi.access(s,'read',self.now)['allowed'])
 def test_private_causes_not_exposed_and_original_not_mutated(self):
  before=copy.deepcopy(self.s);s=mi.prepare(self.s,self.now,2,'ad');self.assertEqual(self.s,before)
  public=mi.public(s);self.assertNotIn('causes',public);self.assertNotIn('baseline',public);self.assertNotIn('account_disabled',public['description'])
 def test_active_incident_blocks_all_special_generators(self):
  import file_incidents,directory_incidents,dns_incidents
  s=mi.prepare(self.s,self.now,1,'ad')
  for fn in (mi.prepare,file_incidents.prepare,directory_incidents.prepare,dns_incidents.prepare):
   with self.assertRaises(ValueError):fn(s,self.now)
 def test_target_deletion_and_other_record_change_rejected(self):
  self.s['dns_service']['records']['other']=dict(id='other',name='other.'+self.s['dns_service']['server']['zone'],type='A',value='192.168.1.11',ttl=300,enabled=True)
  s=mi.prepare(self.s,self.now,1,'ad');self.repair(s)
  original=copy.deepcopy(s);del s['file_service']['files'][s['mixed_incident']['target_file_id']]
  self.assertFalse(all(c['status']=='valide' for c in mi.checks(s,self.now)))
  s=original;rid=next(iter(s['mixed_incident']['baseline']['records']));s['dns_service']['records'][rid]['ttl']+=1
  self.assertEqual(mi.checks(s,self.now)[-2]['status'],'non satisfait')
 def test_stale_proof_cannot_validate(self):
  s=mi.prepare(self.s,self.now,1,'ad');self.repair(s)
  self.assertFalse(all(c['status']=='valide' for c in mi.checks(s,self.now+46)))
 def test_controller_duration_persists_and_dialogue_callback(self):
  result=self.c.next_mixed_incident(1,'ad',17);self.assertEqual(self.c.workspace.state['mixed_incident']['timer_minutes'],17)
  cb=Mock();self.c.on_change=cb;ident=result['mixed_incident']['id']
  self.c.dialogue(dict(ticket_id=ident,question='scope'));cb.assert_called_once()
  stored=json.loads(self.c.workspace.path.read_text());self.assertEqual(len(stored['mixed_incident']['dialogue']),1)
 def test_dialogue_current_state_and_no_repair(self):
  with patch.object(mi,'choose',return_value=[('ad','account_disabled')]):s=mi.prepare(self.s,self.now)
  self.auth(s);ident=s['mixed_incident']['id'];before=copy.deepcopy(s['directory'])
  self.assertIn('désactivé',cd.ask(s,ident,'login',self.now)['answer']);self.assertEqual(s['directory'],before)
  self.repair(s);self.assertIn('ouverte',cd.ask(s,ident,'login',self.now)['answer']);self.assertIn('peux ouvrir',cd.ask(s,ident,'retest',self.now)['answer'])
 def test_dialogue_link_requires_its_own_fresh_observation(self):
  s=mi.prepare(self.s,self.now,1,'ad');ident=s['mixed_incident']['id'];s['observation']['probes']['share']['status']='failed'
  self.assertIn('pas de constat',cd.ask(s,ident,'network',self.now)['answer'])
  s['network_observation']=dict(at=self.now,client_link=False)
  self.assertIn('débranché',cd.ask(s,ident,'network',self.now)['answer']);self.assertIn('pas de constat',cd.ask(s,ident,'network',self.now+46)['answer'])
 def test_wrong_dialogue_and_route_environment_rejected(self):
  s=mi.prepare(self.s,self.now,1,'ad');self.c.workspace.state=s
  with self.assertRaises(ValueError):cd.ask(s,'old','scope',self.now)
  h=Mock();h.path='/workspace/dialogue'
  for data in ({},{'environment_id':'old'}):
   with self.assertRaises(ValueError):WorkspaceRoutes(self.c,'token').post(h,data)
 def test_vpn_requires_fresh_correct_source_gateway_and_password(self):
  s=self.s;tm.ensure(s);s['technician_session'].update(location='outside',connection='wired');s['technician_locations']={'outside':dict(gateway='192.168.2.1')}
  self.assertFalse(tm.vpn(s,'connect','Formation!2026',self.now)['allowed'])
  s['observation']['probes']['vpn_gateway']=dict(at=self.now,status='passed',source_device='technician',target='192.168.2.1')
  self.assertFalse(tm.vpn(s,'connect','wrong',self.now)['allowed']);self.assertTrue(tm.vpn(s,'connect','Formation!2026',self.now)['allowed']);self.assertTrue(tm.policy(s,self.now)['allowed'])
  self.assertFalse(tm.policy(s,self.now+46)['allowed']);self.assertFalse(tm.policy(s,self.now+1801)['allowed'])
  s['observation']['probes']['vpn_gateway']['source_device']='client';self.assertFalse(tm.vpn(s,'connect','Formation!2026',self.now)['allowed'])
 def test_console_pending_and_vpn_disconnect_close_access(self):
  tm.ensure(self.s);t=self.s['technician_session'];t['connection']='console';self.assertFalse(tm.policy(self.s,self.now)['allowed']);self.assertEqual(ad.context(self.s,'technician',self.now)['network']['status'],'failed')
  t['pending']={'location':'office'};self.assertEqual(tm.policy(self.s,self.now)['status'],'unknown');tm.vpn(self.s,'disconnect',now=self.now);self.assertFalse(self.s['remote_session']);self.assertIsNone(self.s['directory_auth'])
 def test_cable_script_guards_and_escapes_name(self):
  js=wl.disconnect_js(dict(name='pc";evil()',serial='serial'),'FastEthernet0',dict(device='switch',port='Fa1'))
  self.assertIn('getSerialNumber()',js);self.assertIn('deleteLink',js);self.assertNotIn('shutdown',js);self.assertIn('pc\\";evil()',js)
 def test_reserved_ports_excluded_from_collateral_signature(self):
  self.s['technician_locations']={'office':dict(device='sw',port='Fa20')}
  snapshot={'devices':[self.s['devices']['client'],dict(name='sw',serial='sw',ports=[dict(name='Fa20',linked=False),dict(name='Fa1',linked=True,peer=dict(device='client',port='FastEthernet0')),dict(name='Fa2',linked=True)])]}
  self.assertEqual(set(wl.signature(snapshot,self.s)),{'sw:Fa2'})

if __name__=='__main__':unittest.main()

class BridgeTests(unittest.TestCase):
 setUp=MixedTests.setUp
 auth=MixedTests.auth
 repair=MixedTests.repair
 def test_cable_failure_persists_uncertain_then_explicit_confirmation(self):
  import threading
  s=self.s;s['network_file']='C:/env/entreprise.pkt'
  client=dict(s['devices']['client'],ports=[dict(name='FastEthernet0',linked=True,peer=dict(device='sw',port='Fa1'))])
  snapshot=dict(saved_filename=s['network_file'],devices=[client,dict(s['devices']['server'],ports=[]),dict(s['devices']['technician'],ports=[]),dict(name='sw',serial='sw',ports=[])])
  engine=Mock();engine.lock=threading.Lock();engine.snapshot.return_value=snapshot;engine.call.side_effect=TimeoutError('bridge timeout');self.c.engine=engine
  with self.assertRaises(TimeoutError):self.c.next_mixed_incident(1,'network',9)
  incident=self.c.workspace.state['mixed_incident'];self.assertEqual(incident['injection_state'],'uncertain');self.assertIsNone(self.c.workspace.state['observation']);self.assertTrue(mi.public(self.c.workspace.state)['requires_confirmation'])
  client['ports'][0].update(linked=False,peer=None);self.c.confirm_mixed_injection();self.assertEqual(incident['injection_state'],'applied');self.assertFalse(mi.public(self.c.workspace.state)['requires_confirmation'])
 def test_wrong_file_blocks_cable_mutation(self):
  import threading
  self.s['network_file']='C:/env/entreprise.pkt';engine=Mock();engine.lock=threading.Lock();engine.snapshot.return_value=dict(saved_filename='C:/other.pkt',devices=[]);self.c.engine=engine
  with self.assertRaises(ValueError):self.c.next_mixed_incident(1,'network')
  engine.call.assert_not_called();self.assertNotIn('mixed_incident',self.c.workspace.state)
 def test_mobility_failed_api_keeps_pending_until_manual_confirmation(self):
  import threading
  s=self.s;s['network_file']='C:/env/entreprise.pkt';dest=dict(label='Serveurs',device='sw',serial='sw',port='FastEthernet0/20',ip='192.168.2.23',mask='255.255.255.0',gateway='192.168.2.1');s['technician_locations']={'server_room':dest}
  tech=dict(s['devices']['technician'],ports=[dict(name='FastEthernet0',linked=False)])
  snapshot=dict(saved_filename=s['network_file'],devices=[dict(s['devices']['client'],ports=[]),dict(s['devices']['server'],ports=[]),tech,dict(name='sw',serial='sw',ports=[])])
  engine=Mock();engine.lock=threading.Lock();engine.snapshot.return_value=snapshot;engine.call.return_value=json.dumps({'error':'API unavailable'});self.c.engine=engine
  with self.assertRaises(ValueError):self.c.technician('move',dict(location='server_room',connection='wired'))
  self.assertIsNotNone(s['technician_session']['pending']);self.assertFalse(s['remote_session']);self.assertIsNone(s['directory_auth'])
  tech['ports'][0].update(linked=True,peer=dict(device='sw',port='FastEthernet0/20'),ip=dest['ip'],mask=dest['mask'])
  self.c.technician('confirm',{});self.assertIsNone(s['technician_session']['pending']);self.assertEqual(s['devices']['technician']['ip'],dest['ip']);self.assertEqual(s['technician_session']['location'],'server_room')
 def test_same_environment_dialogue_does_not_pause_arrivals(self):
  from tickets_app import Tickets
  from service_desk import ServiceDesk
  from pathlib import Path
  s=self.s;s.update(network_file='C:/env/entreprise.pkt',expected_cable={'peer':'sw'})
  t=Tickets(None,Path(self.tmp.name)/'old.json');generator=Mock();t.bind_environment(s,Path(self.tmp.name),generator,self.c)
  t.desk.settings.update(active=True,next_at=12345,mixed_level=3);original=t.desk
  t.bind_environment(s,Path(self.tmp.name),generator,self.c)
  self.assertIs(t.desk,original);self.assertTrue(t.desk.settings['active']);self.assertEqual(t.desk.settings['next_at'],12345)
 def test_ad_group_and_file_acl_failures_remain_independent(self):
  with patch.object(mi,'choose',return_value=[('ad','read_group_missing'),('files','share_read_missing')]):s=mi.prepare(self.s,self.now,2)
  self.auth(s);gid=s['directory_resource']['allowed_group_ids']['read'][0];s['directory']['groups'][gid]['member_user_ids'].append(s['directory_user_id'])
  self.assertFalse(mi.access(s,'read',self.now)['allowed']);self.repair(s);self.assertTrue(mi.access(s,'read',self.now)['allowed'])
