"""Réactiver le compte n'est pas une preuve de connexion de l'employé."""
import copy
import unittest
import directory_adapter as ad
import enterprise_incidents as live
import test_client_workspaces as fixtures
import test_enterprise_incidents as incidentfixtures

class LoginConfirmationTests(unittest.TestCase):
    setUp=fixtures.ClientWorkspacesTests.setUp
    proofs=fixtures.ClientWorkspacesTests.proofs
    tickets=incidentfixtures.LiveTests.tickets

    def prepare(self):
        tickets=self.tickets();live.receive(tickets,'ad',client_serial='second')
        ticket=tickets.state['tickets'][0]
        self.s['directory']['users'][ticket['requester_account_id']]['enabled']=True
        with self.c.client_scope('second'):
            self.proofs(self.c.workspace.state)
            self.c.workspace.state['directory_auth']=None
        return tickets,ticket

    def test_enabled_account_without_login_is_unknown_and_cannot_close(self):
        tickets,ticket=self.prepare();row=live.checks(self.s,ticket,self.now)[0]
        self.assertEqual(row['status'],'inconnu');self.assertIn('Ouvre la session',row['detail'])
        with self.assertRaises(ValueError):tickets.workspace_action(ticket,'close',{})
        self.assertNotEqual(ticket['status'],'clos');self.assertFalse(ticket['complete'])

    def test_login_of_original_user_on_original_station_allows_confirmation(self):
        tickets,ticket=self.prepare()
        with self.c.client_scope('second'):
            self.c.workspace.state['directory_auth']=ad.open_session(self.c.workspace.state,self.now)
        self.assertEqual(live.checks(self.s,ticket,self.now)[0]['status'],'valide')
        tickets.workspace_action(ticket,'close',{})
        self.assertEqual(ticket['status'],'clos')

    def test_primary_session_is_not_secondary_session(self):
        tickets,ticket=self.prepare()
        self.s['directory_auth']=ad.open_session(self.s,self.now)
        self.assertEqual(live.checks(self.s,ticket,self.now)[0]['status'],'inconnu')

    def test_wrong_station_token_or_old_password_stamp_cannot_confirm(self):
        tickets,ticket=self.prepare()
        with self.c.client_scope('second'):
            auth=ad.open_session(self.c.workspace.state,self.now)
            self.c.workspace.state['directory_auth']=auth
        local=self.s['client_workspaces']['second']['local']
        for field in ('station_serial','account_stamp'):
            original=local['directory_auth'][field];local['directory_auth'][field]='different'
            self.assertEqual(live.checks(self.s,ticket,self.now)[0]['status'],'inconnu')
            local['directory_auth'][field]=original

    def test_login_cannot_replace_fresh_network_observation(self):
        tickets,ticket=self.prepare()
        with self.c.client_scope('second'):
            self.c.workspace.state['directory_auth']=ad.open_session(self.c.workspace.state,self.now)
        self.assertNotEqual(live.checks(self.s,ticket,self.now+46)[0]['status'],'valide')

    def test_confirmation_is_read_only_and_never_logs_in_for_user(self):
        tickets,ticket=self.prepare();before=copy.deepcopy(self.s)
        live.checks(self.s,ticket,self.now)
        self.assertEqual(self.s,before);self.c.observe.assert_not_called()

if __name__=='__main__':unittest.main()
