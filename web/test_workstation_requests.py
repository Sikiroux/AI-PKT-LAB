import copy
import unittest
from unittest.mock import patch
import test_desktop_services as fixtures
import desktop_incidents as di
import desktop_services as ds
import workstation_requests as wr

class WorkstationRequestsTests(unittest.TestCase):
    setUp=fixtures.ControllerTests.setUp
    proofs=fixtures.ServicesTests.proofs
    login=fixtures.ServicesTests.login
    def prepare(self,profile):
        with patch.object(wr.random,'Random') as rng:
            rng.return_value.choice.side_effect=lambda values: profile if isinstance(values[0],str) else values[0]
            s=di.prepare(self.s,self.now,'workstation_setup',25)
        self.proofs(s);self.c.workspace.state=s;return s
    def configure(self,s):
        i=s['desktop_incident'];e=s['desktop_services']['endpoint']
        for app in i['required_apps']:ds.operation(s,'endpoint','set_application',dict(id=app,installed=True))
        e['mapped_drive']['path']='\\\\server\\Documents'
        ds.operation(s,'printing','set_default',dict(queue_id='office'))
    def finish(self,s):
        self.configure(s);i=s['desktop_incident']
        result=self.c.files('action',dict(request=dict(action='read',share_id=s['documents_share_id'],file_id=i['target_file_id'])))
        self.assertTrue(result['result']['allowed'],result)
        if 'print' in i['tasks']:self.assertTrue(self.c.desktop('printing/print',dict(name=i['print_name']))['result']['allowed'])
        if 'download' in i['tasks']:
            self.assertTrue(self.c.desktop('ftp/login',dict(payload=dict(username='depot',password='Formation!2026')))['result']['allowed'])
            self.assertTrue(self.c.desktop('ftp/download',dict(payload=dict(name=i['download'])))['result']['allowed'])
            self.assertTrue(self.c.desktop('ftp/upload',dict(payload=dict(name=i['upload'],content=i['content'],expected_revision=s['desktop_services']['ftp']['revision'])))['result']['allowed'])
    def test_each_profile_requires_real_actions_then_passes(self):
        for profile in wr.PROFILES:
            with self.subTest(profile=profile):
                s=self.prepare(profile);self.assertFalse(all(x['status']=='valide' for x in di.checks(s,self.now)))
                self.configure(s);self.assertFalse(all(x['status']=='valide' for x in di.checks(s,self.now)))
                self.finish(s);self.assertTrue(all(x['status']=='valide' for x in di.checks(s,self.now+2)),di.checks(s,self.now+2))
    def test_seed_reproducible_and_varied_without_mutation(self):
        before=copy.deepcopy(self.s);a=di.prepare(self.s,self.now,'workstation_setup');b=di.prepare(self.s,self.now,'workstation_setup')
        self.assertEqual(a,b);self.assertEqual(self.s,before)
        profiles=set()
        for index in range(30):
            s=copy.deepcopy(self.s);s['desktop_incident_count']=index;profiles.add(di.prepare(s,self.now,'workstation_setup')['desktop_incident']['profile'])
        self.assertEqual(profiles,set(wr.PROFILES))
    def test_copied_contents_without_transfer_do_not_complete(self):
        s=self.prepare('exchange');self.configure(s);i=s['desktop_incident'];self.login(s)
        s['desktop_services']['endpoint']['local_files'][i['download']]=i['baseline']['ftp_files'][i['download']]
        s['desktop_services']['ftp']['files'][i['upload']]=i['content']
        rows=di.checks(s,self.now);self.assertNotEqual(rows[3]['status'],'valide');self.assertNotEqual(rows[4]['status'],'valide')
    def test_failed_read_and_failed_transfer_do_not_record_evidence(self):
        s=self.prepare('exchange');self.configure(s);i=s['desktop_incident'];s['file_service']['service_status']='stopped'
        self.c.files('action',dict(request=dict(action='read',share_id=s['documents_share_id'],file_id=i['target_file_id'])))
        self.assertNotIn('read',i['evidence']);self.login(s);s['desktop_services']['ftp']['data_allowed']=False
        self.c.desktop('ftp/download',dict(payload=dict(name=i['download'])));self.assertNotIn('download',i['evidence'])
    def test_evidence_wrong_target_source_environment_or_time_rejected(self):
        s=self.prepare('documents');self.finish(s);i=s['desktop_incident']
        for key,value in [('target','other'),('source','technician'),('environment_id','other'),('at',self.now-1),('at',self.now+100)]:
            changed=copy.deepcopy(s);changed['desktop_incident']['evidence']['read'][key]=value
            self.assertNotEqual(di.checks(changed,self.now+2)[1]['status'],'valide')
        self.assertFalse(wr.record(s,'read','other',self.now));self.assertFalse(wr.record(s,'upload','other',self.now))
    def test_current_network_and_application_required_after_success(self):
        s=self.prepare('documents');self.finish(s)
        changed=copy.deepcopy(s);changed['observation']['probes']['share']['status']='failed';self.assertNotEqual(di.checks(changed,self.now+2)[1]['status'],'valide')
        changed=copy.deepcopy(s);changed['desktop_services']['endpoint']['applications'].remove('documents');self.assertNotEqual(di.checks(changed,self.now+2)[1]['status'],'valide')
    def test_unrelated_data_and_rights_must_be_preserved(self):
        s=self.prepare('documents');self.finish(s)
        for kind in ('device','file','account','rights','application'):
            changed=copy.deepcopy(s)
            if kind=='device':changed['devices']['server']['ip']='192.0.2.1'
            elif kind=='file':changed['desktop_services']['endpoint']['local_files']['Bienvenue.txt']='lost'
            elif kind=='account':changed['desktop_services']['ftp']['accounts']['depot']['write']=False
            elif kind=='application':changed['desktop_services']['endpoint']['applications'].remove('terminal')
            else:
                uid=next(iter(changed['desktop_incident']['baseline']['other_users']))
                for layer in ('share_acl','folder_acl'):changed['file_service']['shares'][changed['documents_share_id']][layer]['delete']['user_ids']=[uid]
            self.assertNotEqual(di.checks(changed,self.now+2)[-1]['status'],'valide',kind)
    def test_public_projection_dialogue_and_active_guard(self):
        s=self.prepare('office');self.assertNotIn('baseline',di.public(s));self.assertNotIn('evidence',di.public(s))
        self.assertIn('prépare',di.dialogue(s,s['desktop_incident']['id'],'when',self.now)['answer'])
        with self.assertRaises(ValueError):di.prepare(s,self.now,'workstation_setup')
    def test_local_limit_and_ftp_capacity_fail_without_mutation(self):
        for local in (True,False):
            s=copy.deepcopy(self.s)
            if local:s['desktop_services']['endpoint']['local_files']={str(n):'' for n in range(98)}
            else:s['desktop_services']['ftp']['capacity_bytes']=1
            before=copy.deepcopy(s)
            with patch.object(wr.random,'Random') as rng:
                rng.return_value.choice.return_value='exchange'
                with self.assertRaises(ValueError):di.prepare(s,self.now,'workstation_setup')
            self.assertEqual(s,before)

    def test_request_persists_and_reopened_session_requires_reauthentication(self):
        from workspace_model import Workspace
        s=self.prepare('exchange');self.finish(s);self.c.workspace.save()
        restored=Workspace(self.c.workspace.path).state
        self.assertEqual(restored['desktop_incident']['evidence'],s['desktop_incident']['evidence'])
        self.assertEqual(restored['desktop_incident']['baseline'],s['desktop_incident']['baseline'])
        self.assertFalse(restored['remote_session']);self.assertEqual(restored['desktop_services']['ftp']['sessions'],{})
        self.assertFalse(all(x['status']=='valide' for x in di.checks(restored,self.now+2)))
    def test_ticket_closure_checks_required_actions_and_keeps_duration(self):
        from pathlib import Path
        from tickets_app import Tickets
        from unittest.mock import Mock
        s=self.prepare('office');controller=Mock();controller.workspace=self.c.workspace
        controller.workspace.public=Mock(return_value={'checks':{'read':{'allowed':False}}})
        tickets=Tickets(Mock(),Path(self.tmp.name)/'tickets.json');tickets.controller=controller;tickets.public=Mock(return_value={})
        tickets.append_workspace_incident(s);ticket=tickets.state['tickets'][-1]
        self.assertEqual(ticket['name'],'client');self.assertEqual(ticket['workspace_goal'],'workstation_setup')
        with self.assertRaises(ValueError):tickets.workspace_action(ticket,'close',{})
        self.finish(s);tickets.workspace_action(ticket,'close',{})
        self.assertEqual(ticket['status'],'clos');self.assertTrue(s['validated'])
    def test_controller_generation_notifies_tickets_and_preserves_timer(self):
        from unittest.mock import Mock
        self.c.on_change=Mock();result=self.c.next_desktop_incident('workstation_setup',17)
        self.assertEqual(result['desktop_incident']['goal'],'workstation_setup')
        self.assertEqual(self.c.workspace.state['desktop_incident']['timer_minutes'],17)
        self.c.on_change.assert_called_once()

if __name__=='__main__':unittest.main()
