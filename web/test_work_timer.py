import unittest
from unittest.mock import patch
import timers
import test_tickets as fixtures

class WorkTimerTests(unittest.TestCase):
 def test_elapsed_starts_at_take_and_excludes_waiting_and_closed_time(self):
  ticket={'timer':{'elapsed':0,'running_since':0}}
  timers.track_work(ticket,'wait',100);self.assertNotIn('work_timer',ticket)
  timers.track_work(ticket,'take',100);timers.track_work(ticket,'take',110)
  timers.track_work(ticket,'wait',130);self.assertEqual(ticket['work_timer']['elapsed'],30)
  timers.track_work(ticket,'take',200);timers.track_work(ticket,'close',220)
  self.assertEqual(ticket['work_timer']['elapsed'],50)
  timers.track_work(ticket,'resolve',300);self.assertEqual(ticket['work_timer']['elapsed'],50)
  timers.track_work(ticket,'reopen',400);timers.track_work(ticket,'wait',410)
  self.assertEqual(ticket['work_timer']['elapsed'],60)
  self.assertEqual(ticket['timer'],{'elapsed':0,'running_since':0})
 def test_successful_actions_persist_work_time_but_refusals_do_not(self):
  # Explicit integration fixture avoids importing an additional test suite.
  import tempfile
  from pathlib import Path
  from tickets_app import Tickets
  with tempfile.TemporaryDirectory() as folder:
   t=Tickets(fixtures.Fake(),Path(folder)/'state.json');t.register();t.new('incident');ticket=t.state['tickets'][-1]
   with patch('timers.time.time',return_value=100):result=t.action(ticket['id'],'take',{})
   self.assertEqual(result['tickets'][-1]['work_timer']['running_since'],100)
   with patch('timers.time.time',return_value=125):t.action(ticket['id'],'wait',{})
   self.assertEqual(ticket['work_timer']['elapsed'],25)
   before=dict(ticket['work_timer'])
   with self.assertRaises(ValueError):t.action(ticket['id'],'close',{})
   self.assertEqual(ticket['work_timer'],before)
   restored=Tickets(fixtures.Fake(),Path(folder)/'state.json')
   self.assertEqual(restored.state['tickets'][-1]['work_timer'],before)
