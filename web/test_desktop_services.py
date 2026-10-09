import copy
import tempfile
import time
import threading
import unittest
from unittest.mock import Mock, patch
from workspace_model import generate, Workspace
from workspace_app import Controller
from workspace_routes import WorkspaceRoutes
import directory_adapter as ad
import files_adapter as fa
import dns_adapter as da
import desktop_services as ds
import desktop_incidents as di
import directory_incidents
import file_incidents
import dns_incidents
import mixed_incidents

class ServicesTests(unittest.TestCase):
    def setUp(self):
        self.now=time.time();self.s=generate('desktop-seed');self.s['environment_id']='env'
        self.s['devices']={k:dict(name=k,ip=ip,serial=k) for k,ip in [('client','192.168.50.2'),('server','192.168.50.10'),('technician','192.168.50.20'),('printer','192.168.50.40')]}
        ad.ensure(self.s);fa.ensure(self.s);da.ensure(self.s);ds.ensure(self.s);self.proofs(self.s)
    def proofs(self,s):
        s['remote_session']=True;s['directory_auth']=dict(user_id=s['directory_user_id'],status='authenticated',environment_id='env',source_device_id='client',expires_at=self.now+1000)
        s['observation']={'probes':{k:dict(at=self.now,status='passed',source_device=s['devices'][src]['name'],target=s['devices'][dst]['ip']) for k,src,dst in [('remote','technician','client'),('share','client','server'),('directory','technician','server'),('printing','client','printer')]}}
    def login(self,s):
        return ds.ftp_action(s,'login',dict(username='depot',password='Formation!2026'),'client',self.now)
    def planned(self,family,cause):
        with patch.object(di.random,'Random') as rng:
            rng.return_value.choice.return_value=cause
            s=di.prepare(self.s,self.now,family)
        self.proofs(s);return s
    def repair(self,s):
        d=s['desktop_services'];e=d['endpoint'];p=d['printing'];f=d['ftp']
        e['applications']=list(ds.APPS);e['mapped_drive']['path']='\\\\server\\Documents'
        p['spooler_running']=True;p['default_queue']='office';p['queues']['office'].update(port_ip=s['devices']['printer']['ip'],driver_valid=True,paused=False,use_offline=False);p['printer'].update(enabled=True,paper_pages=50)
        f.update(service_running=True,control_allowed=True,data_allowed=True,capacity_bytes=1048576);f['accounts']['depot'].update(enabled=True,read=True,write=True,password_hash=ds.password_hash('Formation!2026'))
    def finish(self,s):
        i=s['desktop_incident'];self.repair(s)
        if i['goal']=='print':ds.print_job(s,i['document'],'office',self.now)
        elif i['goal'] in ('upload','download','install'):
            self.assertTrue(self.login(s)['allowed'])
            if i['goal']=='upload':ds.ftp_action(s,'upload',dict(name=i['upload'],content=i['content'],expected_revision=s['desktop_services']['ftp']['revision']),'client',self.now)
            elif i['goal']=='download':ds.ftp_action(s,'download',dict(name=i['download']),'client',self.now)
        return di.checks(s,self.now)
    def test_all_eighteen_causes_require_intervention(self):
        for family,causes in di.FAMILIES.items():
            for cause in causes:
                with self.subTest(family=family,cause=cause):
                    s=self.planned(family,cause)
                    self.assertFalse(all(r['status']=='valide' for r in di.checks(s,self.now)))
                    self.assertTrue(all(r['status']=='valide' for r in self.finish(s)),di.checks(s,self.now))
    def test_seed_reproducibility_and_variation(self):
        plans=[di.prepare(self.s,self.now,target='random')['desktop_incident'] for _ in range(2)]
        self.assertEqual(plans[0],plans[1]);seen=set()
        for index in range(45):
            s=copy.deepcopy(self.s);s['desktop_incident_count']=index;seen.add(di.prepare(s,self.now)['desktop_incident']['cause'])
        self.assertGreater(len(seen),12)
    def test_original_not_mutated_and_no_private_causes(self):
        before=copy.deepcopy(self.s);s=self.planned('printing','wrong_port');self.assertEqual(self.s,before)
        public=di.public(s);self.assertNotIn('cause',public);self.assertNotIn('baseline',public);self.assertNotIn('wrong_port',public['description'])
    def test_new_incident_clears_validated_and_blocks_other_generators(self):
        self.s['validated']=True;s=self.planned('ftp','data_blocked');self.assertFalse(s['validated'])
        for fn in (di.prepare,directory_incidents.prepare,file_incidents.prepare,dns_incidents.prepare,mixed_incidents.prepare):
            with self.assertRaises(ValueError):fn(s,self.now)
    def test_completed_incident_removed_by_dns_generator(self):
        s=self.planned('printing','spooler_stopped');self.finish(s);s['validated']=True
        self.assertNotIn('desktop_incident',dns_incidents.prepare(s,self.now))
    def test_invalid_duration_and_target(self):
        for value in (True,-1,1441,'30'):
            with self.assertRaises(ValueError):di.prepare(self.s,self.now,'printing',value)
        with self.assertRaises(ValueError):di.prepare(self.s,self.now,'bad')
    def test_queued_is_not_printed_and_repair_resumes_queue(self):
        p=self.s['desktop_services']['printing'];p['queues']['office']['paused']=True
        r=ds.print_job(self.s,'Bienvenue.txt','office',self.now);self.assertEqual(r['code'],'QUEUED');self.assertEqual(r['job']['status'],'blocked')
        ds.operation(self.s,'printing','set_paused',dict(value=False));ds.process_jobs(self.s,self.now)
        self.assertEqual(p['jobs'][0]['status'],'printed');self.assertEqual(p['printer']['paper_pages'],49)
        ds.process_jobs(self.s,self.now);self.assertEqual(p['printer']['paper_pages'],49)
    def test_restart_does_not_fix_wrong_driver(self):
        p=self.s['desktop_services']['printing'];p['queues']['office']['driver_valid']=False
        ds.operation(self.s,'printing','restart_spooler',{})
        self.assertEqual(ds.evaluate_print(self.s,'office',self.now)['code'],'DRIVER_INVALID')
    def test_unknown_and_failed_printer_network(self):
        probe=self.s['observation']['probes']['printing'];probe['at']=self.now-46
        self.assertEqual(ds.evaluate_print(self.s,'office',self.now)['status'],'unknown')
        probe.update(at=self.now,status='failed');self.assertEqual(ds.evaluate_print(self.s,'office',self.now)['code'],'NETWORK_DOWN')
    def test_wrong_source_or_destination_proof_rejected(self):
        for key,value in [('source_device','technician'),('target','192.168.99.40')]:
            s=copy.deepcopy(self.s);s['observation']['probes']['printing'][key]=value
            self.assertFalse(ds.evaluate_print(s,'office',self.now)['allowed'])
    def test_pdf_does_not_complete_physical_print_ticket(self):
        s=self.planned('printing','wrong_default');i=s['desktop_incident']
        r=ds.print_job(s,i['document'],None,self.now);self.assertEqual(r['job']['queue_id'],'pdf')
        self.assertNotEqual(di.checks(s,self.now)[0]['status'],'valide')
        ds.operation(s,'printing','set_default',dict(queue_id='office'));ds.print_job(s,i['document'],None,self.now)
        self.assertEqual(di.checks(s,self.now)[0]['status'],'valide')
    def test_paper_consumed_per_job_then_queue_waits(self):
        p=self.s['desktop_services']['printing'];p['printer']['paper_pages']=1
        ds.print_job(self.s,'Bienvenue.txt',now=self.now);r=ds.print_job(self.s,'Bienvenue.txt',now=self.now)
        self.assertEqual(r['job']['status'],'blocked');self.assertEqual(p['printer']['paper_pages'],0)
        ds.operation(self.s,'printing','add_paper',dict(pages=2));ds.process_jobs(self.s,self.now);self.assertEqual(p['printer']['paper_pages'],1)
    def test_cancel_and_printed_cannot_be_cancelled(self):
        p=self.s['desktop_services']['printing'];p['queues']['office']['paused']=True;r=ds.print_job(self.s,'Bienvenue.txt',now=self.now)
        ds.operation(self.s,'printing','cancel_job',dict(id=r['job']['id']));self.assertEqual(p['jobs'][0]['status'],'cancelled')
        p['queues']['office']['paused']=False;r=ds.print_job(self.s,'Bienvenue.txt',now=self.now)
        with self.assertRaises(ValueError):ds.operation(self.s,'printing','cancel_job',dict(id=r['job']['id']))
    def test_queue_unknown_rejected(self):
        with self.assertRaises(ValueError):ds.print_job(self.s,'Bienvenue.txt','bad',self.now)
    def test_spooler_stopped_does_not_accept_job(self):
        self.s['desktop_services']['printing']['spooler_running']=False
        self.assertFalse(ds.print_job(self.s,'Bienvenue.txt',now=self.now)['allowed'])
        self.assertEqual(self.s['desktop_services']['printing']['jobs'],[])
    def test_ftp_control_and_data_separate(self):
        self.s['desktop_services']['ftp']['data_allowed']=False;self.assertTrue(self.login(self.s)['allowed'])
        self.assertEqual(ds.ftp_action(self.s,'download',dict(name='Notice.txt'),'client',self.now)['code'],'FTP_DATA_BLOCKED')
    def test_login_alone_does_not_finish_download(self):
        s=self.planned('ftp','service_stopped');self.repair(s);self.login(s)
        self.assertNotEqual(di.checks(s,self.now)[0]['status'],'valide')
    def test_login_bad_password_invalidates_old_session(self):
        self.login(self.s);r=ds.ftp_action(self.s,'login',dict(username='depot',password='bad'),'client',self.now)
        self.assertFalse(r['allowed']);self.assertNotIn('client',self.s['desktop_services']['ftp']['sessions'])
    def test_expired_or_foreign_ftp_session_denied(self):
        self.login(self.s);session=self.s['desktop_services']['ftp']['sessions']['client']
        for key,value in [('environment_id','other'),('source_device','other'),('expires_at',self.now-1)]:
            s=copy.deepcopy(self.s);s['desktop_services']['ftp']['sessions']['client'][key]=value
            self.assertFalse(ds.ftp_check(s,'download','client',self.now)['allowed'])
    def test_service_configuration_invalidates_sessions(self):
        self.login(self.s);ds.operation(self.s,'ftp','set_account',dict(username='depot',field='write',value=False))
        self.assertEqual(self.s['desktop_services']['ftp']['sessions'],{})
    def test_unknown_ftp_proof_does_not_transfer(self):
        self.login(self.s);self.s['observation']['probes']['share']['at']=self.now-46
        self.assertEqual(ds.ftp_action(self.s,'download',dict(name='Notice.txt'),'client',self.now)['status'],'unknown')
    def test_capacity_and_revision_fail_atomically(self):
        self.login(self.s);f=self.s['desktop_services']['ftp'];before=copy.deepcopy(f);f['capacity_bytes']=1
        r=ds.ftp_action(self.s,'upload',dict(name='Rapport.txt',content='abc',expected_revision=f['revision']),'client',self.now)
        self.assertEqual(r['code'],'552_CAPACITY_EXCEEDED');self.assertEqual(f['files'],before['files']);self.assertEqual(f['revision'],before['revision'])
        r=ds.ftp_action(self.s,'upload',dict(name='Rapport.txt',content='abc',expected_revision=-1),'client',self.now)
        self.assertEqual(r['code'],'REVISION_CONFLICT')
    def test_replacement_counts_net_size(self):
        self.login(self.s);f=self.s['desktop_services']['ftp'];f['files']={'large.txt':'12345'};f['capacity_bytes']=5
        r=ds.ftp_action(self.s,'upload',dict(name='large.txt',content='12',expected_revision=f['revision']),'client',self.now)
        self.assertTrue(r['allowed']);self.assertEqual(f['files']['large.txt'],'12')
    def test_local_storage_limit_and_simple_names(self):
        self.login(self.s);self.s['desktop_services']['endpoint']['local_files']={str(n):'' for n in range(100)}
        self.assertEqual(ds.ftp_action(self.s,'download',dict(name='Notice.txt'),'client',self.now)['code'],'LOCAL_STORAGE_FULL')
        for name in ('../bad','a/b','a\\b','bad\n',''):
            with self.assertRaises(ValueError):ds.file_name(name)
    def test_public_projection_removes_credentials_sessions_content(self):
        self.login(self.s);ds.print_job(self.s,'Bienvenue.txt',now=self.now);d=ds.public(self.s)
        self.assertNotIn('sessions',d['ftp']);self.assertNotIn('password_hash',d['ftp']['accounts']['depot']);self.assertNotIn('content',d['printing']['jobs'][0])
    def test_app_installation_not_completed_until_ftp_connection(self):
        s=self.planned('endpoint','install_ftp');ds.operation(s,'endpoint','set_application',dict(id='ftp',installed=True))
        self.assertNotEqual(di.checks(s,self.now)[0]['status'],'valide');self.login(s);self.assertEqual(di.checks(s,self.now)[0]['status'],'valide')
    def test_essential_apps_protected(self):
        for ident in ('settings','login','terminal'):
            with self.assertRaises(ValueError):ds.operation(self.s,'endpoint','set_application',dict(id=ident,installed=False))
    def test_drive_and_documents_app_gate_access(self):
        s=self.planned('endpoint','mapped_drive_wrong');self.assertFalse(fa.access(s,'read',self.now)['allowed']);self.repair(s);self.assertTrue(fa.access(s,'read',self.now)['allowed'])
        s['desktop_services']['endpoint']['applications'].remove('documents');self.assertEqual(fa.access(s,'read',self.now)['code'],'APPLICATION_MISSING')
    def test_collateral_local_ftp_shared_files_and_users_detected(self):
        s=self.planned('printing','spooler_stopped');self.finish(s)
        for kind in ('local','ftp','shared','user'):
            changed=copy.deepcopy(s)
            if kind=='local':changed['desktop_services']['endpoint']['local_files']['Bienvenue.txt']='lost'
            elif kind=='ftp':changed['desktop_services']['ftp']['files']['Notice.txt']='lost'
            elif kind=='shared':next(iter(changed['file_service']['files'].values()))['content']='lost'
            else:next(u for k,u in changed['directory']['users'].items() if k!=changed['directory_user_id'])['enabled']=False
            self.assertNotEqual(di.checks(changed,self.now)[1]['status'],'valide')
    def test_dialogue_identity_and_fresh_link(self):
        s=self.planned('ftp','data_blocked');ident=s['desktop_incident']['id']
        self.assertIn('pas de constat',di.dialogue(s,ident,'network',self.now)['answer'])
        s['network_observation']=dict(at=self.now,client_link=False);self.assertIn('débranchée',di.dialogue(s,ident,'network',self.now)['answer'])
        with self.assertRaises(ValueError):di.dialogue(s,'old','scope',self.now)

