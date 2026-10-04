import copy
import json
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import Mock
import sim_ad
import directory_adapter as ad
from workspace_app import Controller
from workspace_model import generate, evaluate, Workspace
from workspace_routes import WorkspaceRoutes

class IntegrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.c=Controller(None,self.tmp.name)
        s=generate('annuaire');s['environment_id']='env'
        s['devices']={k:dict(name=n,ip=ip,serial=k) for k,n,ip in [('client','Client','192.168.1.2'),('server','Serveur','192.168.1.10'),('technician','Tech','192.168.1.20')]}
        self.c.workspace.state=s;ad.ensure(s);s['remote_session']=True;self.proofs()
    def proofs(self):
        s=self.c.workspace.state;now=time.time()
        s['observation']={'probes':{key:dict(at=now,status='passed',source_device=source,target=target) for key,source,target in [('remote','Tech','192.168.1.2'),('share','Client','192.168.1.10'),('directory','Tech','192.168.1.10')]}}
    def grant(self):
        self.c.action('grant_read')
    def login(self,password=sim_ad.TRAINING_PASSWORD):
        return self.c.directory('login',{'password':password})['result']
    def test_groups_and_login_both_required(self):
        self.grant();self.assertFalse(evaluate(self.c.workspace.state,'read')['allowed'])
        self.assertTrue(self.login()['allowed']);self.assertTrue(evaluate(self.c.workspace.state,'read')['allowed'])
        self.assertFalse(evaluate(self.c.workspace.state,'write')['allowed'])
    def test_remove_membership_invalidates_login_and_right(self):
        self.grant();self.login();s=self.c.workspace.state
        self.c.directory('operation',{'operation':'remove_group_member','payload':{'user_id':s['directory_user_id'],'group_id':s['directory_resource']['allowed_group_ids']['read'][0]}})
        self.assertIsNone(s['directory_auth']);self.login();self.assertFalse(evaluate(s,'read')['allowed'])
    def test_reset_expired_password_and_mandatory_change(self):
        s=self.c.workspace.state;uid=s['directory_user_id'];s['directory']['users'][uid]['password_expires_at']=time.time()-5
        r=self.c.directory('operation',{'operation':'reset_password','payload':{'user_id':uid}})['result']
        temp=r['temporary_password'];self.assertGreater(s['directory']['users'][uid]['password_expires_at'],time.time())
        self.assertEqual(self.login(temp)['code'],sim_ad.MUST_CHANGE_PASSWORD)
        self.assertTrue(self.c.directory('change-password',{'old_password':temp,'new_password':'Formation!Nouvelle'})['result']['allowed'])
        self.assertTrue(self.login('Formation!Nouvelle')['allowed']);self.assertFalse(self.login(temp)['allowed'])
    def test_failed_login_revisions_and_no_secret_audit(self):
        s=self.c.workspace.state;before=s['directory']['revision'];self.login('faux-secret')
        self.assertGreater(s['directory']['revision'],before)
        self.assertNotIn('faux-secret',json.dumps(s['directory']['audit']))
    def test_distinct_source_proofs_and_no_permission_bypass(self):
        s=self.c.workspace.state;s['observation']['probes']['directory']['status']='failed'
        with self.assertRaises(ValueError):self.grant()
        self.assertTrue(self.login()['allowed'])
        s['observation']['probes']['share']['source_device']='Tech'
        self.assertFalse(evaluate(s,'read')['allowed'])
    def test_stale_or_missing_environment_rejected(self):
        routes=WorkspaceRoutes(self.c,'t');h=Mock();h.path='/workspace/directory/login'
        for data in ({'password':sim_ad.TRAINING_PASSWORD},{'environment_id':'old','password':sim_ad.TRAINING_PASSWORD}):
            with self.assertRaises(ValueError):routes.post(h,data)
    def test_roundtrip_clears_authentication_preserves_directory(self):
        self.grant();self.login();s=self.c.workspace.state;self.c.workspace.save()
        w=Workspace(self.c.workspace.path)
        self.assertIsNone(w.state['directory_auth']);self.assertIsNone(w.state['observation'])
        self.assertEqual(w.state['directory'],s['directory'])
        self.assertNotIn('credential',json.dumps(self.c.workspace.public()))
        self.assertNotIn('credential',json.dumps(self.c.directory('state',{})['directory']))
    def test_migration_preserves_old_permissions_and_is_idempotent(self):
        s=generate('legacy');s['devices']=copy.deepcopy(self.c.workspace.state['devices']);s['read_allowed']=True;s['account_enabled']=False
        self.assertTrue(ad.ensure(s));uid=s['directory_user_id'];self.assertFalse(s['directory']['users'][uid]['enabled'])
        gid=s['directory_resource']['allowed_group_ids']['read'][0];self.assertIn(uid,s['directory']['groups'][gid]['member_user_ids'])
        before=copy.deepcopy(s);self.assertFalse(ad.ensure(s));self.assertEqual(s,before)
    def test_existing_session_gets_original_backup_before_migration(self):
        folder=Path(self.tmp.name)/'migration';folder.mkdir()
        original=generate('old');original['devices']=copy.deepcopy(self.c.workspace.state['devices'])
        path=folder/'session.json';raw=json.dumps(original);path.write_text(raw)
        Controller(None,folder)
        self.assertEqual(path.with_suffix('.before-directory.json').read_text(),raw)
        self.assertIn('directory',json.loads(path.read_text()))

    def test_bad_old_secret_counts(self):
        s=self.c.workspace.state;uid=s['directory_user_id']
        r=self.c.directory('change-password',{'old_password':'wrong','new_password':'Formation!Autre'})
        self.assertFalse(r['result']['allowed']);self.assertEqual(s['directory']['users'][uid]['failed_attempts'],1)

if __name__=='__main__':unittest.main()
