"""L'identité du signalement ne suit pas la nouvelle affectation du poste."""
import copy
import unittest
from unittest.mock import patch
import company_registry as registry
import enterprise_incidents as live
import test_company_registry as registry_fixtures
import test_client_workspaces as fixtures
import test_enterprise_incidents as incident_fixtures

class RegistryIdentityTests(unittest.TestCase):
    def test_refresh_never_replaces_recorded_requester(self):
        s=registry_fixtures.fixture();registry.ensure(s)
        ticket={'id':'T','kind':'workspace','target_serial':'s2'}
        registry.link_tickets(s,[ticket]);before=copy.deepcopy(ticket)
        s['client_workspaces']['s2']['user_id']='u1';registry.ensure(s)
        self.assertNotEqual(registry.links(s,'s2')['employee_id'],ticket['employee_id'])
        self.assertFalse(registry.link_tickets(s,[ticket]));self.assertEqual(ticket,before)

    def test_first_link_uses_reported_account_not_new_occupant(self):
        s=registry_fixtures.fixture();registry.ensure(s)
        original=registry.links(s,'s2')['employee_id']
        s['client_workspaces']['s2']['user_id']='u1';registry.ensure(s)
        ticket={'id':'T','kind':'workspace','target_serial':'s2','requester_account_id':'u2'}
        registry.link_tickets(s,[ticket]);self.assertEqual(ticket['employee_id'],original)

class RequesterChecksTests(unittest.TestCase):
    setUp=fixtures.ClientWorkspacesTests.setUp
    proofs=fixtures.ClientWorkspacesTests.proofs
    tickets=incident_fixtures.LiveTests.tickets

    def create(self):
        tickets=self.tickets();live.receive(tickets,'ad',client_serial='second')
        return tickets,tickets.state['tickets'][0]

    def test_creation_records_original_account_in_both_stores(self):
        tickets,ticket=self.create();record=self.s['live_incidents'][ticket['id']]
        uid=self.s['client_workspaces']['second']['user_id']
        self.assertEqual(ticket['requester_account_id'],uid);self.assertEqual(record['requester_account_id'],uid)

    def test_new_occupant_cannot_complete_or_close_original_request(self):
        tickets,ticket=self.create();original=ticket['employee_id']
        self.s['client_workspaces']['second']['user_id']=self.s['directory_user_id']
        with self.c.client_scope('second'):self.proofs(self.c.workspace.state)
        registry.ensure(self.s);registry.link_tickets(self.s,[ticket])
        self.assertEqual(ticket['employee_id'],original)
        rows=live.checks(self.s,ticket,self.now)
        self.assertEqual(rows[0]['status'],'inconnu');self.assertIn('a changé',rows[0]['detail'])
        with self.assertRaises(ValueError):tickets.workspace_action(ticket,'close',{})
        self.assertFalse(ticket['complete']);self.assertNotEqual(ticket['status'],'clos')

    def test_original_assignment_and_repair_can_be_validated(self):
        tickets,ticket=self.create();uid=ticket['requester_account_id']
        self.s['directory']['users'][uid]['enabled']=True
        with self.c.client_scope('second'):self.proofs(self.c.workspace.state)
        self.assertEqual(live.checks(self.s,ticket,self.now)[0]['status'],'valide')

    def test_legacy_client_report_still_guards_original_identity(self):
        tickets,ticket=self.create();record=self.s['live_incidents'][ticket['id']]
        record.pop('requester_account_id');record['ticket'].pop('requester_account_id')
        self.s['client_workspaces']['second']['user_id']=self.s['directory_user_id']
        self.assertEqual(live.checks(self.s,ticket,self.now)[0]['status'],'inconnu')

    def test_missing_target_or_unidentifiable_requester_is_unknown(self):
        tickets,ticket=self.create();record=self.s['live_incidents'][ticket['id']]
        record.pop('requester_account_id');record.pop('client_report');record['ticket'].pop('requester_account_id');record['ticket'].pop('employee_id')
        self.assertEqual(live.checks(self.s,ticket,self.now)[0]['status'],'inconnu')
        self.s['client_workspaces'].pop('second')
        self.assertEqual(live.checks(self.s,ticket,self.now)[0]['status'],'inconnu')

    def test_cable_observation_is_separate_from_ip_result(self):
        tickets=self.tickets();live.receive(tickets,'dns',client_serial='second');ident=tickets.state['tickets'][0]['id']
        local=self.s['client_workspaces']['second']['local']
        local['network_observation']={'at':100,'client_link':False}
        with patch('enterprise_incidents.time.time',return_value=101):
            answer=live.dialogue(self.s,ident,'network')['answer']
            self.assertIn('débranchée',answer)
            self.assertNotIn('débranchée',live.dialogue(self.s,ident,'ip')['answer'])
        with patch('enterprise_incidents.time.time',return_value=146):
            self.assertNotIn('débranchée',live.dialogue(self.s,ident,'network')['answer'])

if __name__=='__main__':unittest.main()
