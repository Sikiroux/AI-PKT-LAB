"""Le signalement nomme la ressource du bon poste sans divulguer la panne."""
import unittest
import test_enterprise_incidents as fixture
import enterprise_incidents as live

class TicketResourcesTests(unittest.TestCase):
 setUp=fixture.LiveTests.setUp
 tickets=fixture.LiveTests.tickets
 proofs=fixture.LiveTests.proofs
 def test_account_uses_target_identity_not_primary(self):
  t=self.tickets();live.receive(t,'ad',client_serial='second');row=t.state['tickets'][0]
  user=self.s['directory']['users'][self.s['client_workspaces']['second']['user_id']]
  self.assertEqual(row['request_context']['resource'],user['username'])
  self.assertEqual(row['request_context']['resource_scope'],'account')
  self.assertIn(user['username'],row['description'])
  self.assertNotIn('cause',row['request_context'])
 def test_shared_documents_name_remote_resource_and_expected_action(self):
  t=self.tickets();live.receive(t,'endpoint',client_serial='second');row=t.state['tickets'][0]
  self.assertEqual(row['request_context']['resource'],'\\\\'+self.s['devices']['server']['name']+'\\Documents')
  self.assertEqual(row['request_context']['resource_scope'],'remote')
  self.assertIn('Ouvrir',row['request_context']['expected_result'])
