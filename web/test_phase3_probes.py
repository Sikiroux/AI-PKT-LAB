import json,subprocess,unittest
from diagnostic_payloads import INVENTORY_PROBES
class Phase3Tests(unittest.TestCase):
 def test_native_references_retained_and_live_properties_read(self):
  js=r'''const vm=require('vm'),assert=require('assert');let input='';process.stdin.on('data',d=>input+=d);process.stdin.on('end',()=>{const scripts=JSON.parse(input);for(const mode of Object.keys(scripts)){let getters=0,reads=0,answer,ip='10.0.0.1',count=1;const own={getName:()=>{reads++;return 'PC'},getModel:()=> 'PC',getSerialNumber:()=> '1',getPortCount:()=>1,getPortAt:()=>{getters++;return port}};const far={getName:()=>{reads++;return 'SW'}};const other={getName:()=> 'Fa1',getOwnerDevice:()=>{getters++;return far}};const link={getPort1:()=>{getters++;return port},getPort2:()=>{getters++;return other}};const port={getName:()=>{reads++;return 'Fa0'},getIpAddress:()=>{reads++;return ip},getLink:()=>{getters++;return link},getOwnerDevice:()=>{getters++;return own}};const net={getDeviceCount:()=>count,getLinkCount:()=>1,getDeviceAt:()=>{getters++;return own}};const ctx=vm.createContext({ipc:{network:()=>{getters++;return net}},reportResult:v=>answer=JSON.parse(v)});const run=()=>{answer=null;vm.runInContext(scripts[mode],ctx);return answer};let a=run();assert(!a.error);assert.equal(a.cache,'built');assert.equal(a.objects,getters);assert.equal(a.cached_ports,1);const initial=getters;reads=0;ip='10.0.0.2';a=run();assert.equal(a.cache,'reused');assert.equal(a.objects,0);assert.equal(getters,initial);if(mode==='inventory_cached_all'){assert.equal(a.devices[0].ports[0].ip,ip);assert.equal(a.devices[0].ports[0].peer.device,'SW');assert(reads>0);count=2;assert(run().error.includes('Topologie'))}else{assert.equal(reads,0);assert.deepEqual(a.devices,[])}}});'''
  scripts={k:INVENTORY_PROBES[k] for k in ('inventory_cached_all','inventory_cached_hold')};p=subprocess.run(['node','-e',js],input=json.dumps(scripts),capture_output=True,text=True);self.assertEqual(p.returncode,0,p.stderr)
 def test_probe_telemetry(self):
  from test_inventory_probes import InventoryProbeTests
  for mode in ('inventory_cached_all','inventory_cached_hold'):
   c,s=InventoryProbeTests().run_probe(mode,{'devices':[],'objects':0,'cache':'reused','cached_devices':54,'cached_ports':190})
   self.assertEqual(s['errors'],0);e=next(e for e in s['events'] if e['kind']=='inventory_probe');self.assertEqual(e['cached_ports'],190);self.assertEqual(e['cached_devices'],54)

 def test_trace_runs_each_step_once_and_stops(self):
  from diagnostic_payloads import GC_TRACE_STEPS
  from test_memory_diagnostic import Controller,Clock,Event
  from memory_diagnostic import MemoryDiagnostic
  c=Controller();clock=Clock();c.engine.call=lambda code:json.dumps({'devices':[]})
  d=MemoryDiagnostic(c,clock);d.stop_event=Event(clock);d.start('inventory_gc_trace',180);d.thread.join(2)
  s=d.snapshot();self.assertEqual(s['cycles'],len(GC_TRACE_STEPS));self.assertFalse(s['running']);self.assertEqual(s['errors'],0)
  self.assertEqual([e['step'] for e in s['events'] if e['kind']=='trace_completed'],[name for name,_ in GC_TRACE_STEPS]);d.close()
 def test_diagnostic_exposes_authenticated_desktop_quit_token(self):
  from pathlib import Path
  import re
  html=Path(__file__).with_name('memory-diagnostic.html').read_text();line=next(line for line in html.splitlines() if "const TOKEN=" in line)
  js="const document={getElementById:()=>({})};"+line.replace('__UI_TOKEN__','expected-secret')+";if(TOKEN!=='expected-secret'||token!==TOKEN)throw Error('quit token mismatch');"
  p=subprocess.run(['node','-e',js],capture_output=True,text=True);self.assertEqual(p.returncode,0,p.stderr)
