import copy
import json
import unittest
import company_documents

class CompanyDocumentsTests(unittest.TestCase):
    def test_facts_scope_and_no_secrets_or_hidden_fault(self):
        state = {'company': 'Agence exemple', 'devices': {'client': {'name': 'PC-CPT-01', 'ip': '10.1.2.3', 'password': 'secret-device'}}, 'directory': {'domain': {'dns_name': 'exemple.local'}, 'users': {'a': {'password': 'secret-user'}}}, 'documents_dns_name': 'fichiers.exemple.local', 'file_incident': {'cause': 'hidden-cause'}, 'observation': {'status': 'passed'}}
        before = copy.deepcopy(state)
        docs = company_documents.public(state)
        text = json.dumps(docs, ensure_ascii=False)
        self.assertIn('PC-CPT-01', text)
        self.assertIn('10.1.2.3', text)
        self.assertIn('exemple.local', text)
        for secret in ('secret-device', 'secret-user', 'hidden-cause'):
            self.assertNotIn(secret, text)
        self.assertEqual(state, before)
        self.assertEqual(docs, company_documents.public(state))
        self.assertEqual(len({d['id'] for d in docs}), len(docs))
    def test_legacy_and_empty_environment(self):
        docs = company_documents.public({})
        self.assertEqual(len(docs), 4)
        self.assertIn('non renseigné', str(docs))
    def test_fault_and_observation_do_not_change_documentation(self):
        state = {'company': 'A', 'devices': {'client': {'name': 'PC-01'}}}
        docs = company_documents.public(state)
        state.update(read_allowed=False, observation={'status':'failed'}, file_incident={'cause':'denied'})
        self.assertEqual(docs, company_documents.public(state))
