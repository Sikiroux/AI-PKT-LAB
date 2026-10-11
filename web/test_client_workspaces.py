import copy
import unittest
from unittest.mock import Mock,patch
import test_desktop_services as fixtures
import client_workspaces as clients
import desktop_services as ds
from workspace_model import Workspace
from workspace_routes import WorkspaceRoutes

class ClientWorkspacesTests(unittest.TestCase):
    proofs=fixtures.ServicesTests.proofs
    def setUp(self):
        fixtures.ControllerTests.setUp(self)
        self.s['devices']['client2']=dict(id='client2',name='second',serial='second',ip='192.168.50.3')
        clients.ensure(self.s);self.second='second';self.routes=WorkspaceRoutes(self.c,'token')
    def scope(self):return self.c.client_scope(self.second)
    def post(self,path,data):
        handler=Mock();handler.path='/workspace/'+path
        self.routes.post(handler,dict(environment_id='env',client_serial=self.second,**data));return handler.send.call_args.args[1]
    def prove_second(self):
        with self.scope():self.proofs(self.c.workspace.state)
    def test_distinct_identity_local_files_and_read_grants(self):
        r=self.s['client_workspaces']['second'];self.assertNotEqual(r['user_id'],self.s['directory_user_id'])
        self.assertIn(r['requester'],r['endpoint']['local_files']['Bienvenue.txt'])
        self.assertIsNone(r['local']['observation']);self.assertFalse(r['local']['remote_session'])
        self.assertFalse(clients.ensure(self.s))
    def test_scope_restores_primary_even_after_error(self):
        before=copy.deepcopy(self.s['devices']['client'])
        with self.assertRaisesRegex(ValueError,'stop'):
            with self.scope():
                self.assertEqual(self.c.workspace.state['devices']['client']['name'],'second')
                self.c.workspace.state['desktop_services']['endpoint']['local_files']['Own.txt']='second';raise ValueError('stop')
        self.assertEqual(self.c.workspace.state,self.s);self.assertEqual(self.s['devices']['client'],before)
        self.assertNotIn('Own.txt',self.s['desktop_services']['endpoint']['local_files'])
        self.assertEqual(self.s['client_workspaces']['second']['endpoint']['local_files']['Own.txt'],'second')
    def test_connect_requires_own_proof_not_primary(self):
        with self.assertRaises(ValueError):self.post('action',dict(action='connect',target_serial='second'))
        self.prove_second();self.post('action',dict(action='connect',target_serial='second'))
        self.assertTrue(self.s['client_workspaces']['second']['local']['remote_session'])
        self.s['remote_session']=False
        view=self.c.public_snapshot('second');self.assertTrue(view['remote_session']);self.assertEqual(view['client_serial'],'second')
    def test_local_save_is_isolated_and_survives_reopen(self):
        self.prove_second();self.post('desktop/endpoint/save-local',dict(payload=dict(name='Own.txt',content='Only second')))
        self.assertNotIn('Own.txt',self.s['desktop_services']['endpoint']['local_files'])
        saved=Workspace(self.c.workspace.path).state
        self.assertEqual(saved['client_workspaces']['second']['endpoint']['local_files']['Own.txt'],'Only second')
        self.assertFalse(saved['client_workspaces']['second']['local']['remote_session']);self.assertIsNone(saved['client_workspaces']['second']['local']['directory_auth'])
        self.assertEqual(saved['devices']['client']['serial'],'client')
    def test_application_drive_and_print_queue_do_not_leak(self):
        self.prove_second();self.post('desktop/endpoint/operation',dict(operation='set_application',payload=dict(id='ftp',installed=False)))
        self.post('desktop/printing/operation',dict(operation='set_default',payload=dict(queue_id='pdf')))
        self.assertIn('ftp',self.s['desktop_services']['endpoint']['applications'])
        self.assertNotIn('ftp',self.s['client_workspaces']['second']['endpoint']['applications'])
        self.assertEqual(self.s['desktop_services']['printing']['default_queue'],'office')
        self.assertEqual(self.s['client_workspaces']['second']['printing']['default_queue'],'pdf')
    def test_ftp_and_dns_sessions_and_cache_are_isolated(self):
        self.prove_second();self.post('desktop/ftp/login',dict(payload=dict(username='depot',password='Formation!2026')))
        self.assertNotIn('client',self.s['desktop_services']['ftp']['sessions'])
        self.assertIsNotNone(self.s['client_workspaces']['second']['ftp_session'])
        with self.scope():
            self.c.workspace.state['dns_service']['cache']['client']={'own':{'marker':'second'}}
        self.assertEqual(self.s['dns_service']['cache'].get('client',{}),{})
        self.assertEqual(self.s['client_workspaces']['second']['dns_cache']['own']['marker'],'second')
    def test_real_dns_resolve_uses_second_and_keeps_primary_cache(self):
        self.prove_second();self.post('dns/resolve',dict(source='client',query=dict(name=self.s['documents_dns_name'],type='A')))
        self.assertTrue(self.s['client_workspaces']['second']['dns_cache']);self.assertEqual(self.s['dns_service']['cache']['client'],{})
    def test_ftp_files_shared_but_authentication_per_client(self):
        self.prove_second();self.post('desktop/ftp/login',dict(payload=dict(username='depot',password='Formation!2026')))
        self.post('desktop/ftp/upload',dict(payload=dict(name='Shared.txt',content='Shared',expected_revision=self.s['desktop_services']['ftp']['revision'])))
        self.assertEqual(self.s['desktop_services']['ftp']['files']['Shared.txt'],'Shared')
        self.assertNotIn('client',self.s['desktop_services']['ftp']['sessions'])
    def test_invalid_identity_environment_and_global_action_rejected(self):
        for serial in ('missing','tech'):
            with self.assertRaises(ValueError):self.post('action',dict(action='connect',target_serial=serial))
        handler=Mock();handler.path='/workspace/desktop/endpoint/save-local'
        with self.assertRaises(ValueError):self.routes.post(handler,dict(environment_id='other',client_serial='second',payload=dict(name='bad',content='bad')))
        with self.assertRaises(ValueError):self.post('action',dict(action='reset'))
    def test_network_observer_pings_both_actual_pc_names(self):
        import threading
        self.s['network_file']='C:/agency.pkt';engine=Mock();engine.lock=threading.RLock()
        engine.snapshot.return_value=dict(saved_filename=self.s['network_file'],devices=[dict(d,ports=[dict(name='FastEthernet0',linked=True,ip=d['ip'],mask='255.255.255.0')]) for d in self.s['devices'].values()])
        engine.ping.return_value=dict(status='valide',detail='reply');self.c.engine=engine;self.c.observe(True)
        calls=[x.args for x in engine.ping.call_args_list]
        self.assertIn(('technician','192.168.50.2'),calls);self.assertIn(('technician','192.168.50.3'),calls)
        self.assertIn(('second','192.168.50.10'),calls)
        r=self.s['client_workspaces']['second'];self.assertEqual(r['local']['observation']['probes']['share']['source_device'],'second')
        self.assertEqual(self.s['observation']['probes']['share']['source_device'],'client')
    def test_discreet_observation_is_batched_targeted_and_manual_only(self):
        from diagnostic import Engine
        self.s['network_file']='C:/agency.pkt';engine=Engine(Mock())
        engine.snapshot=Mock(return_value=dict(saved_filename=self.s['network_file'],devices=[dict(d,ports=[dict(name='FastEthernet0',linked=True,ip=d['ip'],mask='255.255.255.0')]) for d in self.s['devices'].values()]))
        engine.quiet_pings=Mock(return_value=[dict(status='valide',detail='ICMP IPC') for _ in range(4)])
        engine.ping=Mock();self.c.engine=engine
        self.c.observe(True,client_serial='second',accelerate=True)
        self.assertEqual(engine.quiet_pings.call_count,1)
        self.assertTrue(engine.quiet_pings.call_args.kwargs['accelerate'])
        self.assertEqual(engine.quiet_pings.call_args.args[0][0],('technician','192.168.50.3'))
        engine.quiet_pings.reset_mock();self.c.observe()
        self.assertEqual(engine.quiet_pings.call_count,2)
        self.assertTrue(all(not call.kwargs['accelerate'] for call in engine.quiet_pings.call_args_list))
        engine.ping.assert_not_called()

    def test_failure_of_second_closes_only_second_session(self):
        self.prove_second();self.s['client_workspaces']['second']['local']['observation']['probes']['remote']['status']='failed'
        self.assertFalse(self.c.public_snapshot('second')['checks']['remote']['allowed']);self.assertTrue(self.c.public_snapshot()['checks']['remote']['allowed'])
    def test_workstation_list_has_two_supported_clients_and_separate_technician(self):
        rows=self.c.workspace.workstations();self.assertEqual(len([r for r in rows if r['remote_supported']]),2)
        self.assertEqual(len([r for r in rows if r['role']=='technician']),1)
    def test_secondary_preparation_ticket_targets_second(self):
        self.prove_second();result=self.post('desktop-incident',dict(target='workstation_setup',minutes=13))
        i=self.s['desktop_incident'];self.assertEqual(i['target_serial'],'second');self.assertEqual(i['target_name'],'second')
        self.assertIn('second',i['description']);self.assertEqual(self.s['devices']['client']['serial'],'client')
        self.assertEqual(result['desktop_incident']['target_serial'],'second')
        import desktop_incidents
        self.assertFalse(all(r['status']=='valide' for r in desktop_incidents.checks(self.s,self.now)))
        with self.assertRaises(ValueError):self.post('desktop-incident',dict(target='printing',minutes=10))
    def test_ftp_account_change_invalidates_both_clients(self):
        self.prove_second();self.post('desktop/ftp/login',dict(payload=dict(username='depot',password='Formation!2026')))
        self.s['desktop_services']['ftp']['sessions']['client']={'username':'depot'}
        with self.scope():self.c.workspace.state['desktop_services']['ftp']['accounts']['depot']['enabled']=False
        self.assertEqual(self.s['desktop_services']['ftp']['sessions'],{})
        self.assertIsNone(self.s['client_workspaces']['second']['ftp_session'])

    def test_audit_only_directory_changes_keep_other_user_session(self):
        auth=dict(user_id=self.s['directory_user_id'],status='authenticated')
        self.s['directory_auth']=copy.deepcopy(auth)
        with self.scope():
            self.c.workspace.state['directory']['audit'].append(dict(operation='login',code='OK'))
            self.c.workspace.state['directory']['revision']+=1
        self.assertEqual(self.s['directory_auth'],auth)

    def test_public_cache_stays_canonical_during_secondary_scope(self):
        primary=self.s['devices']['client']['serial']
        with self.scope():
            snapshot=self.c.public_snapshot()
            self.assertEqual(snapshot['client_serial'],primary)
            second=self.c.public_snapshot('second')
            self.assertEqual(second['client_serial'],'second')
            self.assertGreaterEqual(len(snapshot['workstations']),2)

    def test_primary_scope_publishes_fresh_session_snapshot(self):
        with self.c.client_scope(None):
            self.s['remote_session']=True
        self.assertTrue(self.c._read_state['remote_session'])

    def test_password_admin_invalidates_other_client_auth(self):
        self.prove_second();self.post('directory/operation',dict(operation='reset_password',payload=dict(user_id=self.s['directory_user_id'])))
        self.assertIsNone(self.s['directory_auth'])

if __name__=='__main__':unittest.main()
