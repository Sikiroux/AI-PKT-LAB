import copy
import json
import tempfile
import threading
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock,patch
import sim_ad
import sim_corporate as sim
import sim_inventory
import company_registry
import desktop_controller
import test_sim_deployment
from tickets_app import Tickets

class CorporateTests(unittest.TestCase):
    def setUp(self):
        devices={'client':dict(name='PC-CPT-01',serial='pc',ip='10.0.0.2')}
        directory=sim_ad.generate_directory('corp','env',[dict(id='pc',name='PC-CPT-01',role='client')],dict(id='client-user',username='client',display_name='Client',device_id='pc'),100)
        self.s=dict(seed='corp',company='Entreprise Démo',environment_id='env',directory=directory,devices=devices,directory_user_id=directory['bindings']['requester_user_id'] if 'bindings' in directory else next(iter(directory['users'])),requester='Client')
        for u in directory['users'].values():u.update(enabled=True,must_change_password=False,locked_until=None,password_expires_at=10000)
        sim.ensure(self.s);company_registry.ensure(self.s);sim_inventory.ensure(self.s)
    def act(self,operation,**payload):self.s,self.result=sim.operate(self.s,operation,payload,self.s['corporate']['revision'],200);return self.result
    def request(self):
        self.act('create-request',display_name='Alex Nouveau',username='alex.nouveau',department='Comptabilité',manager='Chef Compta',start_date='2026-10-12',group_ids=[next(iter(self.s['directory']['groups']))])
        return self.result['request_id']
    def add_user(self):
        actor=dict(environment_id='env',permissions=[sim_ad.CAPABILITY_USERS,sim_ad.CAPABILITY_GROUPS])
        out=sim_ad.apply_operation(self.s['directory'],'create_user',dict(username='alex.nouveau',display_name='Alex Nouveau',ou_id=next(iter(self.s['directory']['ous'])),must_change_password=False),actor,200)
        self.s['directory']=out['directory'];return out['result']['user_id']
    def test_policy_seed_and_saved_policy(self):
        p=sim.policy(self.s);self.assertEqual(p,sim.policy(copy.deepcopy(self.s)));self.assertTrue(p['domain'].endswith('.example'))
        self.s['corporate']['policy']['notice_days']=99;self.assertFalse(sim.ensure(self.s));self.assertEqual(self.s['corporate']['policy']['notice_days'],99)
    def test_cross_environment_rejected(self):
        self.s['corporate']['environment_id']='other'
        with self.assertRaises(ValueError):sim.ensure(self.s)
    def test_no_secrets_and_read_only_projection(self):
        before=copy.deepcopy(self.s);text=json.dumps(sim.public(self.s));self.assertNotIn('credential',text);self.assertNotIn('Formation!',text);self.assertEqual(before,self.s)
    def test_stale_boolean_revision_atomic(self):
        for rev in (True,1,None):
            before=copy.deepcopy(self.s)
            with self.assertRaises(ValueError):sim.operate(self.s,'set-mail-service',{'enabled':False},rev,200)
            self.assertEqual(before,self.s)
    def test_license_capacity_and_no_partial_allocation(self):
        license=self.s['corporate']['licenses']['mail'];license['capacity']=len(license['assigned']);uid=self.add_user();before=copy.deepcopy(self.s)
        with self.assertRaises(ValueError):self.act('assign-license',license_id='mail',user_id=uid)
        self.assertEqual(before,self.s)
    def test_license_idempotent_and_removal(self):
        uid=next(iter(self.s['directory']['users']));before=len(self.s['corporate']['licenses']['mail']['assigned']);self.act('assign-license',license_id='mail',user_id=uid);self.assertEqual(before,len(self.s['corporate']['licenses']['mail']['assigned']));self.act('remove-license',license_id='mail',user_id=uid);self.assertNotIn(uid,self.s['corporate']['licenses']['mail']['assigned'])
    def test_capacity_cannot_shrink_below_assigned(self):
        with self.assertRaises(ValueError):self.act('license-capacity',license_id='mail',capacity=0)
        with self.assertRaises(ValueError):self.act('license-capacity',license_id='mail',capacity=True)
    def test_send_delivery_and_copy_on_write(self):
        uid=next(iter(self.s['directory']['users']));before=copy.deepcopy(self.s)
        new,_=sim.operate(self.s,'send',dict(mailbox_id='company-welcome',recipient=self.s['corporate']['mailboxes'][uid]['address'],subject='Bienvenue',body='Message de test'),0,200)
        self.assertEqual(self.s,before);self.assertEqual(new['corporate']['mailboxes'][uid]['messages'][0]['direction'],'inbox');self.assertEqual(new['corporate']['mailboxes']['company-welcome']['messages'][0]['direction'],'sent')
    def test_unavailable_mail_account_license_and_service(self):
        uid=next(iter(self.s['directory']['users']));p=dict(mailbox_id=uid,recipient=self.s['corporate']['mailboxes']['company-welcome']['address'],subject='Test',body='Test')
        cases=[lambda s:s['corporate'].update(mail_running=False),lambda s:s['corporate']['mailboxes'][uid].update(enabled=False),lambda s:s['directory']['users'][uid].update(enabled=False),lambda s:s['directory']['users'][uid].update(locked_until=201),lambda s:s['directory']['users'][uid].update(password_expires_at=100),lambda s:s['corporate']['licenses']['mail']['assigned'].remove(uid)]
        for break_it in cases:
            broken=copy.deepcopy(self.s);break_it(broken);before=copy.deepcopy(broken)
            with self.assertRaises(ValueError):sim.operate(broken,'send',p,0,200)
            self.assertEqual(before,broken)
    def test_full_destination_blocks_sender_and_recipient(self):
        uid=next(iter(self.s['directory']['users']));self.s['corporate']['mailboxes'][uid]['quota_bytes']=1;before=copy.deepcopy(self.s)
        with self.assertRaises(ValueError):self.act('send',mailbox_id='company-welcome',recipient=self.s['corporate']['mailboxes'][uid]['address'],subject='Test',body='Corps')
        self.assertEqual(before,self.s)
    def test_unknown_recipient_and_duplicate_mailbox(self):
        with self.assertRaises(ValueError):self.act('send',mailbox_id='company-welcome',recipient='inexistant@example.com',subject='Test',body='Test')
        with self.assertRaises(ValueError):self.act('create-mailbox',user_id=next(iter(self.s['directory']['users'])))
    def test_new_mailbox_address_from_account(self):
        uid=self.add_user();self.act('create-mailbox',user_id=uid);self.assertEqual(self.s['corporate']['mailboxes'][uid]['address'],'alex.nouveau@'+self.s['corporate']['policy']['domain'])
    def test_request_baseline_and_administrative_identity(self):
        ident=self.request();self.assertFalse(sim.evaluate(self.s,ident,200)['passed']);uid=self.add_user();company_registry.ensure(self.s);r=self.s['corporate']['requests'][ident];p=self.s['company_registry']['people'][r['employee_id']];self.assertFalse(p['represented']);self.assertTrue(p['account_present']);self.assertEqual(p['account_id'],uid)
    def test_request_duplicate_and_invalid_date_atomic(self):
        self.request();before=copy.deepcopy(self.s)
        for username,date in [('alex.nouveau','2026-10-12'),('autre.nom','2026-02-31')]:
            with self.assertRaises(ValueError):self.act('create-request',display_name='Alex Nouveau',username=username,department='Compta',manager='Chef Compta',start_date=date)
            self.assertEqual(before,self.s)
    def complete(self):
        ident=self.request();uid=self.add_user();r=self.s['corporate']['requests'][ident]
        for gid in r['group_ids']:self.s['directory']['groups'][gid]['member_user_ids'].append(uid)
        for key in r['license_ids']:self.act('assign-license',license_id=key,user_id=uid)
        self.act('create-mailbox',user_id=uid);box=self.s['corporate']['mailboxes'][uid]
        self.act('send',mailbox_id='company-welcome',recipient=box['address'],subject='Bienvenue',body=r['welcome_document'])
        self.act('send',mailbox_id=uid,recipient=self.s['corporate']['mailboxes']['company-welcome']['address'],subject='Test',body='Message reçu')
        d=test_sim_deployment.DeploymentTests();d.setUp();d.disk();d.partition();d.finish();self.s['inventory']['items']['reserve-laptop']['deployment']=d.s
        company_registry.ensure(self.s)
        sim_inventory.operate(self.s,dict(expected_revision=0,item_id='reserve-laptop',employee_id=r['employee_id'],operation='assign'),200)
        return ident,uid
    def test_complete_onboarding_uses_real_motors(self):
        ident,uid=self.complete();self.assertTrue(sim.evaluate(self.s,ident,200)['passed'])
        self.act('remove-license',license_id='mail',user_id=uid);self.assertFalse(sim.evaluate(self.s,ident,200)['passed'])
    def test_returned_equipment_and_changed_letter_invalidate(self):
        ident,uid=self.complete();self.act('welcome-document',request_id=ident,body='Nouvelle lettre qui n’a pas été livrée.');self.assertFalse(sim.evaluate(self.s,ident,200)['passed'])
    def test_json_roundtrip_preserves_requests_messages_evaluation(self):
        ident,uid=self.complete();restored=json.loads(json.dumps(self.s));self.assertEqual(sim.evaluate(self.s,ident,200),sim.evaluate(restored,ident,200));self.assertFalse(sim.ensure(restored))
    def test_ticket_bridge_idempotent_and_resolution_rechecks(self):
        ident,uid=self.complete()
        with tempfile.TemporaryDirectory() as folder:
            engine=Mock();t=Tickets(engine,Path(folder)/'tickets.json');t.append_arrivals(self.s);t.append_arrivals(self.s);self.assertEqual(len(t.state['tickets']),1)
            t.controller=SimpleNamespace(lock=threading.RLock(),workspace=SimpleNamespace(state=self.s));ticket=t.state['tickets'][0];ticket['notes']='Préparation et remise administrative du portable vérifiées.'
            with patch('desktop_controller.admin'),patch('tickets_app.time.time',return_value=200):
                t.action(ident,'resolve',{});self.assertEqual(ticket['status'],'resolu');rid=ticket['resolution']['id']
                self.act('remove-license',license_id='office',user_id=uid)
                t.controller.workspace.state=self.s
                with self.assertRaises(ValueError):t.action(ident,'close',dict(confirmation=True,resolution_id=rid))
                self.assertEqual(ticket['status'],'resolu')
            engine.snapshot.assert_not_called();engine.ping.assert_not_called()
    def test_adapter_read_scope_and_stale_refusal(self):
        self.s['desktop_services']={}
        workspace=SimpleNamespace(state=self.s,save=Mock(),event=Mock(),path=Path('/tmp/session.json'));c=SimpleNamespace(lock=threading.RLock(),workspace=workspace,on_change=None)
        with patch('desktop_controller.admin'),patch('tickets_app.time.time',return_value=200):
            self.assertIn('mailboxes',desktop_controller.handle(c,'corporate/state',{}))
            with self.assertRaises(ValueError):desktop_controller.handle(c,'corporate/operation',dict(operation='set-mail-service',payload={'enabled':False},expected_revision=True))
            with self.assertRaises(ValueError):desktop_controller.handle(c,'corporate/state',{'client_serial':'pc'})
            self.s['_client_view']=True
            with self.assertRaises(ValueError):desktop_controller.handle(c,'corporate/state',{})
        workspace.event.assert_not_called()

    def test_first_connection_delegates_password_rules_and_clears_initial_requirement(self):
        self.request();uid=self.add_user();self.s['directory']['users'][uid]['must_change_password']=True;self.s['desktop_services']={}
        workspace=SimpleNamespace(state=self.s,save=Mock(),event=Mock(),path=Path('/tmp/session.json'));c=SimpleNamespace(lock=threading.RLock(),workspace=workspace,on_change=None)
        ctx=dict(environment_id='env',network=dict(status='passed',observed_at=190,valid_until=250),directory_service='running')
        with patch('desktop_controller.admin'),patch('desktop_controller.ad.context',return_value=ctx),patch('desktop_controller.time.time',return_value=200):
            result=desktop_controller.handle(c,'corporate/operation',dict(operation='first-login',expected_revision=self.s['corporate']['revision'],payload=dict(username='alex.nouveau',old_password=sim_ad.TRAINING_PASSWORD,new_password='Nouveau!2026')))
        self.assertEqual(result['result']['code'],'OK');self.assertFalse(self.s['directory']['users'][uid]['must_change_password']);self.assertNotIn('Nouveau!',str(workspace.event.call_args))
    def test_malformed_group_and_unknown_operation_preserve_state(self):
        before=copy.deepcopy(self.s)
        with self.assertRaises(ValueError):self.act('create-request',display_name='Alex Nouveau',username='alex.nouveau',department='Compta',manager='Chef Compta',start_date='2026-10-12',group_ids=[{}])
        with self.assertRaises(ValueError):self.act('unknown')
        self.assertEqual(before,self.s)
    def test_documentation_policies_do_not_expose_mail_content(self):
        import company_documents
        self.s['corporate']['mailboxes']['company-welcome']['messages'].append(dict(body='PRIVATE-MAIL',subject='PRIVATE-SUBJECT'))
        docs=company_documents.public(self.s);self.assertIn('company-onboarding',[d['id'] for d in docs]);self.assertNotIn('PRIVATE-',str(docs));self.assertIn(self.s['corporate']['policy']['domain'],str(docs))

    def test_mail_inspection_state_from_motor(self):
        import desktop_services
        self.s['corporate']['mail_running']=False
        services=desktop_services.inspection(self.s)['services']
        self.assertEqual(next(x for x in services if x['id']=='mail')['status'],'stopped')

    def test_foreign_material_never_satisfies_onboarding(self):
        ident,uid=self.complete();self.s['inventory']['items']['reserve-laptop']['deployment']['environment_id']='other'
        self.assertFalse(sim.evaluate(self.s,ident,200)['passed'])
