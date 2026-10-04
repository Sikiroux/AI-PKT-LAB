import copy
import json
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import Mock
import directory_adapter as ad
import directory_incidents
import files_adapter as fa
import sim_ad
from workspace_app import Controller
from workspace_model import generate,evaluate,Workspace
from workspace_routes import WorkspaceRoutes

class FilesIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.c=Controller(None,self.tmp.name);self.s=generate('files-test');self.s['environment_id']='env'
        self.s['devices']={k:dict(name=k,ip=ip,serial=k) for k,ip in [('client','192.168.1.2'),('server','192.168.1.10'),('technician','192.168.1.20')]}
        ad.ensure(self.s);fa.ensure(self.s);self.c.workspace.state=self.s;self.s['remote_session']=True
        now=time.time();self.s['observation']={'probes':{key:dict(at=now,status='passed',source_device=source,target=target) for key,source,target in [('remote','technician','192.168.1.2'),('share','client','192.168.1.10'),('directory','technician','192.168.1.10')]}}
        self.sid=self.s['documents_share_id']
    def grant(self,right='read'):
        self.c.action('grant_'+right)
    def login(self):
        self.s['remote_session']=True
        return self.c.directory('login',{'password':sim_ad.TRAINING_PASSWORD})
    def run_file(self,action,**kwargs):
        return self.c.files('action',dict(request=dict(action=action,share_id=self.sid,**kwargs)))['result']
    def test_migration_preserves_denial_and_ids_and_is_idempotent(self):
        self.assertEqual(self.s['file_service']['server']['id'],'server')
        self.assertEqual(self.s['file_service']['environment_id'],'env')
        self.login();self.assertFalse(self.run_file('list')['allowed'])
        before=copy.deepcopy(self.s);self.assertFalse(fa.ensure(self.s));self.assertEqual(before,self.s)
    def test_group_membership_and_both_acl_layers_required(self):
        self.grant();self.login();self.assertTrue(self.run_file('list')['allowed'])
        self.c.files('operation',{'operation':'set_acl','payload':dict(share_id=self.sid,layer='folder_acl',action='read',user_ids=[],group_ids=[])})
        self.assertFalse(evaluate(self.s,'read')['allowed'])
        self.assertTrue(self.run_file('list')['allowed'])
    def test_authentication_required_even_with_permissions(self):
        self.grant();self.assertFalse(self.run_file('list')['allowed'])
        self.login();self.assertTrue(self.run_file('list')['allowed'])
    def test_create_read_edit_delete_and_revision_conflict(self):
        self.grant();self.grant('write');self.login()
        rev=self.s['file_service']['revision']
        r=self.run_file('write',name='Bonjour.txt',content='Bonjour é',expected_revision=rev);self.assertTrue(r['allowed']);fid=r['data']['id']
        self.assertEqual(self.run_file('read',file_id=fid)['data']['content'],'Bonjour é')
        self.assertEqual(self.run_file('write',file_id=fid,content='autre',expected_revision=rev)['code'],'REVISION_CONFLICT')
        r=self.run_file('write',file_id=fid,content='autre',expected_revision=self.s['file_service']['revision']);self.assertTrue(r['allowed'])
        self.assertTrue(self.run_file('delete',file_id=fid,expected_revision=self.s['file_service']['revision'])['allowed'])
        self.assertNotIn(fid,self.s['file_service']['files'])
    def test_disk_and_quota_block_growth_not_reading(self):
        self.grant();self.grant('write');self.login()
        self.c.files('operation',{'operation':'set_quota','payload':dict(share_id=self.sid,mode='hard',limit_bytes=1)})
        self.assertTrue(evaluate(self.s,'read')['allowed']);self.assertFalse(evaluate(self.s,'write')['allowed'])
        self.c.files('operation',{'operation':'set_quota','payload':dict(share_id=self.sid,mode='off',limit_bytes=None)})
        self.c.files('operation',{'operation':'set_volume_capacity','payload':dict(capacity_bytes=1)})
        self.assertTrue(evaluate(self.s,'read')['allowed']);self.assertFalse(evaluate(self.s,'write')['allowed'])
    def test_admin_only_needs_technician_network_and_can_restart_service(self):
        self.c.files('operation',{'operation':'set_service_status','payload':{'status':'stopped'}})
        self.assertEqual(self.c.files('admin',{})['service']['service_status'],'stopped')
        self.c.files('operation',{'operation':'set_service_status','payload':{'status':'running'}})
        self.s['observation']['probes']['directory']['at']=0
        with self.assertRaises(ValueError):self.c.files('admin',{})
    def test_remote_session_and_current_environment_required(self):
        self.s['remote_session']=False
        with self.assertRaises(ValueError):self.run_file('list')
        h=Mock();h.path='/workspace/files/admin'
        with self.assertRaises(ValueError):WorkspaceRoutes(self.c,'token').post(h,{'environment_id':'other'})
    def test_legacy_write_action_uses_real_file_model(self):
        self.grant();self.grant('write');self.login();self.c.action('write')
        self.assertIn('Test.txt',fa.names(self.s));self.c.action('write')
        self.assertEqual(fa.names(self.s).count('Test.txt'),1)
    def test_public_state_contains_no_contents(self):
        text=json.dumps(self.c.workspace.public())
        self.assertNotIn('Document de formation :',text);self.assertNotIn('credential',text)
    def test_saved_content_restores_but_observation_and_auth_do_not(self):
        self.grant();self.grant('write');self.login()
        self.run_file('write',name='Save.txt',content='texte sauvegardé',expected_revision=self.s['file_service']['revision'])
        loaded=Workspace(self.c.workspace.path)
        self.assertTrue(any(f['content']=='texte sauvegardé' for f in loaded.state['file_service']['files'].values()))
        self.assertIsNone(loaded.state['directory_auth']);self.assertIsNone(loaded.state['observation'])
    def test_backup_before_files_migration(self):
        old=copy.deepcopy(self.s);old.pop('file_service');old.pop('documents_share_id')
        folder=Path(self.tmp.name)/'old';folder.mkdir();p=folder/'session.json';p.write_text(json.dumps(old))
        raw=p.read_bytes();c=Controller(None,folder)
        self.assertEqual(p.with_suffix('.before-files.json').read_bytes(),raw)
        self.assertIn('file_service',c.workspace.state)
    def test_ad_read_group_incident_remains_effective_with_files(self):
        s=self.s
        for _ in range(5):
            s=directory_incidents.prepare(s,time.time())
            if s['directory_incident']['family']=='read_group_missing':break
            s['validated']=True
        self.c.workspace.state=s;self.s=s;self.login()
        self.assertFalse(evaluate(s,'read')['allowed']);self.grant();self.login()
        self.assertTrue(evaluate(s,'read')['allowed'])

if __name__=='__main__':unittest.main()
