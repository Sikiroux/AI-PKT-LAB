const fs=require('fs'),vm=require('vm');
const fixtureSource=fs.readFileSync(__dirname+'/test_desktop_ui.js','utf8').split('(async()=>{')[0];
const scenario=String.raw`
(async()=>{
 const originalFetch=ctx.fetch;let code='RESOLVED',status='resolved',fail=false,hold=false,release,flushAllowed=true;
 ctx.fetch=async(url,options)=>{if(url.endsWith('dns/resolve')){requests.push([url,JSON.parse(options.body)]);if(hold)await new Promise(r=>release=r);if(fail)throw Error('Pont indisponible');return{ok:true,json:async()=>({result:{status,code,answers:status==='resolved'?[{name:'docs.lab.test',type:'A',value:'192.168.1.50',ttl_remaining:120}]:[]}})}}if(url.endsWith('dns/flush'))return{ok:true,json:async()=>({result:{allowed:flushAllowed,code:flushAllowed?'OK':'PERMISSION_DENIED'}})};return originalFetch(url,options)};
 vm.runInContext('dnsConsole()',ctx);await tick();const dns=contents.at(-1);let name=find(dns,e=>e.attributes['aria-label']==='Nom DNS');assert(find(dns,e=>e.textContent==='Aucun test effectué'));assert.equal(requests.filter(([u])=>u.endsWith('dns/resolve')).length,0);
 name.value='docs.lab.test';name.oninput();hold=true;const pending=byButton(dns,'Résoudre').onclick();await tick();assert(name.disabled);await byButton(dns,'Résoudre').onclick();assert.equal(requests.filter(([u])=>u.endsWith('dns/resolve')).length,1);release();await pending;hold=false;assert(find(dns,e=>e.textContent==='Résolution réussie · RESOLVED'));assert(find(dns,e=>e.textContent==='Cache : non renseigné'));name.value='other.lab.test';name.oninput();assert(find(dns,e=>e.textContent==='docs.lab.test · A · Poste client'));
 await byButton(dns,'Actualiser la console').onclick();name=find(dns,e=>e.attributes['aria-label']==='Nom DNS');assert.equal(name.value,'other.lab.test');assert(find(dns,e=>e.textContent==='Résolution réussie · RESOLVED'));
 status='unknown';code='OBSERVATION_UNKNOWN';await byButton(dns,'Résoudre').onclick();assert(find(dns,e=>e.dataset.state==='unknown'));assert(!find(dns,e=>e.textContent==='192.168.1.50'));
 fail=true;await byButton(dns,'Résoudre').onclick();assert(find(dns,e=>e.textContent==='Test non confirmé'));assert(find(dns,e=>e.textContent==='Pont indisponible'));fail=false;
 status='resolved';code='RESOLVED';await byButton(dns,'Résoudre').onclick();flushAllowed=false;await byButton(dns,'Vider mon cache').onclick();assert(find(dns,e=>e.textContent==='Résolution réussie · RESOLVED'),'Refused flush retains the last result');flushAllowed=true;await byButton(dns,'Vider mon cache').onclick();assert(find(dns,e=>e.textContent==='Aucun test effectué'));name.value=' ';name.oninput();assert(byButton(dns,'Résoudre').disabled);
 console.log('DNS resolution: query snapshot, persistence, unknown/error states, duplicate protection and cache refusal OK');
})().catch(e=>{console.error(e);process.exitCode=1});`;
vm.runInNewContext(fixtureSource+scenario,{require,__dirname,process,console,setImmediate,URLSearchParams},{filename:__filename});
