import copy
import unittest
from types import SimpleNamespace
import ticket_learning as learning
import test_ticket_followups as fixtures
import enterprise_incidents

class LearningTests(unittest.TestCase):
 setUp=fixtures.TicketFollowupsTests.setUp
 tearDown=fixtures.TicketFollowupsTests.tearDown
 def test_hints_are_persisted_without_network_or_validation(self):
  self.app.action('T1','learning_hint',{'level':2});self.app.action('T1','learning_hint',{'level':2})
  self.assertEqual(self.ticket['learning']['hints'],[2]);self.assertFalse(self.ticket['complete']);self.assertEqual(self.ticket['status'],'nouveau')
  reloaded=type(self.app)(fixtures.NoNetwork(),self.path).public()['tickets'][0]
  self.assertEqual(reloaded['assessment']['hints'],[2])
 def test_invalid_hint_and_unknown_correction_do_not_change_ticket(self):
  before=copy.deepcopy(self.ticket)
  for payload in ({'level':True},{'level':0},{'level':4}):
   with self.assertRaises(ValueError):self.app.action('T1','learning_hint',payload)
  with self.assertRaises(ValueError):self.app.action('T1','learning_correction',{})
  self.assertEqual(self.ticket,before)
 def test_all_live_causes_have_a_correction_without_mutation(self):
  ticket=dict(id='X',target_serial='S',name='PC-01',request_context={'resource':'\\\\SRV\\Documents'})
  for family,cause in enterprise_incidents.CATALOGUE:
   s={'live_incidents':{'X':dict(target_serial='S',family=family,cause=cause,lifecycle='reported')}};before=copy.deepcopy(s)
   result=learning.correction(ticket,s);self.assertTrue(result['available'],cause);self.assertEqual(len(result['steps']),3);self.assertEqual(s,before)
 def test_replaced_target_or_hidden_event_cannot_reveal(self):
  ticket=dict(id='X',target_serial='S')
  self.assertFalse(learning.correction(ticket,{'live_incidents':{'X':dict(target_serial='OTHER',cause='account_disabled')}})['available'])
  self.assertFalse(learning.correction(ticket,{'live_incidents':{'X':dict(target_serial='S',lifecycle='awaiting_activity')}})['available'])
 def test_export_escapes_user_text_and_excludes_private_cause(self):
  self.ticket.update(title='<script>alert(1)</script>',notes='<img src=x onerror=alert(1)>',injection={'password':'SECRET'},baseline={'cause':'SECRET'})
  html=learning.export_html([self.ticket],'Demo <company>')
  self.assertIn('&lt;script&gt;',html);self.assertNotIn('<script>',html);self.assertNotIn('SECRET',html);self.assertIn('Intervention non clôturée',html)
 def test_reveal_persists_and_does_not_repair_or_complete(self):
  self.ticket.update(target_serial='S',name='PC-01')
  state={'live_incidents':{'T1':dict(target_serial='S',family='ad',cause='account_disabled',lifecycle='reported')},'directory':{'disabled':True}}
  saved=[];self.app.controller=SimpleNamespace(workspace=SimpleNamespace(state=state,save=lambda:saved.append(True)))
  self.app.action('T1','learning_correction',{})
  self.assertTrue(self.ticket['learning']['correction']['available']);self.assertTrue(state['directory']['disabled']);self.assertFalse(self.ticket['complete']);self.assertEqual(self.ticket['status'],'nouveau');self.assertTrue(saved)
  self.assertTrue(self.app.public()['tickets'][0]['assessment']['correction_viewed'])

 def test_historical_multi_layer_and_replaced_incident(self):
  import mixed_incidents
  ticket=dict(id='MIX',target_serial='S')
  for layer,causes in mixed_incidents.CATALOGUE.items():
   for cause in causes:
    s={'devices':{'client':{'serial':'S'}},'mixed_incident':dict(id='MIX',injection_state='applied',causes=[(layer,cause)])}
    self.assertTrue(learning.correction(ticket,s)['available'],(layer,cause))
    s['mixed_incident']['id']='OTHER';self.assertFalse(learning.correction(ticket,s)['available'])
 def test_pending_network_injection_has_no_correction(self):
  s={'devices':{'client':{'serial':'S'}},'mixed_incident':dict(id='MIX',injection_state='pending',causes=[('network','cable_disconnected')])}
  self.assertFalse(learning.correction(dict(id='MIX',target_serial='S'),s)['available'])
