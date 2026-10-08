import copy
import time
import tempfile
from pathlib import Path
from unittest.mock import Mock
from tickets_app import Tickets
import unittest
from workspace_model import generate
import directory_adapter as ad
import files_adapter as fa
import dns_adapter as da
import desktop_services as ds
import desktop_incidents as di
import deployment_incidents as dep
import sim_deployment as sim

class DeploymentIncidents(unittest.TestCase):
    def setUp(self):
        self.now=time.time();self.s=generate('deployment-ticket');self.s['environment_id']='env'
        self.s['devices']={k:dict(name=k,ip=ip,serial=k) for k,ip in [('client','192.168.50.2'),('server','192.168.50.10'),('technician','192.168.50.20')]}
        ad.ensure(self.s);fa.ensure(self.s);da.ensure(self.s);ds.ensure(self.s)
    def prepared(self):return di.prepare(self.s,self.now,'deployment',30)
    def finish(self,s):
        d=s['desktop_services']['deployment']
        def act(a,**p):
            nonlocal d
            d=sim.apply(d,a,p,d['revision'])
        act('start');act('mount',image_id=d['requirements']['image_id']);act('boot',source='usb');act('setup');act('load_driver');act('backup')
        for ident in ('old-os','old-data'):act('delete_partition',partition_id=ident)
        act('partition',size_gib=100);act('install',partition_id='windows')
        for _ in range(3):act('advance')
        act('eject');act('restart');act('configure',**{k:d['requirements'][k] for k in ('locale','keyboard','account')});s['desktop_services']['deployment']=d
    def test_no_free_validation(self):self.assertEqual(dep.checks(self.prepared())[0]['status'],'non satisfait')
    def test_finish(self):
        s=self.prepared();self.finish(s);self.assertTrue(all(r['status']=='valide' for r in di.checks(s,self.now)))
    def test_preserved(self):
        s=self.prepared();self.assertEqual(dep.baseline(s),dep.baseline(self.s));self.assertEqual(s['devices'],self.s['devices'])
    def test_unauthorised_changes_fail(self):
        s=self.prepared();self.finish(s);s['devices']['client']['ip']='other';self.assertEqual(dep.checks(s)[1]['status'],'non satisfait')
    def test_reproducible_and_varied(self):
        a=self.prepared();b=self.prepared();self.assertEqual(a,b);a['validated']=True;next_s=di.prepare(a,self.now,'deployment');self.assertNotEqual(a['desktop_incident']['station'],next_s['desktop_incident']['station'])
    def test_active_guard(self):
        with self.assertRaises(ValueError):di.prepare(self.prepared(),self.now,'deployment')
    def test_revision_monotonic(self):
        self.s['desktop_services']['deployment']=sim.generate('old','env');self.s['desktop_services']['deployment']['revision']=25
        s=self.prepared();self.assertEqual(s['desktop_services']['deployment']['revision'],26)
    def test_dialogue_state(self):
        s=self.prepared();ident=s['desktop_incident']['id'];before=di.dialogue(s,ident,'retest',self.now)['answer'];self.finish(s);after=di.dialogue(s,ident,'retest',self.now)['answer'];self.assertNotEqual(before,after)
    def test_wrong_image_fails(self):
        s=self.prepared();self.finish(s);s['desktop_services']['deployment']['image_id']='home';self.assertEqual(dep.checks(s)[0]['status'],'non satisfait')
    def test_target_station_check(self):
        s=self.prepared();self.finish(s);s['desktop_services']['deployment']['station']='other';self.assertEqual(dep.checks(s)[0]['status'],'non satisfait')
    def test_duration_invalid(self):
        with self.assertRaises(ValueError):di.prepare(self.s,self.now,'deployment',-1)
    def test_ticket_target_and_closure(self):
        s=self.prepared()
        with tempfile.TemporaryDirectory() as folder:
            t=Tickets(Mock(),Path(folder)/'tickets.json');t.controller=Mock();t.controller.workspace.state=s;t.controller.workspace.public.return_value={'checks':{'read':{'allowed':False}}};t.public=Mock(return_value={})
            t.append_workspace_incident(s);ticket=t.state['tickets'][0];self.assertEqual(ticket['name'],s['desktop_incident']['station'])
            with self.assertRaises(ValueError):t.action(ticket['id'],'close',{})
            self.assertFalse(ticket['complete']);self.finish(s);t.action(ticket['id'],'close',{});self.assertEqual(ticket['status'],'clos');self.assertTrue(s['validated'])
    def test_input_unchanged(self):
        old=copy.deepcopy(self.s);self.prepared();self.assertEqual(old,self.s)

if __name__=='__main__':unittest.main()
