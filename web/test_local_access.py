import copy
import json
import unittest
from unittest.mock import Mock
from test_files_integration import FilesIntegrationTests
import workspace_model

class LocalAccessTests(unittest.TestCase):
    setUp=FilesIntegrationTests.setUp
    def state(self,serial='client'):return self.c.credentials('state',{'station_serial':serial})
    def op(self,operation,**kw):
        return self.c.credentials('operation',dict(station_serial='client',operation=operation,expected_revision=self.s['local_access']['revision'],**kw))
    def secret(self):self.state();return self.op('reveal')['password']
    def test_secret_is_explicit_and_absent_from_normal_views(self):
        public=self.state();self.assertNotIn('password',public);secret=self.secret()
        self.assertNotIn(secret,json.dumps(self.c.workspace.public()))
        self.assertNotIn(secret,json.dumps(self.s['events']))
        self.assertNotIn(secret,json.dumps(self.s['local_access']['history']))
    def test_actual_authentication_is_station_local_and_not_ad(self):
        secret=self.secret();directory=copy.deepcopy(self.s['directory']);auth=self.s.get('directory_auth');devices=copy.deepcopy(self.s['devices'])
        self.assertFalse(self.op('login',username='support.local',password=secret)['result']['allowed'])
        self.assertFalse(self.op('login',username='.\\support.local',password='incorrect')['result']['allowed'])
        self.assertTrue(self.op('login',username='.\\support.local',password=secret)['result']['allowed'])
        self.assertEqual(directory,self.s['directory']);self.assertEqual(auth,self.s.get('directory_auth'));self.assertEqual(devices,self.s['devices'])
        other=self.state('technician');self.assertFalse(other['authenticated'])
    def test_reset_updates_vault_and_hash_closes_session(self):
        old=self.secret();self.op('login',username='.\\support.local',password=old)
        new='NouveauLocal!2026';self.op('reset',password=new)
        self.assertFalse(self.state()['authenticated']);self.assertEqual(new,self.op('reveal')['password'])
        self.assertFalse(self.op('login',username='.\\support.local',password=old)['result']['allowed'])
        self.assertTrue(self.op('login',username='.\\support.local',password=new)['result']['allowed'])
        self.assertNotIn(new,json.dumps(self.s['events']))
    def test_disabled_account_and_logout(self):
        secret=self.secret();self.op('enable',enabled=False)
        self.assertFalse(self.op('login',username='.\\support.local',password=secret)['result']['allowed'])
        self.op('enable',enabled=True);self.op('login',username='.\\support.local',password=secret)
        self.assertFalse(self.op('logout')['authenticated'])
    def test_stale_revision_invalid_input_and_foreign_station(self):
        self.state();before=copy.deepcopy(self.s['local_access'])
        for params in ({'operation':'reset','password':'short'}, {'operation':'enable','enabled':'false'}, {'operation':'reveal','expected_revision':True}):
            with self.assertRaises(ValueError):self.c.credentials('operation',dict({'station_serial':'client','expected_revision':0},**params))
            self.assertEqual(before,self.s['local_access'])
        with self.assertRaises(ValueError):self.state('not-here')
        self.op('reset',password='ValidLocal!2026')
        with self.assertRaises(ValueError):self.c.credentials('operation',dict(station_serial='client',operation='reveal',expected_revision=0))
    def test_persistence_and_restart_session_invalidation(self):
        secret=self.secret();self.op('login',username='.\\support.local',password=secret)
        reloaded=workspace_model.Workspace(self.c.workspace.path)
        self.assertEqual(secret,reloaded.state['local_access']['vault']['client']['password'])
        self.assertFalse(reloaded.state['local_access']['sessions'])
    def test_wrong_environment_rejected(self):
        self.state();self.s['local_access']['environment_id']='other'
        with self.assertRaises(ValueError):self.state()
    def test_routes_refuse_foreign_environment_and_client_desktop(self):
        from workspace_routes import WorkspaceRoutes
        handler=Mock();handler.path='/workspace/credentials/state';r=WorkspaceRoutes(self.c,'token')
        for data in ({'environment_id':'foreign','station_serial':'client'}, {'environment_id':'env','client_serial':'client','station_serial':'client'}):
            with self.assertRaises(ValueError):r.post(handler,data)
        handler.send.assert_not_called()

del FilesIntegrationTests
