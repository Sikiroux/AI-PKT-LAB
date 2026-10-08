import copy
import unittest
from pathlib import Path
from unittest.mock import Mock,patch
from test_files_integration import FilesIntegrationTests
import peripheral_incidents as incidents
import desktop_incidents
from tickets_app import Tickets

class PeripheralIncidentTests(unittest.TestCase):
    setUp=FilesIntegrationTests.setUp
    def prepare(self,cause=None):
        self.c.peripherals('state',{'station_serial':'client'})
        if cause:
            with patch.object(incidents.random,'Random') as rng:
                rng.return_value.choice.return_value=cause
                return desktop_incidents.prepare(self.s,100,'peripherals',30)
        return desktop_incidents.prepare(self.s,100,'peripherals',30)
    def repair(self,state):
        serial=state['devices']['client']['serial'];self.c.workspace.state=state
        for kind,c in state['peripherals']['items'].copy().items():
            if c['station_serial'] not in (None,serial):continue
            if c['station_serial'] is None:
                if c['id']==next((i['id'] for i in state['peripherals']['items'].values() if i['station_serial']==serial and i['kind']==c['kind']),None):continue
            def op(operation,**kw):return self.c.peripherals('operation',dict(station_serial=serial,operation=operation,expected_revision=state['peripherals']['revision'],**kw))
            if not c['working']:
                r=op('add',kind=c['kind']);new=next(i for i in r['items'] if i['station_serial'] is None and i['working'] and i['kind']==c['kind']);op('attach',item_id=new['id'])
            elif c['station_serial'] is None:op('attach',item_id=c['id'])
            else:
                op('connection',item_id=c['id'],value=True)
                if c['kind']=='monitor':op('power',item_id=c['id'],value=True);op('input',item_id=c['id'],value='HDMI')
    def test_all_nine_faults_start_failed_and_accept_actual_repair(self):
        original=copy.deepcopy(self.s)
        for cause in incidents.CAUSES:
            with self.subTest(cause=cause):
                self.s=copy.deepcopy(original);self.c.workspace.state=self.s;s=self.prepare(cause)
                self.assertFalse(all(r['status']=='valide' for r in desktop_incidents.checks(s,100)))
                self.assertTrue(s['remote_session'],'Local fault must not close remote session')
                public=desktop_incidents.public(s);self.assertNotIn('cause',public);self.assertNotIn('baseline',public)
                self.repair(s)
                self.assertTrue(all(r['status']=='valide' for r in desktop_incidents.checks(s,100)))
    def test_procedural_reproducibility(self):
        first=self.prepare();second=self.prepare();self.assertEqual(first['desktop_incident'],second['desktop_incident']);self.assertEqual(first['peripherals'],second['peripherals'])
    def test_collateral_changes_refuse_validation(self):
        s=self.prepare(('monitor','power'));self.repair(s)
        s['directory']['users'][s['directory_user_id']]['enabled']=False
        self.assertEqual(desktop_incidents.checks(s,100)[-1]['status'],'non satisfait')
    def test_local_ticket_closes_without_ping_and_does_not_accept_unrepaired(self):
        s=self.prepare(('mouse','connection'));self.c.workspace.state=s
        t=Tickets(None,Path(self.tmp.name)/'tickets-local.json');t.controller=self.c
        t.append_workspace_incident(s);ticket=t.state['tickets'][-1];self.c.observe=Mock()
        with self.assertRaises(ValueError):t.workspace_action(ticket,'close',{})
        self.c.observe.assert_not_called();self.assertFalse(ticket['complete'])
        self.repair(s);t.workspace_action(ticket,'close',{})
        self.assertEqual(ticket['status'],'clos');self.c.observe.assert_not_called()
    def test_diagnostic_caches_and_audits_do_not_count_as_damage(self):
        s=self.prepare(('keyboard','connection'));self.repair(s)
        s['directory']['audit'].append({'operation':'login'})
        s['directory']['revision']+=1
        s['directory']['users'][s['directory_user_id']]['failed_attempts']=1
        self.assertTrue(all(r['status']=='valide' for r in desktop_incidents.checks(s,100)))
    def test_creation_without_network_observation(self):
        self.s['observation']=None
        self.c.next_desktop_incident('peripherals',0)
        self.assertEqual(self.c.workspace.state['desktop_incident']['family'],'peripherals')
    def test_active_ticket_and_invalid_duration_refused(self):
        with self.assertRaises(ValueError):desktop_incidents.prepare(self.s,100,'peripherals',True)
        s=self.prepare()
        with self.assertRaises(ValueError):desktop_incidents.prepare(s,100,'peripherals',30)

del FilesIntegrationTests

import test_client_workspaces as multi
class PeripheralMultipleClientsTests(unittest.TestCase):
    setUp=multi.ClientWorkspacesTests.setUp
    proofs=multi.ClientWorkspacesTests.proofs
    def test_second_workstation_fault_persists_without_affecting_primary(self):
        self.c.peripherals('state',{'station_serial':'client'})
        before=copy.deepcopy([i for i in self.s['peripherals']['items'].values() if i['station_serial']=='client'])
        with patch.object(incidents.random,'Random') as rng:
            rng.return_value.choice.return_value=('monitor','power')
            self.c.next_desktop_incident('peripherals',15,client_serial='second')
        self.assertEqual(self.s['desktop_incident']['target_serial'],'second')
        self.assertEqual(before,[i for i in self.s['peripherals']['items'].values() if i['station_serial']=='client'])
        self.assertFalse(all(r['status']=='valide' for r in desktop_incidents.checks(self.s,100)))
        v=self.c.peripherals('state',{'station_serial':'second'});item=next(i for i in v['items'] if i['station_serial']=='second' and i['kind']=='monitor')
        self.c.peripherals('operation',dict(station_serial='second',operation='power',item_id=item['id'],value=True,expected_revision=v['revision']))
        self.assertTrue(all(r['status']=='valide' for r in desktop_incidents.checks(self.s,100)))
