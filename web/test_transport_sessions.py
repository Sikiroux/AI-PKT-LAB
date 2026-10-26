"""Mobilité/VPN : invalider le transport sans déconnecter l'employé."""
import copy
import unittest
import technician_model
import test_client_workspaces as fixtures
import directory_adapter as ad
import network_proofs
from workspace_model import evaluate

class TransportSessionsTests(unittest.TestCase):
    setUp=fixtures.ClientWorkspacesTests.setUp
    proofs=fixtures.ClientWorkspacesTests.proofs

    def prepare(self):
        technician_model.ensure(self.s)
        self.s['directory_auth']=ad.open_session(self.s,self.now)
        for profile in self.s['client_workspaces'].values():
            profile['local'].update(remote_session=True,directory_auth={'status':'authenticated','user_id':profile['user_id']},validated=True,
                                    observation=copy.deepcopy(self.s['observation']),network_observation={'at':self.now})
        self.s['validated']=True
        return copy.deepcopy(self.s['directory_auth']),copy.deepcopy(self.s['client_workspaces'])

    def test_move_preserves_logon_but_invalidates_all_projections(self):
        auth,profiles=self.prepare()
        technician_model.invalidate(self.s)
        self.assertEqual(self.s['directory_auth'],auth)
        self.assertTrue(self.s['remote_session'])
        self.assertFalse(self.s['validated'])
        for serial,profile in self.s['client_workspaces'].items():
            local=profile['local']
            self.assertIsNone(local['observation']);self.assertIsNone(local['network_observation'])
            self.assertEqual(local['directory_auth'],profiles[serial]['local']['directory_auth'])
            self.assertTrue(local['remote_session']);self.assertFalse(local['validated'])
        self.assertEqual(ad.authentication(self.s,'client',self.now),auth)
        self.assertFalse(evaluate(self.s,'remote',self.now)['allowed'])

    def test_vpn_disconnect_does_not_logout_employee(self):
        auth,_=self.prepare()
        self.s['technician_session']['vpn'].update(connected=True,expires_at=self.now+100)
        result=technician_model.vpn(self.s,'disconnect',now=self.now)
        self.assertEqual(result['code'],'VPN_DISCONNECTED')
        self.assertFalse(self.s['technician_session']['vpn']['connected'])
        self.assertEqual(self.s['directory_auth'],auth)
        self.assertTrue(self.s['remote_session'])
        self.assertIsNone(self.s['observation'])

    def test_fresh_proof_restores_remote_without_new_employee_login(self):
        auth,_=self.prepare();observation=copy.deepcopy(self.s['observation'])
        technician_model.invalidate(self.s)
        self.s['observation']=observation
        self.assertTrue(evaluate(self.s,'remote',self.now)['allowed'])
        self.assertEqual(ad.authentication(self.s,'client',self.now),auth)

    def test_no_directory_and_no_profiles_is_supported(self):
        s={'observation':{'at':1},'remote_session':True}
        technician_model.invalidate(s)
        self.assertIsNone(s['observation']);self.assertTrue(s['remote_session'])

if __name__=='__main__':unittest.main()