class ControllerTests(unittest.TestCase):
    proofs=ServicesTests.proofs
    planned=ServicesTests.planned
    repair=ServicesTests.repair
    finish=ServicesTests.finish
    login=ServicesTests.login
    def setUp(self):
        ServicesTests.setUp(self);self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.c=Controller(None,self.tmp.name);self.c.workspace.state=self.s
    def test_no_remote_and_stale_admin_are_denied(self):
        self.s['remote_session']=False
        with self.assertRaises(ValueError):self.c.desktop('ftp/login',dict(payload={}))
        self.s['observation']['probes']['directory']['at']=self.now-46
        with self.assertRaises(ValueError):self.c.desktop('ftp/admin',{})
    def test_wrong_environment_route_cannot_mutate(self):
        h=Mock();h.path='/workspace/desktop/ftp/operation'
        with self.assertRaises(ValueError):WorkspaceRoutes(self.c,'token').post(h,dict(environment_id='other',operation='set_service',payload=dict(value=False)))
        self.assertTrue(self.s['desktop_services']['ftp']['service_running'])
    def test_controller_persists_and_restore_clears_sessions(self):
        self.c.desktop('ftp/login',dict(payload=dict(username='depot',password='Formation!2026')))
        saved=Workspace(self.c.workspace.path);self.assertEqual(saved.state['desktop_services']['ftp']['sessions'],{})
    def test_callback_ticket_duration_and_dialogue(self):
        cb=Mock();self.c.on_change=cb
        result=self.c.next_desktop_incident('ftp',12);i=result['desktop_incident'];self.assertEqual(self.c.workspace.state['desktop_incident']['timer_minutes'],12)
        self.c.dialogue(dict(ticket_id=i['id'],question='scope'));self.assertEqual(cb.call_count,2)
    def test_pdf_validated_never_gets_free_points(self):
        s=self.planned('printing','wrong_default');self.c.workspace.state=s
        with self.assertRaises(ValueError):self.c.action('validate')
    def test_migration_preserves_existing_service_state(self):
        before=copy.deepcopy(self.s['desktop_services']);self.assertFalse(ds.ensure(self.s));self.assertEqual(self.s['desktop_services'],before)


