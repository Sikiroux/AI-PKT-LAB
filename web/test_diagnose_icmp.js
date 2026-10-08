const assert=require('assert'),vm=require('vm'),cp=require('child_process');
const r=cp.spawnSync('python3',['-c','import diagnose_icmp;print(diagnose_icmp.SCRIPT)'],{cwd:__dirname,encoding:'utf8'});
assert.equal(r.status,0,r.stderr);
let reports=[],calls=[];
const devices=[
 {getName:()=> 'PC-test',getModel:()=> 'PC-PT',getProcess(name){calls.push(name);if(name==='Icmp')throw Error('invalid string position');return {createPingProcess(){throw Error('must never create a ping');},getPingProcess(){throw Error('must never get a ping');}};}},
 {getName:()=> 'SW-test',getModel:()=> '2960',getProcess(){return null;}}
];
vm.runInNewContext(r.stdout,{reportResult:s=>reports.push(JSON.parse(s)),ipc:{network:()=>({getDeviceCount:()=>devices.length,getDeviceAt:i=>devices[i]})}});
assert.equal(reports.length,1);
assert.deepStrictEqual(calls,['Icmp','IcmpProcess']);
assert.equal(reports[0].devices[0].attempts[0].error,'Error: invalid string position');
assert.equal(reports[0].devices[0].attempts[1].create_ping_available,true);
assert.equal(reports[0].devices[1].attempts[0].present,false);
assert(!r.stdout.includes('enterCommand'));
assert(!r.stdout.includes('fastForwardTime'));
console.log('Diagnostic ICMP: two names, independent errors, no ping and no configuration writes OK');
