import copy
import unittest
from unittest.mock import Mock
import ticket_processing as processing
import test_tickets as fixtures
from tickets_app import Tickets

class ProcessingTests(unittest.TestCase):
    def test_matrix_all_combinations_and_justification(self):
        for i,u in enumerate(processing.LEVELS):
            for j,impact in enumerate(processing.LEVELS):
                t={};processing.set_classification(t,dict(urgency=u,impact_level=impact),'2026-01-01')
                self.assertEqual(t['severity'],processing.LEVELS[processing.MATRIX[i][j]])
        t={};before=copy.deepcopy(t)
        with self.assertRaises(ValueError):processing.set_classification(t,dict(urgency='faible',impact_level='faible',priority='critique'), 'now')
        self.assertEqual(t,before)
        processing.set_classification(t,dict(urgency='faible',impact_level='faible',priority='critique',reason='Échéance contractuelle immédiate.'),'now')
        self.assertEqual(t['classification']['source'],'manual')
    def test_legacy_no_mutation_or_auto_priority_replacement(self):
        t={'severity':'critique','impact':{'affected_count':10}};before=copy.deepcopy(t)
        result=processing.classification(t)
        self.assertEqual(result['priority'],'critique');self.assertEqual(result['source'],'legacy');self.assertEqual(t,before)
    def test_task_revision_and_cross_ticket_isolation(self):
        t={};task=processing.add_task(t,dict(text='Contrôler DNS',minutes=15),'2026-01-01')
        before=copy.deepcopy(t)
        for data in [dict(task_id=task['id'],expected_revision=1,task_status='done'),dict(task_id='other',expected_revision=0,task_status='done')]:
            with self.assertRaises(ValueError):processing.update_task(t,data,'now')
            self.assertEqual(t,before)
        processing.update_task(t,dict(task_id=task['id'],expected_revision=0,task_status='done'),'2026-01-02')
        self.assertEqual(task['revision'],1);self.assertEqual(task['status'],'done')
        processing.update_task(t,dict(task_id=task['id'],expected_revision=1,task_status='done'),'later')
        self.assertEqual(task['revision'],1)
    def test_invalid_task_never_mutates(self):
        for data in [dict(text='',minutes=0),dict(text='Test',minutes=True),dict(text='Test',minutes=-1),dict(text='Test',minutes=1441)]:
            t={}
            with self.assertRaises(ValueError):processing.add_task(t,data,'now')
            self.assertEqual(t,{})
    def test_timeline_public_excludes_internal_and_is_stable(self):
        t={'followups':[dict(date='2026-01-02',kind='followup',text='Message ancien'),dict(date='2026-01-01',kind='followup',text='Secret interne',visibility='private')], 'workflow':[dict(date='2026-01-03',previous='nouveau',status='en_cours')]}
        before=copy.deepcopy(t)
        self.assertEqual([e['text'] for e in processing.timeline(t,True)],['Message ancien'])
        self.assertEqual(processing.timeline(t)[0]['text'],'Secret interne');self.assertEqual(t,before)

class IntegrationTests(unittest.TestCase):
    setUp=fixtures.TestTickets.setUp
    tearDown=fixtures.TestTickets.tearDown
    def ticket(self):
        self.t.new('pc');return self.t.state['tickets'][0]
    def test_metadata_never_probes_and_survives_reload(self):
        t=self.ticket();self.e.snapshot=Mock(side_effect=AssertionError('No network call'))
        self.t.action(t['id'],'classify',dict(urgency='elevee',impact_level='moderee'))
        self.t.action(t['id'],'task_add',dict(text='Vérifier la configuration',minutes=10))
        self.t.action(t['id'],'followup',dict(text='Observation privée',visibility='private'))
        restored=Tickets(self.e,self.t.path)
        self.assertEqual(restored.state['tickets'][0]['tasks'],t['tasks'])
        public=self.t.public()['tickets'][0]
        self.assertEqual(public['tasks'][0]['status'],'todo');self.assertFalse(public['complete']);self.assertEqual(public['followups'][0]['visibility'],'private')
    def test_closed_and_invalid_visibility_rejected(self):
        t=self.ticket()
        for data in [dict(text='Test',visibility='other'),dict(text='Solution',entry_kind='solution',visibility='private')]:
            with self.assertRaises(ValueError):self.t.action(t['id'],'followup',data)
        t['status']='clos'
        for action,data in [('task_add',dict(text='Nouvelle tâche')),('classify',dict(urgency='faible',impact_level='faible'))]:
            with self.assertRaises(ValueError):self.t.action(t['id'],action,data)

if __name__=='__main__':unittest.main()
