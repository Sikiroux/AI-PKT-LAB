import json,threading,tempfile,unittest,os
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch,Mock
from memory_suite import MemorySuite
class SuiteTests(unittest.TestCase):
 def diag(self):return SimpleNamespace(controller=SimpleNamespace(engine=SimpleNamespace(lock=threading.Lock(),bridge=SimpleNamespace(is_connected=True))),snapshot=lambda:{'running':False},stop=Mock())
 def test_sequence_copies_and_export(self):
  with tempfile.TemporaryDirectory() as folder:
   parent_gc=os.environ.get('QV4_MM_AGGRESSIVE_GC');root=Path(folder);base=root/'source.pkt';base.write_bytes(b'original');d=self.diag();s=MemorySuite(d,root);s.data.update(running=True,report_file=str(root/'report.json'));clock=[0];launches=[]
   def launch(args,**kwargs):
    self.assertEqual(kwargs['env']['QV4_MM_AGGRESSIVE_GC'],'1');launches.append(args);return SimpleNamespace(pid=100+len(launches),poll=lambda:None)
   d.controller.engine.call=lambda code:json.dumps({'file':launches[-1][1],'devices':54});d.start=Mock();d.thread=SimpleNamespace(join=Mock())
   def wait(n):clock[0]+=n;return True
   s._wait=wait;s._close_owned=Mock();s._memory_guard=Mock()
   with patch('memory_suite.MODES',('pause','inventory_cached_ports')),patch('memory_suite.read_packet_tracer_memory',return_value={'processes':[]}),patch('memory_suite.subprocess.Popen',side_effect=launch),patch('memory_suite.time.monotonic',side_effect=lambda:clock[0]):s.run(Path('PacketTracer.exe'),base,root)
   self.assertEqual(os.environ.get('QV4_MM_AGGRESSIVE_GC'),parent_gc);self.assertEqual(len(launches),2);self.assertNotEqual(launches[0][1],launches[1][1]);self.assertEqual(base.read_bytes(),b'original');self.assertEqual(s.data['phase'],'completed');self.assertEqual(len(json.loads((root/'report.json').read_text())['runs']),2);self.assertEqual(d.start.call_count,2);self.assertEqual(s.data['runs'][0]['process_environment'],{'QV4_MM_AGGRESSIVE_GC':'1'})
 def test_cap_and_unavailable(self):
  s=MemorySuite(self.diag(),'.')
  for v in ({'available':False,'reason':'denied'},{'available':True,'processes':[{'private_bytes':2*1024**3}]}):
   with patch('memory_suite.read_packet_tracer_memory',return_value=v):
    with self.assertRaises(RuntimeError):s._memory_guard()
 def test_only_owned_pid_is_closed(self):
  s=MemorySuite(self.diag(),'.');s.process=SimpleNamespace(pid=123,poll=lambda:None,wait=Mock())
  with patch('memory_suite.subprocess.run') as run:s._close_owned();self.assertEqual(run.call_args.args[0],['taskkill','/PID','123','/T','/F'])
  with patch('memory_suite.subprocess.run') as run:s._close_owned();run.assert_not_called()
 def test_cancel(self):
  d=self.diag();s=MemorySuite(d,'.');s.stop();self.assertTrue(s.cancel.is_set());d.stop.assert_called_once()

 def test_default_plan_contains_only_new_tests_in_priority_order(self):
  from memory_suite import MODES
  expected=('inventory_cached_all',)
  self.assertEqual(MODES,expected)
  self.assertEqual(MemorySuite(self.diag(),'.').snapshot()['plan'],list(expected))

class MemorySummaryTests(unittest.TestCase):
 def test_separates_initial_growth_from_later_slope(self):
  from memory_suite import memory_summary
  def sample(t,n,phase='test'):return {'elapsed':t,'phase':phase,'processes':[{'pid':7,'private_bytes':n}]}
  d={'memory_after_initial_inventory':sample(1,110),'process_memory':{'samples':[sample(0,100),sample(30,120),sample(90,180),sample(180,190,'after')]},'object_retrievals':655}
  s=memory_summary(d)['per_process'][0];self.assertEqual(s['initial_acquisition_private_bytes'],10);self.assertEqual(s['repeated_reads_private_bytes'],70);self.assertEqual(s['slope_after_30s_bytes_per_minute'],60);self.assertEqual(s['final_private_bytes'],190)
 def test_ten_minute_cached_test_keeps_first_events_and_setup(self):
  import json
  from test_memory_diagnostic import Controller,Clock,Event
  from memory_diagnostic import MemoryDiagnostic
  c=Controller();clock=Clock();calls=[0]
  def call(code):
   calls[0]+=1
   return json.dumps({'devices':[{'name':'PC','ports':[{'ip':'10.0.0.1' if calls[0]<100 else '10.0.0.2'}]}],'objects':655 if calls[0]==1 else 0,'cache':'built' if calls[0]==1 else 'reused'})
  c.engine.call=call;d=MemoryDiagnostic(c,clock);d.stop_event=Event(clock);d.start('inventory_cached_all',600);d.thread.join(3);s=d.snapshot();self.assertFalse(d.thread.is_alive());self.assertEqual(s['cycles'],600);self.assertEqual(s['object_retrievals'],655);self.assertEqual(s['value_changes'],1);self.assertEqual(s['events'][0]['kind'],'bridge_call');self.assertIn('memory_after_initial_inventory',s);d.close()

