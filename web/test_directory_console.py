import copy
import unittest
import directory_console as console
from test_files_integration import FilesIntegrationTests

class DirectoryConsoleTests(unittest.TestCase):
    setUp = FilesIntegrationTests.setUp
    def test_revision_conflict_leaves_all_state_untouched(self):
        uid=self.s['directory_user_id']; rev=self.s['directory']['revision']
        self.c.directory('operation',dict(operation='update_user',payload={'user_id':uid,'display_name':'Compte renommé'},expected_revision=rev))
        before=copy.deepcopy(self.s)
        with self.assertRaises(ValueError):
            self.c.directory('operation',dict(operation='update_user',payload={'user_id':uid,'display_name':'Ancienne vue'},expected_revision=rev))
        self.assertEqual(before,self.s)
    def test_read_keeps_proofs_and_state_unchanged(self):
        self.c.workspace.save(); before=copy.deepcopy(self.s)
        result=self.c.directory('state',{})
        self.assertEqual(before,self.s)
        self.assertEqual(result['administration']['environment_id'],'env')
        self.assertNotIn('credential',repr(result))
    def test_matching_revision_does_not_bypass_network(self):
        self.s['observation']['probes']['directory']['at']=0
        before=copy.deepcopy(self.s)
        with self.assertRaises(ValueError):
            self.c.directory('operation',dict(operation='unlock_user',payload={'user_id':self.s['directory_user_id']},expected_revision=self.s['directory']['revision']))
        self.assertEqual(before,self.s)
    def test_wrong_registry_environment_has_no_links(self):
        self.c.workspace.save(); self.s['company_registry']['environment_id']='foreign'
        result=console.public_context(self.s)
        self.assertEqual(result['account_links'],{})
        self.assertEqual(result['computer_links'],{})
    def test_ambiguous_computer_link_is_not_chosen(self):
        self.c.workspace.save()
        assets=self.s['company_registry']['assets']
        asset=next(iter(assets.values()))
        asset['represented']=True
        self.s['directory']['computers']['test']={'device_id':asset['source_role']}
        assets['duplicate']=copy.deepcopy(asset)
        self.assertNotIn('test',console.public_context(self.s)['computer_links'])
    def test_account_link_survives_display_name_change(self):
        self.c.workspace.save(); uid=self.s['directory_user_id']
        before=console.public_context(self.s)['account_links'][uid]
        self.c.directory('operation',dict(operation='update_user',payload={'user_id':uid,'display_name':'Nouveau nom'},expected_revision=self.s['directory']['revision']))
        after=console.public_context(self.s)['account_links'][uid]
        self.assertEqual([a['id'] for a in before['assets']],[a['id'] for a in after['assets']])
        self.assertEqual([p['id'] for p in before['employees']],[p['id'] for p in after['employees']])
    def test_revision_type_is_strict_and_legacy_request_supported(self):
        for value in (True,'1',None,1.0):
            with self.assertRaises(ValueError):console.check_revision({'revision':1},{'expected_revision':value})
        console.check_revision({'revision':1},{})
        console.check_revision({'revision':1},{'expected_revision':1})

del FilesIntegrationTests
