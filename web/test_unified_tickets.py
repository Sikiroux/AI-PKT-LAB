import copy
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import Mock
from tickets_app import Tickets
from workspace_model import Workspace,generate
from service_desk import site_choices

class UnifiedTickets(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.t=Tickets(Mock(),Path(self.temp.name)/'legacy.json')
        self.g=Mock();self.g.jobs.return_value=[]
        self.controller=Mock()
        self.controller.workspace=Workspace(Path(self.temp.name)/'workspace.json')

    def state(self,seed):
        s=generate(seed);s['environment_id']=seed;s['network_file']=str(Path(self.temp.name)/seed/'network.pkt')
        s['devices']={role:dict(name=seed+'-'+role,serial=seed+'-'+role,ip=ip) for role,ip in [('client','172.20.1.21'),('technician','172.20.1.23'),('server','172.20.2.30')]}
        s['expected_cable']={'peer':seed+'-switch'}
        return s

    def bind(self,s):
        self.controller.workspace.state=s
        self.t.bind_environment(s,Path(self.temp.name)/s['environment_id'],self.g,self.controller)

    def test_tickets_are_isolated_and_resumed_with_same_file(self):
        a=self.state('a');b=self.state('b');self.bind(a)
        self.t.action('INC-1000','notes',{'notes':'Progression conservée'})
        self.t.desk.settings['active']=True
        self.bind(b)
        self.assertEqual(self.t.state['tickets'][0]['notes'],'')
        self.assertFalse(self.t.desk.settings['active'])
        self.bind(a)
        self.assertEqual(self.t.state['tickets'][0]['notes'],'Progression conservée')
        self.assertEqual(self.t.public()['site']['file'],a['network_file'])
        self.assertEqual(self.t.profile('switch'),'a-switch')
        self.assertEqual(self.t.profile('network'),'172.20.1.0/24')

    def test_closure_requires_fresh_network_and_read_permission(self):
        s=self.state('a');self.bind(s)
        with self.assertRaises(ValueError):self.t.action('INC-1000','close',{})
        s.update(read_allowed=True,observation={'at':time.time(),'status':'passed'})
        self.t.action('INC-1000','close',{})
        self.assertEqual(self.t.state['tickets'][0]['status'],'clos')
        self.controller.observe.assert_called_with(blocking=True)

    def test_inventory_checks_the_active_filename(self):
        s=self.state('a');self.bind(s)
        snapshot={'saved_filename':s['network_file'],'devices':[dict(d,ports=[],model='PC-PT') for d in s['devices'].values()]}
        self.t.engine.snapshot.return_value=snapshot
        self.t.sync_inventory()
        self.assertEqual(len(self.t.public()['site']['inventory']),3)
        wrong=copy.deepcopy(snapshot);wrong['saved_filename']='other.pkt'
        self.t.engine.snapshot.return_value=wrong
        with self.assertRaises(ValueError):self.t.sync_inventory()

    def test_no_wifi_demand_without_access_point(self):
        s=self.state('a');self.bind(s)
        with self.assertRaises(ValueError):self.t.new('wifi')
        snapshot={'devices':[dict(name='a-switch',ports=[dict(name='FastEthernet0/2',linked=False)])]}
        self.assertEqual(site_choices(snapshot,[], 'a-switch',None),[('pc',None)])

    def test_save_as_updates_both_tools_and_invalidates_connection(self):
        s=self.state('a');self.bind(s)
        new=Path(self.temp.name)/'renamed.pkt';new.write_bytes(b'fixture')
        self.t.engine.snapshot.return_value={'saved_filename':str(new),'devices':[dict(d,ports=[]) for d in s['devices'].values()]}
        self.t.attach(str(new))
        self.assertEqual(self.t.state['site']['file'],str(new))
        self.assertEqual(s['network_file'],str(new))
        self.assertIsNone(s['observation'])
        self.assertFalse(s['remote_session'])

    def test_reset_archives_tickets_before_recreating_initial_incident(self):
        s=self.state('a');self.bind(s)
        self.t.action('INC-1000','notes',{'notes':'Historique à conserver'})
        s['reset_id']='test-reset';self.bind(s)
        self.assertEqual(self.t.state['tickets'][0]['notes'],'')
        archived=Path(self.temp.name)/'a/tickets-before-reset-test-reset.json'
        self.assertIn('Historique à conserver',archived.read_text())
