"""Le DNS réparé ne prouve pas à lui seul la lecture demandée."""
import copy
import unittest
from unittest.mock import patch
import enterprise_incidents as live
import test_client_workspaces as fixtures
import test_enterprise_incidents as incidentfixtures

class DnsDocumentTests(unittest.TestCase):
    setUp=fixtures.ClientWorkspacesTests.setUp
    proofs=fixtures.ClientWorkspacesTests.proofs
    tickets=incidentfixtures.LiveTests.tickets

    def prepare(self,repair=True):
        tickets=self.tickets();live.receive(tickets,'dns',client_serial='second');ticket=tickets.state['tickets'][0]
        with self.c.client_scope('second'):
            s=self.c.workspace.state;self.proofs(s)
            user=s['directory']['users'][s['directory_user_id']]
            user.update(enabled=True,locked_until=None,must_change_password=False,password_expires_at=self.now+1000)
            fs=s['file_service'];fs.update(service_status='running',firewall_tcp445_allowed=True)
            share=fs['shares'][s['documents_share_id']];share['enabled']=True
            for layer in ('share_acl','folder_acl'):
                for action in ('read','list'):
                    share[layer][action]['user_ids']=[s['directory_user_id']]
                    share[layer][action]['group_ids']=[]
            if repair:
                s['dns_service']['clients']['client']['dns_server_ip']=s['devices']['server']['ip']
                s['dns_service']['cache']['client']={}
        with self.c.client_scope('second'):self.proofs(self.c.workspace.state)
        return tickets,ticket

    def deny_read(self):
        share=self.s['file_service']['shares'][self.s['documents_share_id']]
        for layer in ('share_acl','folder_acl'):share[layer]['read'].update(user_ids=[],group_ids=[])

    def test_repaired_dns_and_read_access_allow_completion(self):
        tickets,ticket=self.prepare();rows=live.checks(self.s,ticket,self.now)
        self.assertEqual([r['status'] for r in rows],['valide','valide'])
        tickets.workspace_action(ticket,'close',{});self.assertEqual(ticket['status'],'clos')

    def test_name_only_cannot_close_when_read_is_denied(self):
        tickets,ticket=self.prepare();self.deny_read()
        rows=live.checks(self.s,ticket,self.now)
        self.assertEqual([r['status'] for r in rows],['valide','non satisfait'])
        with self.assertRaises(ValueError):tickets.workspace_action(ticket,'close',{})
        self.assertFalse(ticket['complete']);self.assertNotEqual(ticket['status'],'clos')

    def test_empty_share_does_not_count_as_document_read(self):
        tickets,ticket=self.prepare();self.s['file_service']['files']={}
        self.assertEqual(live.checks(self.s,ticket,self.now)[1]['status'],'non satisfait')

    def test_missing_login_keeps_document_unverified(self):
        tickets,ticket=self.prepare();self.s['client_workspaces']['second']['local']['directory_auth']=None
        self.assertEqual([r['status'] for r in live.checks(self.s,ticket,self.now)],['valide','inconnu'])

    def test_unresolved_name_does_not_claim_document_attempt(self):
        tickets,ticket=self.prepare(False);rows=live.checks(self.s,ticket,self.now)
        self.assertNotEqual(rows[0]['status'],'valide');self.assertEqual(rows[1]['status'],'inconnu')
        with patch('enterprise_incidents.time.time',return_value=self.now):live.dialogue(self.s,ticket['id'],'retest')
        self.assertEqual(self.s['live_incidents'][ticket['id']]['client_report']['attempts'][-1]['status'],'failed' if rows[0]['status']=='non satisfait' else 'unknown')

    def test_missing_app_and_wrong_drive_still_block_document(self):
        tickets,ticket=self.prepare();endpoint=self.s['client_workspaces']['second']['endpoint']
        endpoint['applications'].remove('documents')
        self.assertEqual(live.checks(self.s,ticket,self.now)[1]['status'],'non satisfait')
        endpoint['applications'].append('documents');endpoint['mapped_drive']['path']='\\\\wrong\\Documents'
        self.assertEqual(live.checks(self.s,ticket,self.now)[1]['status'],'non satisfait')

    def test_retest_distinguishes_resolved_name_and_denied_read(self):
        tickets,ticket=self.prepare();self.deny_read()
        with patch('enterprise_incidents.time.time',return_value=self.now):answer=live.dialogue(self.s,ticket['id'],'retest')['answer']
        self.assertIn('nom est retrouvé',answer);self.assertIn('lecture',answer);self.assertIn('indisponible',answer)
        self.assertNotIn('ne retrouve',answer)

    def test_successful_retest_and_verification_do_not_modify_files(self):
        tickets,ticket=self.prepare();before=copy.deepcopy(self.s)
        live.checks(self.s,ticket,self.now);self.assertEqual(self.s,before)
        with patch('enterprise_incidents.time.time',return_value=self.now):answer=live.dialogue(self.s,ticket['id'],'retest')['answer']
        self.assertIn('autorise la lecture',answer)
        self.assertEqual(self.s['file_service'],before['file_service']);self.c.observe.assert_not_called()

if __name__=='__main__':unittest.main()
