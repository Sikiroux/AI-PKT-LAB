import copy
from types import SimpleNamespace
from unittest.mock import Mock,patch
import test_tickets as fixtures
import unittest
import timers

class WorkflowTests(unittest.TestCase):
    setUp=fixtures.TestTickets.setUp
    tearDown=fixtures.TestTickets.tearDown
    added=fixtures.TestTickets.added
    # Reuse realistic fake PT fixture, but don't rerun the parent's tests.
    def prepare(self):
        self.t.new('pc');self.added('pc');ticket=self.t.state['tickets'][0]
        self.t.action(ticket['id'],'notes',{'notes':'Poste ajouté et communication avec le serveur vérifiée.'})
        return ticket
    def test_resolve_confirm_close_rechecks_network(self):
        ticket=self.prepare();ticket['timer']=timers.configure(30,'training');timers.autostart(ticket['timer'])
        self.t.action(ticket['id'],'resolve',{})
        self.assertEqual(ticket['status'],'resolu');self.assertNotIn('closed',ticket);self.assertTrue(ticket['timer']['finished'])
        rid=ticket['resolution']['id']
        for data in ({},{'confirmation':True,'resolution_id':'old'},{'confirmation':False,'resolution_id':rid}):
            with self.assertRaises(ValueError):self.t.action(ticket['id'],'close',data)
        self.e.ok=False
        with self.assertRaises(ValueError):self.t.action(ticket['id'],'close',{'confirmation':True,'resolution_id':rid})
        self.assertEqual(ticket['status'],'resolu')
        self.e.ok=True;self.t.action(ticket['id'],'close',{'confirmation':True,'resolution_id':rid})
        self.assertEqual(ticket['status'],'clos');self.assertIn('confirmation',ticket['resolution'])
    def test_solution_required_and_failed_checks_never_resolve(self):
        ticket=self.prepare();ticket['notes']='short'
        with self.assertRaises(ValueError):self.t.action(ticket['id'],'resolve',{})
        self.t.action(ticket['id'],'followup',{'entry_kind':'solution','text':'Poste préparé ; liaison réseau supposée rétablie.'})
        self.e.ok=False
        with self.assertRaises(ValueError):self.t.action(ticket['id'],'resolve',{})
        self.assertNotEqual(ticket['status'],'resolu');self.assertNotIn('resolution',ticket)
    def test_reopen_keeps_history_invalidates_proofs_and_restarts_timer(self):
        ticket=self.prepare();ticket['timer']=timers.configure(15,'training');timers.autostart(ticket['timer'])
        self.t.action(ticket['id'],'resolve',{});previous=copy.deepcopy(ticket['resolution'])
        with self.assertRaises(ValueError):self.t.action(ticket['id'],'take',{})
        self.t.action(ticket['id'],'reopen',{'reason':'Le problème est revenu.'})
        self.assertEqual(ticket['status'],'en_cours');self.assertFalse(ticket['complete']);self.assertEqual(ticket['checks'],[])
        self.assertNotIn('resolution',ticket);self.assertNotIn('checked',ticket)
        self.assertEqual(ticket['workflow'][-1]['resolution'],previous);self.assertTrue(ticket['workflow'][-1]['timer']['finished'])
        self.assertFalse(ticket['timer']['finished']);self.assertTrue(ticket['timer']['started'])
    def test_old_ticket_close_still_compatible(self):
        ticket=self.prepare();self.t.action(ticket['id'],'close',{})
        self.assertEqual(ticket['status'],'clos')
        self.t.action(ticket['id'],'reopen',{'reason':'Nouvelle observation à vérifier.'})
        self.assertEqual(ticket['status'],'en_cours')
    def test_workspace_reopening_rejects_replaced_scenario_and_other_active(self):
        ticket={'id':'INC-APP-1','kind':'workspace','status':'clos','stage':'prepared','checks':[],'complete':True}
        self.t.state['tickets']=[ticket];state={'desktop_incident':{'id':'INC-APP-2'},'validated':True}
        self.t.controller=SimpleNamespace(workspace=SimpleNamespace(state=state,save=Mock()))
        with self.assertRaises(ValueError):self.t.action(ticket['id'],'reopen',{'reason':'Le problème revient.'})
        self.assertTrue(state['validated']);state['desktop_incident']['id']=ticket['id']
        self.t.state['tickets'].append(dict(ticket,id='INC-APP-other',status='en_cours'))
        with self.assertRaises(ValueError):self.t.action(ticket['id'],'reopen',{'reason':'Le problème revient.'})
        self.t.state['tickets'].pop();self.t.action(ticket['id'],'reopen',{'reason':'Le problème revient.'})
        self.assertFalse(state['validated']);self.t.controller.workspace.save.assert_called_once()

    def test_workspace_resolution_uses_current_checks_and_persists_pending_status(self):
        ticket={'id':'INC-AD-1','kind':'workspace','status':'en_cours','stage':'prepared','checks':[],'complete':False,'notes':'Compte corrigé et ouverture du partage vérifiée.'}
        self.t.state['tickets']=[ticket]
        state={'directory_incident':{'id':ticket['id']},'validated':False}
        workspace=SimpleNamespace(state=state,save=Mock(),public=Mock(return_value={'checks':{'read':{'allowed':True}}}))
        self.t.controller=SimpleNamespace(engine=object(),workspace=workspace,observe=Mock())
        self.t.action(ticket['id'],'resolve',{})
        self.assertEqual(ticket['status'],'resolu');self.assertTrue(state['validated'])
        self.assertEqual(self.t.controller.observe.call_count,1)
        rid=ticket['resolution']['id'];workspace.public.return_value={'checks':{'read':{'allowed':False}}}
        with self.assertRaises(ValueError):self.t.action(ticket['id'],'close',{'confirmation':True,'resolution_id':rid})
        self.assertEqual(ticket['status'],'resolu');self.assertFalse(state['validated'])
        self.assertEqual(self.t.controller.observe.call_count,2)
