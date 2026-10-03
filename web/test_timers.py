import tempfile,unittest,json
from pathlib import Path
from unittest.mock import patch
import timers
from tickets_app import Tickets
from test_tickets import Fake
from generator_app import Generator
class TestTimers(unittest.TestCase):
 def test_pause_resume_excludes_paused_time(self):
  t=timers.configure(30,'training');timers.operate(t,'start',100);timers.operate(t,'pause',160)
  self.assertEqual(timers.elapsed(t,999),60);timers.operate(t,'resume',1000);timers.operate(t,'finish',1060)
  self.assertEqual(t['elapsed'],120);self.assertFalse(t['exceeded'])
 def test_challenge_cannot_pause_or_restart(self):
  t=timers.configure(1,'challenge');timers.operate(t,'start',100)
  with self.assertRaises(ValueError):timers.operate(t,'pause',110)
  with self.assertRaises(ValueError):timers.operate(t,'start',120)
  timers.operate(t,'finish',200);self.assertTrue(t['exceeded'])
 def test_json_restart_keeps_deadline(self):
  t=timers.configure(1,'challenge');timers.operate(t,'start',100);t=json.loads(json.dumps(t));self.assertEqual(timers.elapsed(t,200),100)
 def test_finish_requires_start(self):
  with self.assertRaises(ValueError):timers.operate(timers.configure(15,'training'),'finish',100)
 def test_invalid_settings(self):
  for m,mode in [(-1,'training'),(1441,'training'),(20,'bad')]:
   with self.assertRaises(ValueError):timers.configure(m,mode)
 def test_ticket_timer_and_failed_close(self):
  with tempfile.TemporaryDirectory() as folder:
   path=Path(folder)/'tickets.json';e=Fake();app=Tickets(e,path);app.register();app.new('pc');t=app.state['tickets'][0]
   app.action(t['id'],'timer',dict(timer_action='configure',minutes=30,mode='training'))
   app.action(t['id'],'take',{});self.assertTrue(t['timer']['started'])
   with self.assertRaises(ValueError):app.action(t['id'],'close',{})
   self.assertFalse(t['timer']['finished']);self.assertTrue(Tickets(e,path).state['tickets'][0]['timer']['started'])
 def test_lab_timer_persists(self):
  with tempfile.TemporaryDirectory() as folder:
   g=Generator();g.root=Path(folder);ident='a'*32;(g.root/ident).mkdir();job=dict(id=ident,status='done',files=['lab.pka'],created='now');g.save(job)
   g.timer(dict(id=ident,timer_action='configure',minutes=15,mode='challenge'));g.timer(dict(id=ident,timer_action='start'))
   with self.assertRaises(ValueError):g.timer(dict(id=ident,timer_action='pause'))
   self.assertTrue(g.jobs()[0]['timer']['started'])
if __name__=='__main__':unittest.main()
