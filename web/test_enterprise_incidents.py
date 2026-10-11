"""Incidents avant signalement, isolation, regroupement et réparation ciblée."""
import copy
import unittest
from unittest.mock import Mock
from pathlib import Path
from tickets_app import Tickets
from test_tickets import Fake
import test_client_workspaces as fixtures
import enterprise_incidents as live
import ticket_arrivals
import client_workspaces

class LiveTests(unittest.TestCase):
 setUp=fixtures.ClientWorkspacesTests.setUp
 proofs=fixtures.ClientWorkspacesTests.proofs
 def tickets(self):
  self.s['staff_size']=30
  t=Tickets(Fake(),Path(self.tmp.name)/'live-tickets.json');t.controller=self.c
  t.state['site']=dict(environment_id='env',devices=[]);self.c.observe=Mock();return t
 def test_network_dialogue_uses_observation_timestamp(self):
  from unittest.mock import patch
  t=self.tickets();live.receive(t,'ad',client_serial='second');ident=next(iter(self.s['live_incidents']))
  profile=self.s['client_workspaces']['second']['local']
  for status,stamp,expected in [('passed',100,'positif'),('failed',100,'échoué'),('passed',50,'récent'),('passed',102,'récent')]:
   profile['observation']=dict(at=stamp,status=status)
   with patch('enterprise_incidents.time.time',return_value=101):row=live.dialogue(self.s,ident,'network')
   self.assertIn(expected,row['answer'])
 def test_mutation_precedes_persistence_and_take_does_not_probe(self):
  t=self.tickets();live.receive(t,'ad',client_serial='second');row=t.state['tickets'][0]
  self.assertFalse(self.s['directory']['users'][self.s['client_workspaces']['second']['user_id']]['enabled'])
  self.assertEqual(row['stage'],'prepared');self.assertTrue(row['timer']['started'])
  t.action(row['id'],'take',{});self.c.observe.assert_not_called()
  self.assertEqual(row['status'],'en_cours');self.assertEqual(row['request_context']['serial'],'second')
 def test_distinct_incidents_coexist_without_overwriting(self):
  t=self.tickets();live.receive(t,'ad',client_serial='second');live.receive(t,'printing',client_serial='client')
  self.assertEqual(len(t.state['tickets']),2)
  self.assertFalse(self.s['directory']['users'][self.s['client_workspaces']['second']['user_id']]['enabled'])
  self.assertEqual({r['status'] for r in live.work_status(self.s)}, {'blocked','degraded'})
  with self.assertRaises(ValueError):live.receive(t,'dns',client_serial='second')
 def test_shared_ftp_signals_are_grouped(self):
  t=self.tickets();self.s['staff']=[dict(display_name=p['requester'],department='Opérations',activity='Traiter les commandes clients',service_dependencies=['ftp']) for p in self.s['client_workspaces'].values()];live.receive(t,'ftp');first=t.state['tickets'][0]
  self.assertFalse(self.s['desktop_services']['ftp']['service_running'])
  live.receive(t,'ftp');self.assertEqual(len(t.state['tickets']),1)
  self.assertEqual(len(first['followups']),1);self.assertEqual(first['severity'],'critique')
  self.assertEqual(first['impact']['affected_count'],2)
 def test_shared_ftp_affects_only_dependent_workflows(self):
  t=self.tickets();profiles=self.s['client_workspaces']
  self.s['staff']=[dict(display_name=p['requester'],department='Opérations' if serial=='second' else 'Accueil',activity='Activité métier',service_dependencies=['ftp'] if serial=='second' else ['files']) for serial,p in profiles.items()]
  live.receive(t,'ftp');ticket=t.state['tickets'][0]
  self.assertEqual(ticket['target_serial'],'second')
  self.assertEqual(ticket['impact']['affected_serials'],['second'])
  self.assertEqual(ticket['impact']['departments'],['Opérations'])
  self.assertEqual(ticket['impact']['evidence'],'business_dependencies')
  statuses={row['serial']:row['status'] for row in live.work_status(self.s)}
  self.assertEqual(statuses['client'],'available');self.assertEqual(statuses['second'],'degraded')
  self.s['desktop_services']['ftp']['service_running']=True
  self.assertEqual({row['status'] for row in live.work_status(self.s)},{'available'})
 def test_ftp_missing_roster_counts_only_reporter(self):
  t=self.tickets();self.s.pop('staff',None)
  live.receive(t,'ftp');ticket=t.state['tickets'][0]
  self.assertEqual(ticket['impact']['affected_serials'],[ticket['target_serial']])
  self.assertEqual(ticket['impact']['evidence'],'reported_workstation')
 def test_ftp_cannot_inject_for_a_non_dependent_reporter(self):
  t=self.tickets();self.s['staff']=[dict(display_name=p['requester'],department='Accueil',activity='Accueil',service_dependencies=[]) for p in self.s['client_workspaces'].values()]
  before=copy.deepcopy(self.s)
  with self.assertRaises(ValueError):live.receive(t,'ftp',client_serial='client')
  self.assertEqual(self.s,before)
 def test_old_open_ftp_scope_migrates_without_changing_target_or_notes(self):
  t=self.tickets();self.s.pop('staff',None);live.receive(t,'ftp');ticket=t.state['tickets'][0]
  target=ticket['target_serial'];ticket['notes']='Conserver mon diagnostic';ticket['impact'].pop('evidence')
  ticket['impact']['affected_serials']=list(self.s['client_workspaces']);ticket['impact']['affected_count']=2
  live.recover(t,self.s)
  self.assertEqual(ticket['impact']['affected_count'],1);self.assertEqual(ticket['target_serial'],target)
  self.assertEqual(ticket['notes'],'Conserver mon diagnostic')
  self.assertEqual(self.s['live_incidents'][ticket['id']]['ticket']['impact'],ticket['impact'])
  ticket['status']='clos';ticket['impact'].pop('evidence');ticket['impact']['affected_count']=2
  live.recover(t,self.s);self.assertEqual(ticket['impact']['affected_count'],2)
 def test_checks_need_repair_on_same_station_and_fresh_proof(self):
  t=self.tickets();live.receive(t,'ad',client_serial='second');row=t.state['tickets'][0]
  with self.c.client_scope('second'):self.proofs(self.c.workspace.state)
  self.assertNotEqual(live.checks(self.s,row,self.now)[0]['status'],'valide')
  self.s['directory']['users'][self.s['client_workspaces']['second']['user_id']]['enabled']=True
  self.assertEqual(live.checks(self.s,row,self.now)[0]['status'],'valide')
  self.assertNotEqual(live.checks(self.s,row,self.now+10000)[0]['status'],'valide')
 def test_close_refuses_broken_function_and_saves_correct_ticket(self):
  t=self.tickets();live.receive(t,'ad',client_serial='second');row=t.state['tickets'][0]
  with self.c.client_scope('second'):self.proofs(self.c.workspace.state)
  with self.assertRaises(ValueError):t.workspace_action(row,'close',{})
  self.assertNotEqual(row['status'],'clos')
  self.s['directory']['users'][self.s['client_workspaces']['second']['user_id']]['enabled']=True
  t.workspace_action(row,'close',{});self.assertEqual(row['status'],'clos')
  self.assertEqual(self.s['live_incidents'][row['id']]['ticket']['status'],'clos')
 def test_checkpoint_recovers_missing_ticket(self):
  t=self.tickets();live.receive(t,'ad');row=copy.deepcopy(t.state['tickets'][0]);t.state['tickets']=[]
  live.recover(t,self.s);live.recover(t,self.s);self.assertEqual(t.state['tickets'],[row])
 def test_seed_replays_selection_and_alternates_users(self):
  t=self.tickets();before=copy.deepcopy(self.s);live.receive(t);first=copy.deepcopy(t.state['tickets'][0])
  self.c.workspace.state=copy.deepcopy(before);t.state['tickets']=[];live.receive(t)
  self.assertEqual(first['target_serial'],t.state['tickets'][0]['target_serial'])
  self.assertEqual(first['live_family'],t.state['tickets'][0]['live_family'])
  live.receive(t);self.assertNotEqual(t.state['tickets'][0]['target_serial'],t.state['tickets'][1]['target_serial'])
 def test_dns_fault_is_local_and_repairable(self):
  t=self.tickets();live.receive(t,'dns',client_serial='second')
  self.assertEqual(self.s['dns_service']['clients']['client']['dns_server_ip'],self.s['devices']['server']['ip'])
  self.assertEqual(self.s['client_workspaces']['second']['dns_client']['dns_server_ip'],'192.0.2.254')
  self.assertEqual(next(r for r in live.work_status(self.s) if r['serial']=='second')['status'],'blocked')
  with self.c.client_scope('second'):
   self.c.workspace.state['dns_service']['clients']['client']['dns_server_ip']=self.s['devices']['server']['ip']
  self.assertEqual(next(r for r in live.work_status(self.s) if r['serial']=='second')['status'],'available')
 def test_other_environment_rejected_before_mutation(self):
  t=self.tickets();t.state['site']['environment_id']='other'
  before=copy.deepcopy(self.s)
  with self.assertRaises(ValueError):ticket_arrivals.receive(t)
  self.assertEqual(before,self.s)

 def test_historical_preparation_cannot_overwrite_live_pannes(self):
  t=self.tickets();live.receive(t,'ad',client_serial='second');before=copy.deepcopy(self.s)
  for method in (self.c.next_directory_incident,self.c.next_file_incident,self.c.next_dns_incident,self.c.next_desktop_incident,self.c.next_mixed_incident):
   with self.assertRaises(ValueError):method()
  self.assertEqual(before,self.s);self.c.observe.assert_not_called()


