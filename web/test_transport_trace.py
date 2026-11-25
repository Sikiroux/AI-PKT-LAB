import json,subprocess,time,unittest
from unittest.mock import Mock
from diagnostic import Engine
from vendor.live_bridge import PTCommandBridge

class TransportTraceTests(unittest.TestCase):
 def bridge(self):
  b=PTCommandBridge(token='test-secret');b._last_poll_time=time.time();return b
 def test_opt_in_marker_and_delivery_and_result_are_correlated(self):
  b=self.bridge();b.diagnostic_events=[];b.take_result=Mock(return_value='OK');e=Engine(b);self.assertEqual(e.call('reportResult("OK");'),'OK');commands=b.drain_commands();self.assertEqual(len(commands),1)
  rid=b.take_result.call_args.args[0]
  js=r'''const vm=require('vm'),assert=require('assert');let text='';process.stdin.on('data',v=>text+=v);process.stdin.on('end',()=>{const a=JSON.parse(text),posts=[];function X(){this.open=(m,u)=>this.url=u;this.setRequestHeader=()=>{};this.send=body=>posts.push({url:this.url,body});}const wc=vm.createContext({XMLHttpRequest:X,$se:()=>{}});vm.runInContext('window=globalThis',wc);const web={evaluateJavaScriptAsync:s=>vm.runInContext(s,wc)};vm.runInNewContext(a.code,{window:{webview:web}});posts.splice(0,posts.length,...posts.filter(p=>!p.url.endsWith('rid=netops-webview-trace')));assert.equal(posts.length,2);assert(posts[0].url.endsWith('rid='+a.rid+'-entered'));assert.equal(posts[0].body,'entered');assert(posts[1].url.endsWith('rid='+a.rid));assert.equal(posts[1].body,'OK');});'''
  p=subprocess.run(['node','-e',js],input=json.dumps({'code':commands[0],'rid':rid}),capture_output=True,text=True);self.assertEqual(p.returncode,0,p.stderr)
  b.put_result(rid+'-entered','entered');b.put_result(rid,'OK');s=b.diagnostic_snapshot();self.assertEqual(s['queued_commands'],0);self.assertEqual([x['kind'] for x in s['events']],['queued','call_finished','dequeued_for_http','result_received','result_received']);self.assertNotIn('test-secret',json.dumps(s));self.assertNotIn('reportResult',json.dumps(s))
 def test_normal_engine_has_no_extra_marker(self):
  b=self.bridge();b.take_result=Mock(return_value='OK');Engine(b).call('reportResult("OK");');self.assertNotIn('__netopsEntered',b.drain_commands()[0]);self.assertIsNone(b.diagnostic_events)
 def test_trace_is_bounded(self):
  b=self.bridge();b.diagnostic_events=[]
  for i in range(400):b.diagnostic_record('test',rid=str(i))
  self.assertEqual(len(b.diagnostic_snapshot()['events']),200)
 def test_webview_boundaries_preserve_calls_and_install_once(self):
  from webview_trace import SCRIPT
  code=SCRIPT.replace('__TRACE_URL__',json.dumps('http://127.0.0.1/result'))
  js=r'''const vm=require('vm'),assert=require('assert');let text='';process.stdin.on('data',d=>text+=d);process.stdin.on('end',()=>{let posts=[],calls=0;function X(){this.handlers={};}X.prototype.open=function(m,u){this.url=u};X.prototype.setRequestHeader=function(){};X.prototype.addEventListener=function(n,f){this.handlers[n]=f};X.prototype.send=function(b){if(this.url.endsWith('/result'))posts.push(JSON.parse(b))};const c=vm.createContext({XMLHttpRequest:X,$se:(name,arg)=>{calls++;if(arg==='fail')throw Error('native error');return 42;}});vm.runInContext('window=globalThis',c);vm.runInContext(text,c);vm.runInContext(text,c);assert.equal(posts.filter(p=>p.stage==='installed').length,1);assert.equal(vm.runInContext('$se("runCode","ok")',c),42);assert.throws(()=>vm.runInContext('$se("runCode","fail")',c));assert.equal(calls,2);assert.equal(posts.filter(p=>p.stage==='runCode_enter').length,2);assert.equal(posts.filter(p=>p.stage==='runCode_return').length,1);assert.equal(posts.filter(p=>p.stage==='runCode_throw').length,1);const x=new c.XMLHttpRequest();x.open('GET','/next');x.send();x.handlers.timeout();assert.equal(posts.at(-1).stage,'next_timeout');});'''
  p=subprocess.run(['node','-e',js],input=code,capture_output=True,text=True);self.assertEqual(p.returncode,0,p.stderr)
 def test_webview_trace_does_not_export_exception_text(self):
  b=self.bridge();b.diagnostic_events=[];b.put_result('netops-webview-trace',json.dumps({'stage':'runCode_throw','info':'sensitive-code-test-secret'}));out=json.dumps(b.diagnostic_snapshot());self.assertIn('runCode_throw',out);self.assertNotIn('sensitive-code',out);self.assertNotIn('test-secret',out)
 def test_light_profile_has_no_extra_native_marker_or_installation(self):
  b=self.bridge();b.diagnostic_events=[];b.diagnostic_light_trace=True;b.take_result=Mock(return_value='OK');Engine(b).call('reportResult("OK");');code=b.drain_commands()[0]
  self.assertNotIn('__netopsEntered',code);self.assertNotIn('__netopsWebTrace',code);self.assertEqual(b.diagnostic_snapshot()['events'][0]['kind'],'queued')
