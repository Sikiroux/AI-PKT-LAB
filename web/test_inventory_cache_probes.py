import json, subprocess, unittest
from diagnostic_payloads import INVENTORY_PROBES, REPEAT_OBJECTS

JS = r'''
const vm=require('vm'),assert=require('assert');let input='';
process.stdin.on('data',d=>input+=d);process.stdin.on('end',()=>{
 const P=JSON.parse(input);
 function world(){
  const w={calls:{},devices:1,links:0,linked:true};
  const mark=(n,v)=>{w.calls[n]=(w.calls[n]||0)+1;return v};
  const link={};
  const port={getName:()=>mark('portName','Fa0'),getIpAddress:()=>mark('ip','10.0.0.2'),getSubnetMask:()=>'255.255.255.0',getLink:()=>mark('getLink',w.linked?link:null)};
  const device={getName:()=>'PC',getPortCount:()=>mark('getPortCount',1),getPortAt:()=>mark('getPortAt',port)};
  const net={getDeviceCount:()=>mark('getDeviceCount',w.devices),getLinkCount:()=>w.links,getDeviceAt:()=>mark('getDeviceAt',device)};
  w.ctx=vm.createContext({ipc:{network:()=>net},reportResult:v=>w.answer=JSON.parse(v)});
  w.run=code=>{w.calls={};vm.runInContext(code,w.ctx);assert(!w.answer.error,w.answer.error);return w.answer};
  return w;
 }
 // E: the same device is retrieved REPEAT times, nothing else is read.
 let w=world(),a=w.run(P.repeat);assert.equal(a.objects,P.n);assert.equal(w.calls.getDeviceAt,P.n);assert(!w.calls.getPortAt);
 // F: first call builds the cache, the next ones reuse it without new retrievals.
 w=world();a=w.run(P.cached);assert.equal(a.cache,'built');assert.equal(a.objects,2);assert.equal(a.devices[0].ports[0].ip,'10.0.0.2');
 a=w.run(P.cached);assert.equal(a.cache,'reused');assert.equal(a.objects,0);assert(!w.calls.getDeviceAt);assert(!w.calls.getPortAt);assert.equal(w.calls.ip,1);
 w.devices=2;a=w.run(P.cached);assert.equal(a.cache,'built');assert.equal(a.devices.length,2);
 w.links=1;a=w.run(P.cached);assert.equal(a.cache,'built');
 // G: reused wrappers, one getLink per port, linked links counted as objects.
 w=world();a=w.run(P.link);assert.equal(a.objects,3);a=w.run(P.link);assert.equal(a.cache,'reused');assert.equal(a.objects,1);assert.equal(w.calls.getLink,1);assert.equal(a.devices[0].ports[0].linked,true);
 w.linked=false;a=w.run(P.link);assert.equal(a.objects,0);assert.equal(a.devices[0].ports[0].linked,false);
 // H: gc is called only when the engine exposes it, and reported either way.
 w=world();a=w.run(P.gc);assert.strictEqual(a.gc,null);assert.equal(a.objects,2);
 let called=0;w.ctx.gc=()=>called++;a=w.run(P.gc);assert.equal(a.gc,'gc');assert.equal(called,1);
 w.ctx.gc=()=>{throw new Error('denied')};a=w.run(P.gc);assert.equal(a.gc_error,'Error: denied');
});'''

class CacheProbeTests(unittest.TestCase):
    def test_cache_probes_in_js_runtime(self):
        payload = dict(repeat=INVENTORY_PROBES['inventory_repeat_same'], n=REPEAT_OBJECTS,
                       cached=INVENTORY_PROBES['inventory_cached_ports'],
                       link=INVENTORY_PROBES['inventory_cached_link_flag'],
                       gc=INVENTORY_PROBES['inventory_ports_gc'])
        p = subprocess.run(['node', '-e', JS], input=json.dumps(payload), capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stderr)

    def test_journal_keeps_object_counts(self):
        from test_inventory_probes import InventoryProbeTests
        t = InventoryProbeTests()
        c, s = t.run_probe('inventory_cached_ports', {'devices': [{'ports': [{}]}], 'objects': 0, 'cache': 'reused'})
        probe = [e for e in s['events'] if e['kind'] == 'inventory_probe'][0]
        self.assertEqual((probe['objects'], probe['cache']), (0, 'reused'))
        c, s = t.run_probe('inventory_ports_gc', {'devices': [], 'objects': 5, 'gc': None, 'gc_error': None})
        probe = [e for e in s['events'] if e['kind'] == 'inventory_probe'][0]
        self.assertIn('gc', probe); self.assertIsNone(probe['gc'])

if __name__ == '__main__':
    unittest.main()
