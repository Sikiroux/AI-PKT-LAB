import copy
import tempfile
import time
import unittest
from unittest.mock import Mock
import directory_adapter as ad
import directory_incidents as incidents
import sim_ad
from workspace_model import generate, Workspace, evaluate
from workspace_app import Controller
from workspace_routes import WorkspaceRoutes
from tickets_app import Tickets

class DirectoryIncidentTests(unittest.TestCase):
    def setUp(self):
        self.now=time.time()
        self.s=generate('incident-001');self.s['environment_id']='env'
        self.s['devices']={k:dict(name=k,ip=ip,serial=k) for k,ip in [('client','192.168.1.2'),('server','192.168.1.10'),('technician','192.168.1.20')]}
        ad.ensure(self.s)
        self.s['observation']={'probes':{key:dict(at=self.now,status='passed',source_device=source,target=target) for key,source,target in [('remote','technician','192.168.1.2'),('share','client','192.168.1.10'),('directory','technician','192.168.1.10')]}}
    def cycle(self):
        s=self.s
        for _ in incidents.FAMILIES:
            s=incidents.prepare(s,self.now);yield s
            s['validated']=True
    def test_deterministic_and_non_mutating(self):
        before=copy.deepcopy(self.s)
        self.assertEqual(incidents.prepare(self.s,self.now),incidents.prepare(self.s,self.now))
        self.assertEqual(before,self.s)
    def test_cycle_contains_all_five_unique_families(self):
        states=list(self.cycle())
        self.assertEqual(set(incidents.FAMILIES),{s['directory_incident']['family'] for s in states})
        self.assertEqual(len({s['directory_incident']['id'] for s in states}),5)
    def test_initial_fault_is_effective_for_each_family(self):
        for s in self.cycle():
            u=s['directory']['users'][s['directory_user_id']];f=s['directory_incident']['family']
            if f=='account_disabled':self.assertFalse(u['enabled'])
            elif f=='account_locked':self.assertGreater(u['locked_until'],self.now)
            elif f=='password_expired':self.assertLess(u['password_expires_at'],self.now)
            else:
                action='read' if f=='read_group_missing' else 'write'
                for gid in s['directory_resource']['allowed_group_ids'][action]:self.assertNotIn(u['id'],s['directory']['groups'][gid]['member_user_ids'])
            self.assertIsNone(s['directory_auth']);self.assertFalse(s['remote_session']);self.assertFalse(s['validated'])
    def test_no_credentials_or_family_in_public_incident(self):
        s=incidents.prepare(self.s,self.now);public=incidents.public_incident(s)
        self.assertNotIn('family',public);self.assertNotIn('credential',str(public));self.assertNotIn('INJECTED',str(public))
    def test_unresolved_incident_blocks_next(self):
        s=incidents.prepare(self.s,self.now)
        with self.assertRaises(ValueError):incidents.prepare(s,self.now)
    def test_other_users_and_devices_are_preserved(self):
        before=copy.deepcopy(self.s);s=incidents.prepare(self.s,self.now)
        for uid,user in before['directory']['users'].items():
            if uid!=before['directory_user_id']:self.assertEqual(user,s['directory']['users'][uid])
        self.assertEqual(before['devices'],s['devices']);self.assertEqual(before['observation'],s['observation'])
    def test_controller_requires_fresh_technician_proof(self):
        with tempfile.TemporaryDirectory() as tmp:
            c=Controller(None,tmp);c.workspace.state=copy.deepcopy(self.s)
            c.workspace.state['observation']['probes']['directory']['at']=self.now-100
            before=copy.deepcopy(c.workspace.state)
            with self.assertRaises(ValueError):c.next_directory_incident()
            self.assertEqual(before,c.workspace.state)
            c.workspace.state=copy.deepcopy(self.s);c.on_change=Mock()
            result=c.next_directory_incident();self.assertIsNotNone(result['directory_incident']);c.on_change.assert_called_once()
    def test_write_goal_requires_read_and_write(self):
        s=next(s for s in self.cycle() if s['directory_incident']['family']=='write_group_missing')
        u=s['directory']['users'][s['directory_user_id']]
        s['directory_auth']={'user_id':u['id'],'status':'authenticated','environment_id':'env','source_device_id':'client','expires_at':self.now+100}
        self.assertTrue(evaluate(s,'read')['allowed']);self.assertFalse(evaluate(s,'write')['allowed'])
        with tempfile.TemporaryDirectory() as tmp:
            w=Workspace(tmp+'/session.json');w.state=s
            with self.assertRaises(ValueError):w.action('validate')
            for gid in s['directory_resource']['allowed_group_ids']['write']:s['directory']['groups'][gid]['member_user_ids'].append(u['id'])
            self.assertTrue(w.action('validate')['validated'])
    def test_route_rejects_wrong_environment(self):
        with tempfile.TemporaryDirectory() as tmp:
            c=Controller(None,tmp);c.workspace.state=self.s
            h=Mock();h.path='/workspace/directory-incident'
            with self.assertRaises(ValueError):WorkspaceRoutes(c,'token').post(h,{'environment_id':'other'})
    def test_persistence_retains_incident_but_not_authentication(self):
        with tempfile.TemporaryDirectory() as tmp:
            w=Workspace(tmp+'/session.json');w.state=incidents.prepare(self.s,self.now);w.save()
            loaded=Workspace(w.path)
            self.assertEqual(loaded.state['directory_incident'],w.state['directory_incident'])
            self.assertIsNone(loaded.state['directory_auth']);self.assertIsNone(loaded.state['observation'])
    def test_each_incident_can_be_repaired_through_ad_operations(self):
        for s in self.cycle():
            f=s['directory_incident']['family'];uid=s['directory_user_id'];d=s['directory']
            operations=[]
            if f=='account_disabled':operations=[('set_user_enabled',dict(user_id=uid,enabled=True))]
            elif f=='account_locked':operations=[('unlock_user',dict(user_id=uid))]
            elif f=='password_expired':
                outcome=sim_ad.change_password(d,d['users'][uid]['username'],sim_ad.TRAINING_PASSWORD,'Nouveau!2026',ad.context(s,now=self.now),self.now)
                self.assertTrue(outcome['result']['allowed']);s['directory']=outcome['directory']
            else:
                action='read' if f=='read_group_missing' else 'write'
                operations=[('add_group_member',dict(user_id=uid,group_id=gid)) for gid in s['directory_resource']['allowed_group_ids'][action]]
            for op,payload in operations:
                s['directory']=sim_ad.apply_operation(s['directory'],op,payload,ad.actor(s),self.now)['directory']
            password='Nouveau!2026' if f=='password_expired' else sim_ad.TRAINING_PASSWORD
            outcome=sim_ad.authenticate(s['directory'],s['directory']['users'][uid]['username'],password,ad.context(s,now=self.now),self.now)
            self.assertTrue(outcome['result']['allowed'],f);s['directory']=outcome['directory']
            s['directory_auth']=dict(user_id=uid,status='authenticated',environment_id='env',source_device_id='client',expires_at=self.now+100)
            self.assertTrue(evaluate(s,'read',self.now)['allowed'],f)
            self.assertTrue(evaluate(s,'write',self.now)['allowed'],f)
    def test_ticket_binding_and_closure_enforce_write_goal(self):
        s=next(s for s in self.cycle() if s['directory_incident']['family']=='write_group_missing')
        uid=s['directory_user_id']
        s['directory_auth']=dict(user_id=uid,status='authenticated',environment_id='env',source_device_id='client',expires_at=self.now+100)
        with tempfile.TemporaryDirectory() as tmp:
            s.update(network_file=tmp+'/network.pkt',expected_cable={'peer':'switch'})
            c=Mock();c.workspace=Workspace(tmp+'/session.json');c.workspace.state=s
            g=Mock();g.jobs.return_value=[]
            t=Tickets(Mock(),tmp+'/tickets.json');t.bind_environment(s,tmp,g,c)
            ident=s['directory_incident']['id']
            self.assertNotIn('family',str(t.public()['tickets']))
            with self.assertRaises(ValueError):t.action(ident,'close',{})
            self.assertFalse(s['validated'])
            for gid in s['directory_resource']['allowed_group_ids']['write']:s['directory']['groups'][gid]['member_user_ids'].append(uid)
            t.action(ident,'close',{});self.assertEqual(t.get(ident)['status'],'clos');self.assertTrue(s['validated'])
            t.bind_environment(s,tmp,g,c)
            self.assertEqual(len([x for x in t.state['tickets'] if x['id']==ident]),1)

if __name__=='__main__':unittest.main()