class PrinterTopologyTests(unittest.TestCase):
    def test_generated_printer_identity_address_and_unique_ports(self):
        import xml.etree.ElementTree as ET
        import workspace_network
        from pathlib import Path
        with tempfile.TemporaryDirectory() as folder, patch.object(workspace_network.ptexplorer,'ptfile_encode'):
            s=workspace_network.build('printer-topology',folder)
            self.assertIn('printer',s['devices']);self.assertEqual(s['devices']['printer']['name'],'PRN-USR-01')
            root=ET.parse(Path(folder)/'reference.xml').getroot()
            devices=root.findall('NETWORK/DEVICES/DEVICE')
            printer=next(d for d in devices if d.findtext('ENGINE/NAME')==s['devices']['printer']['name'])
            self.assertEqual(printer.find('ENGINE/TYPE').get('model'),'Printer-PT')
            self.assertEqual(printer.findtext('ENGINE/.//PORT/IP'),s['devices']['printer']['ip'])
            self.assertEqual(len({d.findtext('ENGINE/SERIALNUMBER') for d in devices}),len(devices))
            ends=[]
            for cable in root.findall('NETWORK/LINKS/LINK/CABLE'):
                ports=cable.findall('PORT');ends.extend([(cable.findtext('FROM'),ports[0].text),(cable.findtext('TO'),ports[1].text)])
            self.assertEqual(len(ends),len(set(ends)))

