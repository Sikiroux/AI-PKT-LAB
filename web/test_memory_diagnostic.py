import threading
import unittest
from types import SimpleNamespace
from memory_diagnostic import MemoryDiagnostic

class Clock:
 def __init__(self):self.at=0
 def __call__(self):return self.at
class Event:
 def __init__(self,clock):self.clock=clock;self.flag=False
 def clear(self):self.flag=False
 def set(self):self.flag=True
 def is_set(self):return self.flag
 def wait(self,seconds):self.clock.at+=seconds;return self.flag
class Engine:
 def __init__(self):self.lock=threading.Lock();self.codes=[];self.fail=False
 def call(self,code,*args,**kwargs):
  self.codes.append(code)
  if self.fail:raise RuntimeError('bridge absent')
  return '{}'
 def snapshot(self):self.call('inventory');return {'devices':[{'name':'PC1'}]}
 def quiet_pings(self,pairs,accelerate=False):self.call('pings');return [{'status':'valide'} for _ in pairs]
class Controller:
 def __init__(self):
  self.lock=threading.RLock();self.engine=Engine();self.workspace=SimpleNamespace(state={'environment_id':'A','devices':{k:{'ip':'192.0.2.1'} for k in ('client','technician','server')}})
 def identities(self,snapshot,partial=False):return {k:{'name':k} for k in ('client','technician','server')}
 def observe(self):self.engine.snapshot();self.engine.quiet_pings([('a','192.0.2.1')])
class MemoryDiagnosticTests(unittest.TestCase):
 def run_mode(self,mode,fail=False):
  c=Controller();clock=Clock();d=MemoryDiagnostic(c,clock);d.stop_event=Event(clock);c.engine.fail=fail;d.start(mode,3);d.thread.join(2);self.assertFalse(d.thread.is_alive());return c,d,d.snapshot()
 def test_idle_and_pause_make_no_calls(self):
  c=Controller();d=MemoryDiagnostic(c);self.assertEqual(c.engine.codes,[])
  c,d,s=self.run_mode('pause');self.assertEqual(s['calls'],0);self.assertFalse(s['running']);self.assertGreaterEqual(s['elapsed'],3)
 def test_inventory_never_pings_and_stops_at_deadline(self):
  c,d,s=self.run_mode('inventory');self.assertEqual(c.engine.codes,['inventory']*3);self.assertEqual(s['calls'],3);self.assertEqual(s['cycles'],3)
 def test_pings_inventory_only_once(self):
  c,d,s=self.run_mode('pings');self.assertEqual(c.engine.codes,['inventory','pings','pings','pings']);self.assertEqual(s['calls'],4);self.assertEqual(sum(e['kind']=='setup_inventory' for e in s['events']),1)
 def test_full_and_error_reporting(self):
  c,d,s=self.run_mode('full');self.assertEqual(s['calls'],6)
  c,d,s=self.run_mode('inventory',True);self.assertFalse(s['running']);self.assertGreater(s['errors'],0);self.assertEqual(s['cycles'],0)
 def test_export_is_copy_and_log_bounded(self):
  c,d,s=self.run_mode('inventory');s['events'].clear();self.assertTrue(d.snapshot()['events'])
  for i in range(1100):d.record('test')
  self.assertEqual(len(d.snapshot()['events']),1000)
 def test_stop_and_no_overlapping_runs(self):
  c=Controller();entered=threading.Event();release=threading.Event()
  def call(code,*args,**kwargs):entered.set();release.wait(2);return '{}'
  c.engine.call=call;d=MemoryDiagnostic(c);d.start('inventory',2);self.assertTrue(entered.wait(1))
  with self.assertRaises(ValueError):d.start('pings')
  self.assertEqual(d.stop()['phase'],'stopping');release.set();d.thread.join(2);self.assertEqual(d.snapshot()['calls'],1);self.assertFalse(d.snapshot()['running'])
 def test_validation(self):
  d=MemoryDiagnostic(Controller())
  for mode,duration in [('bad',180),('full',181),('full',True)]:
   with self.assertRaises(ValueError):d.start(mode,duration)
