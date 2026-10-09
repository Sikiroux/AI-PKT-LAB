import copy
import tempfile
import unittest
from pathlib import Path
from tickets_app import Tickets

class NoNetwork:
    def __getattr__(self,key):
        raise AssertionError('Unexpected bridge call: '+key)

class TicketFollowupsTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.path=Path(self.tmp.name)/'tickets.json'
        self.app=Tickets(NoNetwork(),self.path)
        self.ticket={'id':'T1','kind':'workspace','status':'nouveau','stage':'prepared','complete':False,'notes':'Ancienne note','checks':[]}
        self.app.state['tickets']=[self.ticket]
    def tearDown(self):self.tmp.cleanup()
    def test_legacy_take_assigns_once_and_followup_persists_without_network(self):
        self.app.action('T1','take',{})
        self.app.action('T1','followup',{'text':' Observation du client ', 'author':'Forged', 'date':'Forged'})
        self.app.action('T1','notes',{'notes':'Nouvelle synthèse'})
        saved=Tickets(NoNetwork(),self.path).public()['tickets'][0]
        self.assertEqual(saved['assigned_to'],'Technicien de la session')
        self.assertEqual(saved['followups'][0]['text'],'Observation du client')
        self.assertEqual(saved['followups'][0]['author'],'Technicien de la session')
        self.assertNotEqual(saved['followups'][0]['date'],'Forged')
        self.assertEqual(saved['notes'],'Nouvelle synthèse')
        self.assertFalse(saved['complete'])
    def test_solution_does_not_validate_close_or_modify_prior_entries(self):
        self.app.action('T1','followup',{'text':'Vérification en cours'})
        first=copy.deepcopy(self.ticket['followups'][0])
        self.app.action('T1','followup',{'entry_kind':'solution','text':'Câble reconnecté ; test du fichier à faire.'})
        self.assertEqual(self.ticket['followups'][0],first)
        self.assertEqual([e['id'] for e in self.ticket['followups']],[1,2])
        self.assertEqual(self.ticket['status'],'nouveau')
        self.assertFalse(self.ticket['complete'])
        self.assertNotIn('checked',self.ticket)
    def test_invalid_input_and_closed_ticket_do_not_mutate(self):
        for data in ({'text':' '},{'text':2},{'text':'x'*2001},{'entry_kind':'bogus','text':'test'}):
            before=copy.deepcopy(self.app.state)
            with self.assertRaises(ValueError):self.app.action('T1','followup',data)
            self.assertEqual(self.app.state,before)
        self.ticket['status']='clos'
        with self.assertRaises(ValueError):self.app.action('T1','followup',{'text':'edit closed'})
        self.assertNotIn('followups',self.ticket)
    def test_failed_close_is_still_refused_after_solution(self):
        self.app.action('T1','followup',{'entry_kind':'solution','text':'Je pense avoir corrigé.'})
        self.ticket['stage']='queued'
        with self.assertRaises(ValueError):self.app.action('T1','close',{})
        self.assertNotEqual(self.ticket['status'],'clos')
