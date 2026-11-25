import json
from pathlib import Path
import subprocess
import unittest
from diagnostic_payloads import OK_SCRIPT,PAYLOAD_SCRIPT,CLEANUP_SCRIPT
from test_memory_diagnostic import Controller,Clock,Event
from memory_diagnostic import MemoryDiagnostic

class DiagnosticPayloadTests(unittest.TestCase):
 def test_actual_scripts_and_cleanup_in_js_runtime(self):
  code=r'''const vm=require('vm'),assert=require('assert');let input='';process.stdin.on('data',d=>input+=d);process.stdin.on('end',()=>{const p=JSON.parse(input);let answer;const ctx={reportResult:r=>answer=r};vm.createContext(ctx);vm.runInContext(p.ok,ctx);assert.equal(answer,'OK');vm.runInContext(p.payload,ctx);assert.equal(Buffer.byteLength(answer),42072);assert.equal(answer,'x'.repeat(42072));let rendered=0;ctx.S={logs:[{type:'cmd',msg:'old'},{type:'err',msg:'keep'},{type:'recv',msg:'old'}],history:['keep script'],commandCount:123};ctx.document={getElementById:()=>({querySelectorAll:()=>new Array(900)})};ctx.renderLog=()=>rendered++;ctx.$se=(name,code)=>{assert.equal(name,'runCode');vm.runInContext(code,ctx)};ctx.window={webview:{evaluateJavaScriptAsync:code=>vm.runInContext(code,ctx)}};vm.runInContext(p.cleanup,ctx);let r=JSON.parse(answer);assert(r.supported);assert.equal(r.removed,2);assert.equal(r.displayed_before,900);assert.equal(ctx.S.logs.length,1);assert.equal(ctx.S.logs[0].type,'err');assert.equal(ctx.S.history[0],'keep script');assert.equal(ctx.S.commandCount,123);assert.equal(rendered,1);delete ctx.S;vm.runInContext(p.cleanup,ctx);assert.equal(JSON.parse(answer).supported,false);});'''
  result=subprocess.run(['node','-e',code],input=json.dumps(dict(ok=OK_SCRIPT,payload=PAYLOAD_SCRIPT,cleanup=CLEANUP_SCRIPT)),text=True,capture_output=True)
  self.assertEqual(result.returncode,0,result.stderr)
 def run_mode(self,mode,supported=True,duration=3):
  c=Controller();clock=Clock();d=MemoryDiagnostic(c,clock);d.stop_event=Event(clock)
  # The instrumented real call delegates to this fake bridge response.
  original=c.engine.call
  def call(code,*args,**kwargs):
   response=original(code,*args,**kwargs)
   if code==OK_SCRIPT:return 'OK'
   if code==PAYLOAD_SCRIPT:return 'x'*42072
   if code==CLEANUP_SCRIPT:return json.dumps({'supported':supported,'removed':2})
   return response
  c.engine.call=call;d.start(mode,duration);d.thread.join(2);self.assertFalse(d.thread.is_alive());return c,d.snapshot()
 def test_fixed_modes_do_not_read_network(self):
  for mode,script in [('ok',OK_SCRIPT),('payload',PAYLOAD_SCRIPT)]:
   c,s=self.run_mode(mode);self.assertEqual(c.engine.codes,[script]*3);self.assertEqual(s['cycles'],3);self.assertEqual(s['errors'],0)
 def test_cleanup_is_bounded_and_failure_not_reported_as_success(self):
  c,s=self.run_mode('inventory_clean',duration=12);self.assertEqual(c.engine.codes.count('inventory'),12);self.assertEqual(c.engine.codes.count(CLEANUP_SCRIPT),2);self.assertEqual(sum(e['kind']=='logs_cleaned' for e in s['events']),2)
  c,s=self.run_mode('inventory_clean',False);self.assertEqual(c.engine.codes.count('inventory'),1);self.assertGreater(s['errors'],0);self.assertFalse(any(e['kind']=='logs_cleaned' for e in s['events']))
