import copy
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock
from tickets_app import Tickets
import messaging
import ticket_processing

class MessagingTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
  self.t=Tickets(Mock(),Path(self.tmp.name)/'tickets.json')
  self.t.state['site']=dict(environment_id='env',devices=[])
  self.row=dict(id='INC-LIVE-1',kind='workspace',live_incident=True,stage='prepared',status='en_cours',name='PC-01',request_context=dict(requester='Alice'),dialogue_questions={'scope':'Quel poste ?'},dialogue=[dict(at=100,question='Quel poste ?',answer='PC-01',speaker='Alice')])
  self.t.state['tickets']=[self.row];self.t.controller=Mock()
 def op(self,operation,**kwargs):return messaging.operate(self.t,dict(ticket_id=self.row['id'],operation=operation,**kwargs))
 def test_projection_no_fault_and_no_mutation(self):
  self.row['baseline']={'hidden':'secret'};before=copy.deepcopy(self.t.state)
  channel=messaging.channels(self.t)['channels'][0]
  self.assertEqual(channel['requester'],'Alice');self.assertEqual(channel['unread'],1)
  self.assertNotIn('baseline',str(channel));self.assertEqual(before,self.t.state)
 def test_read_tracks_messages_after_rolling_history(self):
  key=messaging.channels(self.t)['channels'][0]['messages'][0]['key'];self.op('read',keys=[key])
  self.row['dialogue']=[dict(at=101,question='Autre question',answer='Autre réponse')]
  self.assertEqual(messaging.channels(self.t)['channels'][0]['unread'],1)
  with self.assertRaises(ValueError):self.op('read',keys=[key])
 def test_explicit_export_is_private_and_idempotent(self):
  self.assertFalse(any(e['kind']=='dialogue' for e in ticket_processing.timeline(self.row)))
  key=messaging.channels(self.t)['channels'][0]['messages'][0]['key'];self.op('export',key=key);self.op('export',key=key)
  self.assertEqual(len(self.row['followups']),1);self.assertEqual(self.row['followups'][0]['visibility'],'private')
  self.assertIn('PC-01',self.row['followups'][0]['text'])
  self.assertTrue(messaging.channels(self.t)['channels'][0]['messages'][0]['exported'])
 def test_closed_and_invalid_questions_never_call_model(self):
  with self.assertRaises(ValueError):self.op('ask',question='hidden-cause')
  self.row['status']='clos'
  with self.assertRaises(ValueError):self.op('ask',question='scope')
  self.t.controller.dialogue.assert_not_called()
 def test_valid_question_and_pin_persist(self):
  self.op('ask',question='scope');self.t.controller.dialogue.assert_called_once_with(dict(ticket_id=self.row['id'],question='scope'))
  self.op('pin',pinned=True)
  saved=Tickets(Mock(),self.t.path);self.assertTrue(messaging.channels(saved)['channels'][0]['pinned'])
 def test_stale_export_and_closed_ticket_refused(self):
  with self.assertRaises(ValueError):self.op('export',key='stale')
  self.row['status']='clos';key=messaging.channels(self.t)['channels'][0]['messages'][0]['key']
  with self.assertRaises(ValueError):self.op('export',key=key)
  self.assertNotIn('followups',self.row)

class MessagingEngineIntegrationTests(unittest.TestCase):
 def test_live_reply_reaches_chat_and_explicit_note_only(self):
  from test_client_workspaces import ClientWorkspacesTests
  import enterprise_incidents
  fixture=ClientWorkspacesTests();fixture.setUp();self.addCleanup(fixture.doCleanups)
  c=fixture.c;s=fixture.s;s['staff_size']=30
  tickets=Tickets(Mock(),Path(fixture.tmp.name)/'chat-integration.json');tickets.controller=c
  tickets.state['site']=dict(environment_id='env',devices=[])
  c.on_change=lambda state,folder:tickets.append_workspace_incident(state)
  enterprise_incidents.receive(tickets,'endpoint',client_serial='second')
  ident=tickets.state['tickets'][0]['id']
  result=messaging.operate(tickets,dict(ticket_id=ident,operation='ask',question='scope'))
  channel=next(ch for ch in result['channels'] if ch['id']==ident)
  self.assertEqual(len(channel['messages']),1)
  self.assertIn('second',channel['messages'][0]['answer'])
  ticket=tickets.get(ident)
  self.assertFalse(any(e['kind']=='dialogue' for e in ticket_processing.timeline(ticket)))
  messaging.operate(tickets,dict(ticket_id=ident,operation='export',key=channel['messages'][0]['key']))
  self.assertEqual(len(ticket['followups']),1)
  self.assertEqual(ticket['followups'][0]['visibility'],'private')