class IntegrationTests(unittest.TestCase):
    setUp=ControllerTests.setUp
    proofs=ServicesTests.proofs
    planned=ServicesTests.planned
    repair=ServicesTests.repair
    finish=ServicesTests.finish
    login=ServicesTests.login
    def test_observer_processes_queue_and_keeps_application_validation(self):
        s=self.planned('printing','spooler_stopped');self.finish(s);s['validated']=True;self.c.workspace.state=s
        s['network_file']='C:/agency.pkt'
        devices=[dict(d,ports=[dict(name='FastEthernet0',linked=True,ip=d['ip'],mask='255.255.255.0')]) for d in s['devices'].values()]
        engine=Mock();engine.lock=threading.Lock();engine.snapshot.return_value=dict(saved_filename=s['network_file'],devices=devices);engine.ping.return_value=dict(status='valide',detail='reply');self.c.engine=engine
        self.c.observe(blocking=True)
        self.assertIn('printing',s['observation']['probes']);self.assertTrue(s['validated'])
        engine.ping.side_effect=lambda source,target:dict(status='non satisfait' if target==s['devices']['printer']['ip'] else 'valide',detail='test')
        self.c.observe(blocking=True);self.assertFalse(s['validated']);self.assertTrue(s['remote_session'])
    def test_scheduler_dispatches_selected_application_family(self):
        from service_desk import ServiceDesk
        t=Mock();t.state={'site':{'environment_id':'env'},'tickets':[]};t.controller=self.c;t.public.return_value={}
        desk=ServiceDesk(t,Mock());desk.settings.update(arrival_engine='apps',app_target='printing',ticket_minutes=15)
        self.c.next_desktop_incident=Mock()
        desk.create_site(None,[]);self.c.next_desktop_incident.assert_not_called()
        ticket=t.state['tickets'][0];self.assertEqual(ticket['stage'],'queued')
        self.assertEqual(ticket['arrival_plan']['target'],'printing');self.assertEqual(ticket['arrival_plan']['minutes'],15)
    def test_desktop_app_action_missing_environment_rejected(self):
        h=Mock();h.path='/workspace/desktop/ftp/login'
        with self.assertRaises(ValueError):WorkspaceRoutes(self.c,'token').post(h,{'payload':{}})

if __name__=='__main__':unittest.main()