class FailureReportingTests(unittest.TestCase):
 def test_failed_trial_never_reports_completed(self):
  with tempfile.TemporaryDirectory() as folder:
   root=Path(folder);base=root/'source.pkt';base.write_bytes(b'x');clock=[0];launched=[]
   d=SuiteTests().diag();d.snapshot=lambda:{'running':False,'errors':1,'error':'timeout expérimental'};d.start=Mock();d.thread=SimpleNamespace(join=Mock());s=MemorySuite(d,root)
   def launch(args,**kw):launched.append(args);return SimpleNamespace(poll=lambda:None,pid=5)
   d.controller.engine.call=lambda code:json.dumps({'file':launched[-1][1]})
   def wait(n):clock[0]+=n;return True
   s._wait=wait;s._close_owned=Mock();s._memory_guard=Mock()
   with patch('memory_suite.read_packet_tracer_memory',return_value={'processes':[]}),patch('memory_suite.subprocess.Popen',side_effect=launch),patch('memory_suite.time.monotonic',side_effect=lambda:clock[0]):s.run(Path('pt.exe'),base,root)
   self.assertEqual(s.data['phase'],'error');self.assertEqual(s.data['error'],'timeout expérimental');self.assertEqual(s.data['runs'][0]['status'],'failed');self.assertEqual(s.data['runs'][0]['call_timeout_seconds'],60);self.assertIsNone(d.call_timeout)
 def test_timeout_scoped_and_one_failure_count(self):
  from memory_diagnostic import MemoryDiagnostic
  from test_memory_diagnostic import Controller
  c=Controller();original=Mock(side_effect=RuntimeError('test timeout'));c.engine.call=original;d=MemoryDiagnostic(c);d.call_timeout=90
  with self.assertRaises(RuntimeError):c.engine.call('read')
  original.assert_called_once_with('read',timeout=90)
  d.record('run_error',error='test timeout');self.assertEqual(d.snapshot()['errors'],1);self.assertEqual(d.snapshot()['error'],'test timeout');d.close()

class ProfileTimingTests(unittest.TestCase):
 def test_first_call_excluded_from_repeated_latency(self):
  from memory_suite import memory_summary
  s=memory_summary({'events':[{'kind':'bridge_call','seconds':8},{'kind':'bridge_call','seconds':2},{'kind':'bridge_call','seconds':4}]})['command_timing']
  self.assertEqual(s['initial_seconds'],8);self.assertEqual(s['repeated_mean_seconds'],3);self.assertEqual(s['repeated_median_seconds'],3);self.assertEqual(s['repeated_max_seconds'],4)
 def test_profile_requires_exclusive_channel_and_quiets_native_trace(self):
  with tempfile.TemporaryDirectory() as folder:
   root=Path(folder);base=root/'source.pkt';base.write_bytes(b'x');clock=[0];launched=[];scripts=[]
   d=SuiteTests().diag();b=d.controller.engine.bridge;b.diagnostic_snapshot=lambda:{};b.diagnostic_poll_lease=False
   d.start=Mock();d.thread=SimpleNamespace(join=Mock());s=MemorySuite(d,root)
   def call(script):
    scripts.append(script)
    if 'getSavedFilename' in script:b.diagnostic_poll_lease=True;return json.dumps({'file':launched[-1][1]})
    return 'ready'
   d.controller.engine.call=call
   def launch(args,**kw):launched.append(args);return SimpleNamespace(poll=lambda:None,pid=5)
   def wait(n):clock[0]+=n;return True
   s._wait=wait;s._close_owned=Mock();s._memory_guard=Mock()
   with patch('memory_suite.read_packet_tracer_memory',return_value={'processes':[]}),patch('memory_suite.subprocess.Popen',side_effect=launch),patch('memory_suite.time.monotonic',side_effect=lambda:clock[0]):s.run(Path('pt.exe'),base,root)
   self.assertEqual(s.data['phase'],'completed');self.assertTrue(b.diagnostic_light_trace);self.assertIn('__netopsTraceQuiet=true',scripts[1]);d.start.assert_called_once_with('inventory_cached_all',duration=600)

class NativeCaptureTests(unittest.TestCase):
 def test_capture_disables_aggressive_gc_without_changing_parent(self):
  from memory_suite import packet_tracer_environment
  with patch.dict(os.environ,{'QV4_MM_AGGRESSIVE_GC':'1'}):
   self.assertNotIn('QV4_MM_AGGRESSIVE_GC',packet_tracer_environment(True))
   self.assertEqual(os.environ['QV4_MM_AGGRESSIVE_GC'],'1')
 def test_capture_workload_is_three_minutes(self):
  with patch.dict(os.environ,{'NETOPS_NATIVE_MEMORY_PROFILE':'1'}):
   s=MemorySuite(SuiteTests().diag(),'.');self.assertEqual(s.data['limits']['test_seconds'],180);self.assertEqual(s.data['experiment'],'native_heap_capture')
