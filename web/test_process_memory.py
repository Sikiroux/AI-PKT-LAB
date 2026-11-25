import unittest
from process_memory import ProcessMemoryMonitor
from test_memory_diagnostic import Clock
class ProcessMemoryTests(unittest.TestCase):
 def test_baseline_end_followup_and_export_copy(self):
  clock=Clock();values=iter([100,150,120]);m=ProcessMemoryMonitor(lambda:{'available':True,'processes':[{'pid':1,'working_set_bytes':next(values),'private_bytes':200}]},clock,False)
  m.begin();clock.at=180;m.finish();clock.at=240;m.sample();s=m.snapshot()['samples'];self.assertEqual([v['phase'] for v in s],['test','after','after']);self.assertEqual([v['elapsed'] for v in s],[0,180,240]);s.clear();self.assertEqual(len(m.snapshot()['samples']),3);m.close()
 def test_failure_is_unavailable_not_zero_ram(self):
  def fail():raise OSError('access denied')
  m=ProcessMemoryMonitor(fail,background=False);m.begin();s=m.snapshot()['samples'][0];self.assertFalse(s['available']);self.assertIn('access denied',s['reason']);self.assertNotIn('processes',s);m.close()

class NativeCounterTests(unittest.TestCase):
 def test_ex2_private_resident_is_separate_from_commit(self):
  import ctypes
  from process_memory import query_memory,CountersEx2
  def api(handle,ptr,size):
   c=ctypes.cast(ptr,ctypes.POINTER(CountersEx2)).contents;c.WorkingSetSize=800;c.PrivateUsage=900;c.PrivateWorkingSetSize=560;return True
  r=query_memory(api,1);self.assertEqual(r['private_working_set_bytes'],560);self.assertEqual(r['working_set_bytes'],800);self.assertEqual(r['private_bytes'],900)
 def test_older_windows_does_not_substitute_wrong_metric(self):
  import ctypes
  from process_memory import query_memory,Counters,CountersEx2
  calls=[]
  def api(handle,ptr,size):
   calls.append(size)
   if size==ctypes.sizeof(CountersEx2):return False
   c=ctypes.cast(ptr,ctypes.POINTER(Counters)).contents;c.WorkingSetSize=800;c.PrivateUsage=900;return True
  r=query_memory(api,1);self.assertEqual(len(calls),2);self.assertIsNone(r['private_working_set_bytes']);self.assertEqual(r['working_set_bytes'],800)
 def test_unfilled_ex2_field_is_unavailable(self):
  import ctypes
  from process_memory import query_memory,CountersEx2
  def api(handle,ptr,size):
   c=ctypes.cast(ptr,ctypes.POINTER(CountersEx2)).contents;c.WorkingSetSize=800;return True
  self.assertIsNone(query_memory(api,1)['private_working_set_bytes'])
 def test_access_failure(self):
  from process_memory import query_memory
  self.assertIsNone(query_memory(lambda *args:False,1))
 def test_actual_ui_keeps_processes_separate(self):
  from pathlib import Path
  import subprocess
  s=Path(__file__).with_name('memory-diagnostic.html').read_text();code=s[s.index('function memoryText('):s.index('function draw(')]
  code+="""
const assert=require('assert');const process=(pid,n)=>({pid,name:'PacketTracer.exe',private_working_set_bytes:n*1048576,working_set_bytes:800*1048576,private_bytes:900*1048576});
const first={elapsed:0,available:true,processes:[process(1,550),process(2,270)]};
const current={elapsed:10,available:true,processes:[process(1,560),process(2,275)]};
let text=memoryText([first,current]);assert(text.includes('560.0 Mo'));assert(text.includes('275.0 Mo'));assert(!text.includes('835.0 Mo'));assert(text.includes('10.0 Mo'));assert(text.includes('5.0 Mo'));assert(text.includes('PID 1'));assert(text.includes('PID 2'));
current.processes=[process(3,500)];text=memoryText([first,current]);assert(text.includes('Nouveau PID'));assert(text.includes('a disparu'));assert(!text.includes('Écart depuis'));
current.processes[0].private_working_set_bytes=null;assert(memoryText([first,current]).includes('indisponible'));
"""
  p=subprocess.run(['node','-e',code],capture_output=True,text=True);self.assertEqual(p.returncode,0,p.stderr)
