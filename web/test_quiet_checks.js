// Execute the actual generated IPC script with controlled asynchronous signals.
const assert=require('assert'),vm=require('vm'),cp=require('child_process'),path=require('path');
function script(accelerate){const r=cp.spawnSync(process.platform==='win32'?'python':'python3',['-c',`import quiet_checks;print(quiet_checks.script([('A','192.168.1.1'),('B','192.168.1.2')],${accelerate?'True':'False'}))`],{cwd:__dirname,encoding:'utf8'});assert.strictEqual(r.status,0,r.stderr);return r.stdout;}
function run(accelerate,simulation=false,portCount=1,failedSource=null){
 const processes=[],reports=[];let advances=0;
 function getProcess(kind){
  assert.strictEqual(kind,'IcmpProcess');
  return {
   createPingProcess(ip,count,timeout,wait,port){assert.strictEqual(count,2);assert.strictEqual(port,'FastEthernet0');return processes.length;},
   getPingProcess(){
    let callback,received=0;
    const p={start(){},cancel(){},getSentCount:()=>2,getTotalCount:()=>2,
     getReceivedCount:()=>received,registerEvent(name,obj,fn){assert.equal(name,"donePing");callback=fn;},unregisterEvent(){},complete(count){received=count;callback({}, {receiveCount:count,totalDelay:1});}};
    processes.push(p);return p;
   }
  };
 }
 const context={reportResult:s=>reports.push(JSON.parse(s)),ipc:{
  simulation:()=>({isSimulationMode:()=>simulation}),
  appWindow:()=>({getRealtimeToolbar:()=>({fastForwardTime(){advances++;}})}),
  network:()=>({getDevice:name=>{if(name===failedSource)throw Error("source unavailable");return {getProcess,getPortCount:()=>portCount,getPortAt:()=>({getIpAddress:()=>"192.168.1.10",getName:()=>"FastEthernet0"})};}})
 }};
 vm.runInNewContext(script(accelerate),context);return {processes,reports,advances,context};
}
let r=run(false);assert.strictEqual(r.advances,0);assert.strictEqual(r.reports.length,0);r.processes[1].complete(1);assert.strictEqual(r.reports.length,0);r.processes[0].complete(2);assert.deepStrictEqual(r.reports[0].map(x=>x.status),['valide','non satisfait']);
r=run(true);assert.strictEqual(r.advances,1);r.processes.forEach(p=>p.complete(2));assert.strictEqual(r.reports.length,1);
r=run(true,true);assert.strictEqual(r.advances,0);assert.strictEqual(r.processes.length,0);assert.deepStrictEqual(r.reports[0].map(x=>x.status),['inconnu','inconnu']);
r=run(true,false,2);assert.strictEqual(r.advances,0);assert.strictEqual(r.processes.length,0);assert.deepStrictEqual(r.reports[0].map(x=>x.status),['inconnu','inconnu']);
console.log('Quiet IPC: asynchronous correlation, full completion, failure, manual acceleration and Simulation preservation OK');

// Late callbacks must retain their own response function despite another bridge request.
r=run(false);r.context.reportResult=()=>{throw Error("wrong request");};r.processes.forEach(p=>p.complete(2));assert.equal(r.reports.length,1);
// IPC member access can throw: expose the exact stage, keep other probes independent.
r=run(false);r.context.ipc.network=()=>({getDevice:()=>({getProcess(){throw Error("invalid string position");}})});vm.runInNewContext(script(false),r.context);assert(r.reports[0].every(x=>x.status==="inconnu"&&x.detail.includes("processus Icmp")));

r=run(false,false,1,"A");assert.equal(r.processes.length,1);assert.equal(r.reports.length,0);r.processes[0].complete(2);assert.deepStrictEqual(r.reports[0].map(x=>x.status),["inconnu","valide"]);assert(r.reports[0][0].detail.includes("appareil source"));
