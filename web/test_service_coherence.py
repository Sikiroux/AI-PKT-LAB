"""Sessions indépendantes des preuves réseau et trajets communs bien identifiés."""
import copy
import threading
import unittest
from types import SimpleNamespace
from unittest.mock import patch
import test_client_workspaces as fixtures
import directory_adapter as ad
import network_proofs
import technician_model
from workspace_model import evaluate,Workspace

class CoherenceTests(unittest.TestCase):
 setUp=fixtures.ClientWorkspacesTests.setUp
 proofs=fixtures.ClientWorkspacesTests.proofs
 def open(self):self.s['directory_auth']=ad.open_session(self.s,self.now)
 def test_windows_logon_survives_thirty_minutes_and_network_expiration(self):
  self.open();before=copy.deepcopy(self.s['directory_auth'])
  self.assertEqual(ad.context(self.s,now=self.now+3600)['authentication'],before)
  self.assertEqual(ad.context(self.s,now=self.now+3600)['network']['status'],'unknown')
  self.assertTrue(self.s['remote_session'])
 def test_other_account_is_not_shown_as_authenticated(self):
  self.open();self.s['directory_auth']['user_id']=self.s['client_workspaces']['second']['user_id']
  self.assertFalse(ad.context(self.s,now=self.now)['authentication'])
 def test_same_alias_on_another_station_cannot_reuse_windows_logon(self):
  self.open();self.s['devices']['client']['serial']='different-station'
  self.assertFalse(ad.context(self.s,now=self.now)['authentication'])
 def test_password_reset_invalidates_token_without_dependency_on_network(self):
  self.open();self.s['directory']['users'][self.s['directory_user_id']]['credential']['salt']='changed'
  self.assertFalse(ad.context(self.s,now=self.now)['authentication'])
 def test_group_changes_preserve_windows_logon(self):
  self.open();before=copy.deepcopy(self.s['directory_auth'])
  group=next(iter(self.s['directory']['groups'].values()));group['member_user_ids']=[]
  self.assertEqual(ad.context(self.s,now=self.now)['authentication'],before)
 def test_disabled_account_and_legacy_expiration_are_not_authenticated(self):
  self.s['directory_auth']['expires_at']=self.now
  self.assertFalse(ad.context(self.s,now=self.now)['authentication'])
  self.open();self.s['directory']['users'][self.s['directory_user_id']]['enabled']=False
  self.assertFalse(ad.context(self.s,now=self.now)['authentication'])
 def test_remote_pair_refuses_wrong_source_target_and_future_stamp(self):
  p=self.s['observation']['probes']['remote']
  for field,value in [('source_device','other'),('target','192.0.2.9'),('at',self.now+1)]:
   original=p[field];p[field]=value
   self.assertEqual(evaluate(self.s,'remote',self.now)['status'],'unknown');p[field]=original
  self.assertTrue(evaluate(self.s,'remote',self.now)['allowed'])
 def test_aggregate_is_not_a_remote_proof_for_a_bound_company(self):
  self.s['observation']=dict(at=self.now,status='passed')
  self.assertFalse(evaluate(self.s,'remote',self.now)['allowed'])
 def test_malformed_timestamp_cannot_grant_access(self):
  self.s['observation']['probes']['share']['at']='yesterday'
  self.assertEqual(network_proofs.proof(self.s,'share','client',self.s['devices']['server']['ip'],self.now)['status'],'unknown')
 def test_directory_shared_proof_does_not_regress_or_copy_client_probe(self):
  p=copy.deepcopy(self.s['observation']['probes']['directory']);self.c._share_directory_probe(self.s,p)
  older=copy.deepcopy(p);older.update(at=self.now-10,status='failed');self.c._share_directory_probe(self.s,older)
  second=self.s['client_workspaces']['second']['local']['observation']
  self.assertEqual(second['probes']['directory'],p);self.assertNotIn('share',second['probes'])
 def test_vpn_shared_proof_refreshes_policy_for_other_desktops(self):
  technician_model.ensure(self.s);t=self.s['technician_session'];t.update(location='outside',connection='wired')
  t['vpn'].update(connected=True,expires_at=self.now+1000)
  self.s['technician_locations']={'outside':{'gateway':'192.0.2.1','device':'outside-router','port':'GigabitEthernet0/0'}}
  p=dict(at=self.now,status='passed',source_device=self.s['devices']['technician']['name'],target='192.0.2.1')
  self.c._share_directory_probe(self.s,vpn_probe=p)
  with self.c.client_scope('second'):
   self.assertTrue(technician_model.policy(self.c.workspace.state,self.now)['allowed'])
 def test_unknown_poll_preserves_vpn_but_blocks_actions(self):
  technician_model.ensure(self.s);t=self.s['technician_session'];t.update(location='outside',connection='wired')
  t['vpn'].update(connected=True,expires_at=self.now+1000)
  self.s['technician_locations']={'outside':{'gateway':'192.0.2.1','device':'outside-router','port':'GigabitEthernet0/0'}}
  found={key:dict(device,ports=[]) for key,device in self.s['devices'].items()}
  self.c.identities=lambda snapshot, **kwargs:found
  self.c.engine=SimpleNamespace(lock=threading.RLock(),snapshot=lambda:dict(devices=[]),ping=lambda source,target:dict(status='inconnu'))
  self.s['network_file']='training.pkt';self.c._observe_one(blocking=True)
  self.assertIn('vpn_gateway',self.s['observation']['probes'])
  self.assertTrue(t['vpn']['connected']);self.assertEqual(technician_model.policy(self.s,self.now)['status'],'unknown')
 def test_controller_issues_windows_logon_and_restart_clears_it(self):
  outcome=self.c.directory('login',{'password':'Formation!2026'})
  self.assertTrue(outcome['result']['allowed']);self.assertEqual(self.s['directory_auth']['kind'],'windows_logon')
  self.assertNotIn('expires_at',self.s['directory_auth'])
  self.c.workspace.save();loaded=Workspace(self.c.workspace.path)
  self.assertIsNone(loaded.state['directory_auth'])

 def test_vpn_public_separates_open_session_and_unknown_transport(self):
  technician_model.ensure(self.s);t=self.s['technician_session'];t.update(location='outside',connection='wired')
  t['vpn'].update(connected=True,expires_at=self.now+1000)
  self.s['technician_locations']={'outside':{'gateway':'192.0.2.1'}}
  with patch('technician_model.time.time',return_value=self.now):result=technician_model.public(self.s)
  self.assertTrue(result['vpn_connected']);self.assertEqual(result['vpn_access_status'],'unknown')
 def test_network_indicator_rejects_wrong_remote_pair(self):
  import network_monitor
  self.s['observation']['probes']['remote']['source_device']='different'
  self.assertEqual(network_monitor.public_status(self.s,self.now)['status'],'unknown')

 def test_remote_guard_reports_unverified_transport_without_reconnecting(self):
  import desktop_controller
  self.open();before=copy.deepcopy(self.s['directory_auth']);self.s['observation']=None
  with self.assertRaisesRegex(ValueError,'conservés'):desktop_controller.remote(self.s)
  self.assertEqual(self.s['directory_auth'],before);self.assertTrue(self.s['remote_session'])
  self.s['remote_session']=False
  with self.assertRaisesRegex(ValueError,'Ouvre une session'):desktop_controller.remote(self.s)

 def test_disabling_then_reenabling_does_not_revive_old_session(self):
  self.open();uid=self.s['directory_user_id']
  self.c.directory('operation',{'operation':'set_user_enabled','payload':{'user_id':uid,'enabled':False}})
  self.assertIsNone(self.s['directory_auth'])
  self.c.directory('operation',{'operation':'set_user_enabled','payload':{'user_id':uid,'enabled':True}})
  self.assertFalse(ad.context(self.s,now=self.now)['authentication'])
 def test_revocation_is_targeted_to_the_modified_account(self):
  self.open();before=copy.deepcopy(self.s['directory_auth']);uid=self.s['client_workspaces']['second']['user_id']
  self.c.directory('operation',{'operation':'set_user_enabled','payload':{'user_id':uid,'enabled':False}})
  self.assertEqual(self.s['directory_auth'],before)
