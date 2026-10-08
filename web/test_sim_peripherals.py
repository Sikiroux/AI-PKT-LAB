import copy
import json
import unittest
import sim_peripherals as peripherals
from test_files_integration import FilesIntegrationTests

class PeripheralTests(unittest.TestCase):
    setUp=FilesIntegrationTests.setUp
    def state(self,serial='client'):
        return self.c.peripherals('state',{'station_serial':serial})
    def op(self,operation,**kw):
        return self.c.peripherals('operation',dict(station_serial='client',operation=operation,expected_revision=self.s['peripherals']['revision'],**kw))
    def item(self,kind):
        return next(i for i in self.state()['items'] if i['kind']==kind and i['station_serial']=='client')
    def test_monitor_controls_preserve_network_and_remote_session(self):
        monitor=self.item('monitor');devices=copy.deepcopy(self.s['devices']);obs=copy.deepcopy(self.s['observation'])
        r=self.op('power',item_id=monitor['id'],value=False)
        self.assertEqual(r['checks']['monitor']['code'],'POWER_OFF')
        self.assertTrue(self.s['remote_session']);self.assertEqual(self.s['devices'],devices);self.assertEqual(self.s['observation'],obs)
        self.op('power',item_id=monitor['id'],value=True)
        self.assertEqual(self.op('input',item_id=monitor['id'],value='DisplayPort')['checks']['monitor']['code'],'WRONG_INPUT')
        self.assertTrue(self.op('input',item_id=monitor['id'],value='HDMI')['checks']['monitor']['available'])
    def test_mouse_keyboard_connections_are_independent(self):
        for kind in ('keyboard','mouse'):
            i=self.item(kind)
            self.assertEqual(self.op('connection',item_id=i['id'],value=False)['checks'][kind]['code'],'CABLE_DISCONNECTED')
            self.assertTrue(self.state()['checks']['monitor']['available'])
            self.assertTrue(self.op('connection',item_id=i['id'],value=True)['checks'][kind]['available'])
    def test_broken_hardware_requires_replacement_and_old_item_is_preserved(self):
        old=self.item('monitor');self.s['peripherals']['items'][old['id']]['working']=False
        self.assertEqual(self.state()['checks']['monitor']['code'],'HARDWARE_FAILED')
        r=self.op('add',kind='monitor');new=next(i for i in r['items'] if i['station_serial'] is None)
        self.assertTrue(self.op('attach',item_id=new['id'])['checks']['monitor']['available'])
        self.assertIsNone(self.s['peripherals']['items'][old['id']]['station_serial'])
        self.assertFalse(self.s['peripherals']['items'][old['id']]['working'])
    def test_detached_device_can_be_reinstalled(self):
        i=self.item('keyboard');self.assertEqual(self.op('detach',item_id=i['id'])['checks']['keyboard']['code'],'ABSENT')
        self.assertTrue(self.op('attach',item_id=i['id'])['checks']['keyboard']['available'])
    def test_revision_and_payload_rejections_do_not_mutate_state(self):
        i=self.item('monitor');before=copy.deepcopy(self.s['peripherals'])
        for kw in (dict(operation='power',item_id=i['id'],value='false'),dict(operation='repair',item_id=i['id']),dict(operation='add',kind='router'),dict(operation='power',item_id=i['id'],value=False,expected_revision=True)):
            with self.assertRaises(ValueError):self.c.peripherals('operation',dict({'station_serial':'client','expected_revision':before['revision']},**kw))
            self.assertEqual(before,self.s['peripherals'])
        self.op('power',item_id=i['id'],value=False)
        with self.assertRaises(ValueError):self.c.peripherals('operation',dict(station_serial='client',operation='power',item_id=i['id'],value=True,expected_revision=0))
    def test_cross_station_and_unknown_serial_rejected(self):
        self.state();other=next(i for i in self.state('technician')['items'] if i['station_serial']=='technician')
        with self.assertRaises(ValueError):self.op('detach',item_id=other['id'])
        with self.assertRaises(ValueError):self.state('unknown')
    def test_routes_refuse_foreign_environment_and_client_scope(self):
        from unittest.mock import Mock
        from workspace_routes import WorkspaceRoutes
        handler=Mock();handler.path='/workspace/peripherals/state'
        routes=WorkspaceRoutes(self.c,'token')
        with self.assertRaises(ValueError):routes.post(handler,{'environment_id':'foreign','station_serial':'client'})
        with self.assertRaises(ValueError):routes.post(handler,{'environment_id':'env','client_serial':'client','station_serial':'client'})
        handler.send.assert_not_called()
    def test_scope_mismatch_rejected(self):
        self.state();self.s['peripherals']['environment_id']='other'
        with self.assertRaises(ValueError):self.state()
    def test_ids_reproducible_and_state_saved(self):
        self.state();model=copy.deepcopy(self.s['peripherals']);copy_state=copy.deepcopy(self.s);del copy_state['peripherals']
        self.assertEqual(model,peripherals.ensure(copy_state,self.c.workspace.workstations()))
        i=self.item('mouse');self.op('detach',item_id=i['id'])
        saved=json.loads(self.c.workspace.path.read_text())
        self.assertEqual(saved['peripherals'],self.s['peripherals'])

del FilesIntegrationTests
