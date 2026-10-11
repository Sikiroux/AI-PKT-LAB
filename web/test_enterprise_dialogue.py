"""Recettes de connaissance client, ressource, retest et preuves ciblées."""
import copy
import unittest
from unittest.mock import patch
import test_client_workspaces as fixtures
import test_enterprise_incidents as incidentfixtures
import enterprise_incidents as live
import enterprise_dialogue as dialogue

class DialogueTests(unittest.TestCase):
 setUp=fixtures.ClientWorkspacesTests.setUp
 proofs=fixtures.ClientWorkspacesTests.proofs
 tickets=incidentfixtures.LiveTests.tickets
 def create(self,family='endpoint'):
  t=self.tickets();live.receive(t,family,client_serial='second')
  return t,self.s['live_incidents']['INC-LIVE-00001']
 def ask(self,record,question):return live.dialogue(self.s,record['id'],question)['answer']
 def test_families_offer_relevant_questions(self):
  self.assertNotIn('save',dialogue.questions('peripherals'))
  self.assertNotIn('ip',dialogue.questions('ad'))
  self.assertIn('attempts',dialogue.questions('printing'))
  t,r=self.create('printing');self.assertEqual(t.public()['tickets'][0]['dialogue_questions'],dialogue.questions('printing'))
 def test_scope_identifies_remote_resource_without_hidden_cause(self):
  with patch.object(live,'CATALOGUE',(('endpoint','mapped_drive_wrong'),)):t,r=self.create()
  answer=self.ask(r,'scope')
  self.assertIn('second',answer);self.assertIn('\\\\'+self.s['devices']['server']['name']+'\\Documents',answer)
  self.assertIn('fichiers locaux',answer);self.assertNotIn('AncienDossier',answer);self.assertNotIn('mapped_drive_wrong',answer)
 def test_print_scope_names_the_printer_not_a_shared_folder(self):
  t,r=self.create('printing');answer=self.ask(r,'scope')
  self.assertIn(self.s['client_workspaces']['second']['printing']['queues']['office']['name'],answer)
  self.assertNotIn('dossier partagé',answer)
 def test_history_is_stable_and_retest_records_a_new_attempt(self):
  t,r=self.create('ad');before=self.ask(r,'attempts');self.assertIn('sans succès',before)
  snapshot=copy.deepcopy(r['client_report']);self.s['directory']['users'][r['client_report']['user_id']]['enabled']=True
  self.assertEqual(self.ask(r,'attempts'),before)
  self.ask(r,'retest');self.assertEqual(len(r['client_report']['attempts']),2)
  self.assertEqual(r['client_report']['symptom'],snapshot['symptom'])
 def test_login_does_not_reveal_admin_reason(self):
  t,r=self.create('ad');answer=self.ask(r,'login')
  self.assertIn('refusée',answer);self.assertNotIn('désactiv',answer);self.assertNotIn('account_disabled',answer)
 def test_primary_proof_cannot_answer_for_secondary_station(self):
  t,r=self.create('dns');self.proofs(self.s)
  self.assertIn('pas encore',self.ask(r,'ip'))
  self.s['client_workspaces']['second']['local']['observation']=dict(probes={'share':dict(at=100,status='passed',source_device='other',target=self.s['devices']['server']['ip'])})
  with patch('enterprise_incidents.time.time',return_value=101):self.assertIn('pas encore',self.ask(r,'ip'))
 def test_save_cannot_bypass_missing_application_and_does_not_write(self):
  with patch.object(live,'CATALOGUE',(('endpoint','documents_missing'),)):t,r=self.create()
  before=copy.deepcopy(self.s['file_service'])
  answer=self.ask(r,'save');self.assertNotIn('Je peux lire',answer)
  self.assertEqual(r['client_report']['attempts'][-1]['status'],'failed');self.assertEqual(self.s['file_service'],before)
 def test_chat_does_not_mutate_services_or_probe_network(self):
  t,r=self.create('printing');before=copy.deepcopy(self.s['desktop_services'])
  for question in dialogue.questions('printing'):self.ask(r,question)
  self.assertEqual(self.s['desktop_services'],before);self.c.observe.assert_not_called()
 def test_legacy_history_does_not_invent_attempts(self):
  t,r=self.create('ad');r.pop('client_report');r.pop('reported_at')
  self.assertIn('pas détaillé',self.ask(r,'attempts'));self.assertIn('pas noté',self.ask(r,'when'))
 def test_pending_event_cannot_be_interviewed(self):
  t=self.tickets();live.receive(t,'ad',client_serial='second',discovery_delay=30)
  with self.assertRaises(ValueError):live.dialogue(self.s,'INC-LIVE-00001','scope')
 def test_changed_assignment_cannot_validate_original_users_access(self):
  t,r=self.create('ad');self.s['client_workspaces']['second']['user_id']=self.s['directory_user_id']
  self.assertIn('a changé',self.ask(r,'retest'));self.assertEqual(len(r['client_report']['attempts']),1)
 def test_history_is_bounded_and_unknown_questions_rejected(self):
  t,r=self.create('ad')
  for _ in range(65):self.ask(r,'scope')
  self.assertEqual(len(r['ticket']['dialogue']),60)
  with self.assertRaises(ValueError):self.ask(r,'invented')

 def test_dns_retest_does_not_claim_file_access(self):
  t,r=self.create('dns')
  with patch.object(live,'checks',return_value=[dict(status='valide')]):answer=self.ask(r,'retest')
  self.assertIn('encore vérifier',answer);self.assertNotIn('Je peux à nouveau ouvrir',answer)
  self.assertEqual(r['client_report']['attempts'][-1]['operation'],'retrouver le nom du serveur documentaire')
