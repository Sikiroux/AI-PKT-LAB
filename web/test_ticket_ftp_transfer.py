"""Un service disponible ne vaut pas transfert effectué depuis le poste demandé."""
import copy
import unittest
from unittest.mock import patch
import desktop_services as ds
import enterprise_incidents as live
import ftp_transfers
import test_client_workspaces as fixtures
import test_enterprise_incidents as incidentfixtures

class TransferTicketTests(unittest.TestCase):
    setUp=fixtures.ClientWorkspacesTests.setUp
    proofs=fixtures.ClientWorkspacesTests.proofs
    tickets=incidentfixtures.LiveTests.tickets

    def prepare(self):
        tickets=self.tickets()
        with patch('enterprise_incidents.time.time',return_value=self.now):live.receive(tickets,'ftp',client_serial='second')
        ticket=tickets.state['tickets'][0]
        self.s['desktop_services']['ftp']['service_running']=True
        with self.c.client_scope('second'):self.proofs(self.c.workspace.state)
        return tickets,ticket

    def download(self,ticket,serial='second',name=None,at=None):
        with self.c.client_scope(serial):
            s=self.c.workspace.state;self.proofs(s)
            login=ds.ftp_action(s,'login',{'username':'depot','password':'Formation!2026'},'client',self.now+1)
            self.assertTrue(login['allowed'])
            return ds.ftp_action(s,'download',{'name':name or ticket['transfer_goal']['name']},'client',self.now+2 if at is None else at)

    def rows(self,ticket):return live.checks(self.s,ticket,self.now+10)

    def test_ticket_names_document_and_target_station(self):
        tickets,ticket=self.prepare();goal=ticket['transfer_goal']
        self.assertEqual(goal,{'direction':'download','name':'Notice.txt'})
        self.assertIn(goal['name'],ticket['request_context']['expected_result'])
        self.assertIn('second',ticket['request_context']['expected_result'])
        self.assertEqual(self.s['live_incidents'][ticket['id']]['transfer_goal'],goal)

    def test_running_service_and_preexisting_local_copy_do_not_complete(self):
        tickets,ticket=self.prepare();name=ticket['transfer_goal']['name']
        self.s['client_workspaces']['second']['endpoint']['local_files'][name]=self.s['desktop_services']['ftp']['files'][name]
        self.assertEqual([r['status'] for r in self.rows(ticket)],['valide','inconnu'])
        with patch('enterprise_incidents.time.time',return_value=self.now+10):
            with self.assertRaises(ValueError):tickets.workspace_action(ticket,'close',{})
        self.assertNotEqual(ticket['status'],'clos')

    def test_successful_download_then_close(self):
        tickets,ticket=self.prepare();self.assertTrue(self.download(ticket)['allowed'])
        self.assertEqual([r['status'] for r in self.rows(ticket)],['valide','valide'])
        with patch('enterprise_incidents.time.time',return_value=self.now+10):tickets.workspace_action(ticket,'close',{})
        self.assertEqual(ticket['status'],'clos')

    def test_other_station_and_other_file_do_not_satisfy_goal(self):
        tickets,ticket=self.prepare();self.download(ticket,serial='client')
        self.assertEqual(self.rows(ticket)[1]['status'],'inconnu')
        self.s['desktop_services']['ftp']['files']['Other.txt']='Other'
        self.download(ticket,name='Other.txt')
        self.assertEqual(self.rows(ticket)[1]['status'],'inconnu')

    def test_old_foreign_or_future_receipt_does_not_satisfy_goal(self):
        tickets,ticket=self.prepare();self.download(ticket)
        history=self.s['desktop_services']['ftp']['transfer_history'];original=copy.deepcopy(history[-1])
        for field,value in [('completed_at',self.now-1),('completed_at',self.now+100),('environment_id','other'),('source_role','technician'),('account_id','other'),('station_serial','other')]:
            history[-1]=copy.deepcopy(original);history[-1][field]=value
            self.assertEqual(self.rows(ticket)[1]['status'],'inconnu',field)
        history[-1]=original;self.assertEqual(self.rows(ticket)[1]['status'],'valide')

    def test_local_or_server_content_change_requires_current_download(self):
        tickets,ticket=self.prepare();self.download(ticket);name=ticket['transfer_goal']['name']
        local=self.s['client_workspaces']['second']['endpoint']['local_files'];original=local[name]
        local[name]='changed';self.assertEqual(self.rows(ticket)[1]['status'],'inconnu')
        local[name]=original;self.s['desktop_services']['ftp']['files'][name]='new server version'
        self.assertEqual(self.rows(ticket)[1]['status'],'inconnu')
        self.download(ticket);self.assertEqual(self.rows(ticket)[1]['status'],'valide')

    def test_failed_transfer_does_not_record_receipt(self):
        tickets,ticket=self.prepare();self.s['desktop_services']['ftp']['accounts']['depot']['read']=False
        result=self.download(ticket);self.assertFalse(result['allowed'])
        self.assertNotIn('transfer_history',self.s['desktop_services']['ftp'])

    def test_checks_and_dialogue_never_download_for_user(self):
        tickets,ticket=self.prepare();before=copy.deepcopy(self.s['desktop_services'])
        self.rows(ticket)
        with patch('enterprise_incidents.time.time',return_value=self.now+10):answer=live.dialogue(self.s,ticket['id'],'retest')['answer']
        self.assertIn('accessible',answer);self.assertIn('pas encore confirmé',answer)
        self.assertEqual(self.s['desktop_services'],before);self.c.observe.assert_not_called()

    def test_legacy_goal_requires_a_real_new_download_too(self):
        tickets,ticket=self.prepare();record=self.s['live_incidents'][ticket['id']]
        record.pop('transfer_goal');record['ticket'].pop('transfer_goal')
        self.assertEqual(self.rows(ticket)[1]['status'],'inconnu')
        self.download(ticket);self.assertEqual(self.rows(ticket)[1]['status'],'valide')

    def test_history_is_bounded_private_and_has_no_password_or_content(self):
        tickets,ticket=self.prepare();self.download(ticket)
        with self.c.client_scope('second'):
            s=self.c.workspace.state;name=ticket['transfer_goal']['name']
            for _ in range(105):ftp_transfers.record_download(s,'client',name,s['desktop_services']['ftp']['files'][name],self.now+2)
        history=self.s['desktop_services']['ftp']['transfer_history']
        self.assertEqual(len(history),100);self.assertNotIn('password',str(history));self.assertNotIn('content',history[-1])
        self.assertNotIn('transfer_history',ds.public(self.s)['ftp'])

if __name__=='__main__':unittest.main()
