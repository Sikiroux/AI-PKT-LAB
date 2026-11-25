import json, subprocess, unittest
from diagnostic_payloads import INVENTORY_PROBES
from memory_diagnostic import MemoryDiagnostic
from test_memory_diagnostic import Controller, Clock, Event
class InventoryProbeTests(unittest.TestCase):
 def test_native_read_isolation(self):
  js=r'''const vm=require('vm'),assert=require('assert');let input='';process.stdin.on('data',d=>input+=d);process.stdin.on('end',()=>{for(const [mode,script] of Object.entries(JSON.parse(input))){if(!['inventory_count','inventory_identity','inventory_ports','inventory_links'].includes(mode))continue;let seen=[],answer;function mark(n,v){seen.push(n);return v}const port={getName:()=>mark('portName','Fa0'),getLink:()=>mark('link',null),getIpAddress:()=>mark('ip','1.2.3.4')};const device={getName:()=>mark('identity','PC'),getModel:()=>mark('identity','PC'),getSerialNumber:()=>mark('identity','1'),getPortCount:()=>mark('ports',1),getPortAt:()=>mark('port',port)};const net={getDeviceCount:()=>mark('count',1),getDeviceAt:()=>mark('device',device),getLinkCount:()=>mark('linkCount',0)};vm.runInNewContext(script,{ipc:{network:()=>net},reportResult:v=>answer=JSON.parse(v)});assert(!answer.error);if(mode==='inventory_count'){assert.deepEqual(seen,['count']);assert.equal(answer.device_count,1)}else assert.equal(answer.devices.length,1);if(mode==='inventory_identity')assert(!seen.includes('ports'));if(mode==='inventory_ports'){assert(seen.includes('ip'));assert(!seen.includes('link'));assert(!seen.includes('identity'))}if(mode==='inventory_links'){assert(seen.includes('link'));assert(!seen.includes('ip'))}}});'''
  p=subprocess.run(['node','-e',js],input=json.dumps(INVENTORY_PROBES),capture_output=True,text=True);self.assertEqual(p.returncode,0,p.stderr)
 def run_probe(self,mode,response):
  c=Controller();clock=Clock()
  def call(code):c.engine.codes.append(code);return json.dumps(response)
  c.engine.call=call;d=MemoryDiagnostic(c,clock);d.stop_event=Event(clock);d.start(mode,3);d.thread.join(2);self.assertFalse(d.thread.is_alive());return c,d.snapshot()
 def test_only_selected_script_and_journal(self):
  for mode,script in INVENTORY_PROBES.items():
   c,s=self.run_probe(mode,{'device_count':54} if mode=='inventory_count' else {'devices':[{'ports':[{}]}]})
   self.assertEqual(c.engine.codes,[script]*3);self.assertEqual(s['calls'],3);self.assertEqual(s['cycles'],3);self.assertEqual(s['errors'],0);self.assertEqual(sum(e['kind']=='inventory_probe' for e in s['events']),3)
 def test_native_error_stops(self):
  c,s=self.run_probe('inventory_ports',{'error':'native failure'});self.assertEqual(len(c.engine.codes),1);self.assertEqual(s['cycles'],0);self.assertGreater(s['errors'],0)
