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
    def test_business_dependencies_are_documented_separately_from_permissions(self):
        state={'staff':[dict(display_name='Employé',department='Opérations',service_dependencies=['ftp'])],
               'client_workspaces':{'pc':{'requester':'Employé'}}}
        text=str(company_documents.public(state))
        self.assertIn('1 poste(s)',text);self.assertIn('Opérations',text)
        self.assertIn('ne donne aucun droit technique',text)
    def test_legacy_and_empty_environment(self):
        docs = company_documents.public({})
        self.assertEqual(len(docs), 4)
        self.assertIn('non renseigné', str(docs))
    def test_fault_and_observation_do_not_change_documentation(self):
        state = {'company': 'A', 'devices': {'client': {'name': 'PC-01'}}}
        docs = company_documents.public(state)
        state.update(read_allowed=False, observation={'status':'failed'}, file_incident={'cause':'denied'})
        self.assertEqual(docs, company_documents.public(state))

    def test_network_reference_is_categorized_without_inventing_missing_values(self):
        state={'company':'Horizon','devices':{'server':{'name':'SRV-01','ip':'10.8.0.10','password':'private'},'switch':{'name':'SW-01'}}}
        docs=company_documents.public(state)
        network=next(d for d in docs if d['id']=='company-network')
        self.assertEqual(network['category'],'Entreprise · Réseau')
        self.assertIn('10.8.0.10',str(network))
        self.assertIn('non renseignée',str(network))
        self.assertNotIn('private',str(docs))
        state['observation']={'status':'failed'};state['mixed_incident']={'cause':'hidden'}
        self.assertEqual(docs,company_documents.public(state))

    def test_enterprise_reference_documents_mask_gateway_and_vlan(self):
        state={'staff_size':30,'devices':{'client':{'name':'PC-01','ip':'10.10.10.21','vlan':10,'gateway':'10.10.10.1'}}}
        text=str(company_documents.public(state))
        self.assertIn('255.255.255.0',text);self.assertIn('10.10.10.1',text);self.assertIn('VLAN : 10',text)
        self.assertNotIn('masque : 255.255.255.0',str(company_documents.public({'devices':state['devices']})))