class IncidentCheckpointTests(unittest.TestCase):
 proofs=fixtures.ClientWorkspacesTests.proofs
 setUp=fixtures.ClientWorkspacesTests.setUp
 tickets=LiveTests.tickets
 def test_first_persisted_mutation_already_contains_recoverable_ticket(self):
  import json
  from unittest.mock import patch
  t=self.tickets();original=self.c.workspace.save;saved=[]
  def save():
   original()
   saved.append(json.loads(self.c.workspace.path.read_text()))
  with patch.object(self.c.workspace,'save',side_effect=save):live.receive(t,'ad',client_serial='second')
  affected=self.s['client_workspaces']['second']['user_id']
  broken=[s for s in saved if not s['directory']['users'][affected]['enabled']]
  self.assertTrue(broken)
  for state in broken:
   record=state['live_incidents']['INC-LIVE-00001']
   self.assertEqual(record['ticket']['target_serial'],'second')
   self.assertEqual(state['live_incident_count'],1)

 def test_ticket_store_failure_can_recover_without_mutating_again(self):
  from unittest.mock import patch
  t=self.tickets()
  with patch.object(t,'event',side_effect=OSError('ticket store unavailable')):
   with self.assertRaises(OSError):live.receive(t,'ad',client_serial='second')
  before=copy.deepcopy(self.s['directory']);t.state['tickets']=[]
  live.recover(t,self.s);live.recover(t,self.s)
  self.assertEqual(len(t.state['tickets']),1)
  self.assertEqual(self.s['directory'],before)
  self.assertEqual(self.s['live_incident_count'],1)

 def test_when_uses_reported_time_and_legacy_does_not_invent_it(self):
  t=self.tickets();live.receive(t,'ad',client_serial='second');record=next(iter(self.s['live_incidents'].values()))
  answer=live.dialogue(self.s,record['id'],'when')['answer']
  self.assertIn('constaté à',answer);self.assertIn('ne sais pas',answer)
  record.pop('reported_at')
  self.assertIn('pas noté',live.dialogue(self.s,record['id'],'when')['answer'])

 def test_documents_messages_distinguish_local_application_and_remote_share(self):
  from unittest.mock import patch
  for cause,expected in [('mapped_drive_wrong','dossier partagé'),('documents_missing','application Documents')]:
   self.setUp();t=self.tickets()
   with patch.object(live,'CATALOGUE',(('endpoint',cause),)):live.receive(t,'endpoint',client_serial='second')
   ticket=t.state['tickets'][0]
   self.assertIn(expected,ticket['description']);self.assertIn('fichiers locaux restent accessibles',ticket['description'])
   self.assertNotIn(cause,str(ticket))
