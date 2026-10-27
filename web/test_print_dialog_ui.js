const fs=require('fs'),vm=require('vm');
const fixtureSource=fs.readFileSync(__dirname+'/test_desktop_ui.js','utf8').split('(async()=>{')[0];
const scenario=String.raw`
(async()=>{
 const originalFetch=ctx.fetch;let release,hold=false,printCode='QUEUED',noQueues=false,refreshFails=false;
 ctx.fetch=async(url,options)=>{if(url.endsWith('printing/print')){requests.push([url,JSON.parse(options.body)]);if(hold)await new Promise(r=>release=r);return{ok:true,json:async()=>({result:{code:printCode}})}}if(url.endsWith('printing/state')&&refreshFails)throw Error('Pont indisponible');const response=await originalFetch(url,options);if(url.endsWith('printing/state')&&noQueues)return{ok:true,json:async()=>({service:{queues:{},jobs:[],default_queue:''}})};return response};
 vm.runInContext('printingApp()',ctx);await tick();const printers=contents.at(-1);await byButton(printers,'Imprimer…').onclick();const dialog=contents.at(-1),target=find(dialog,e=>e.attributes['aria-label']==='Imprimante destinataire'),send=byButton(dialog,'Imprimer le document');
 assert(find(dialog,e=>e.textContent==='Local.txt'&&e.tagName==='dd'));target.value='pdf';target.onchange();assert(find(dialog,e=>e.textContent==='PDF simulé'&&e.tagName==='dd'));
 hold=true;const pending=send.onclick();await tick();assert(send.disabled);assert(target.disabled);await send.onclick();assert.equal(requests.filter(([u])=>u.endsWith('printing/print')).length,1);release();await pending;assert(!send.disabled);assert(find(dialog,e=>e.textContent==='Travail accepté. Consulte la file pour connaître son état.'));assert.equal(requests.find(([u])=>u.endsWith('printing/print'))[1].queue_id,'pdf');hold=false;
 printCode='NETWORK_UNKNOWN';await send.onclick();assert(find(dialog,e=>e.textContent==='Connectivité réseau non vérifiée · NETWORK_UNKNOWN'));
 printCode='PRINTED';refreshFails=true;await send.onclick();assert(find(dialog,e=>e.textContent.includes('Document imprimé dans la simulation. Actualisation indisponible')),'A refresh failure must not erase the confirmed print result');refreshFails=false;await byButton(printers,'Actualiser les travaux').onclick();
 fixture.service.local_files=[];await byButton(printers,'Actualiser les travaux').onclick();assert(send.disabled);const count=requests.filter(([u])=>u.endsWith('printing/print')).length;await send.onclick();assert.equal(requests.filter(([u])=>u.endsWith('printing/print')).length,count);assert(find(dialog,e=>e.textContent.startsWith('Aucun document local disponible.')));
 noQueues=true;await byButton(printers,'Actualiser les travaux').onclick();assert(byButton(dialog,'Voir la file d’attente').disabled);assert(find(dialog,e=>e.textContent.startsWith('Aucune imprimante disponible.')));
 console.log('Print dialog: preview, single submission, result semantics, refresh failure and empty states OK');
})().catch(e=>{console.error(e);process.exitCode=1});`;
vm.runInNewContext(fixtureSource+scenario,{require,__dirname,process,console,setImmediate,URLSearchParams},{filename:__filename});
