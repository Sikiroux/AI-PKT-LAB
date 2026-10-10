const fs=require('fs'),vm=require('vm');
const fixture=fs.readFileSync(__dirname+'/test_desktop_ui.js','utf8').split('(async()=>{')[0].replace(".replace('__TECHNICIAN__','false')",".replace('__TECHNICIAN__','true')");
const scenario=`
(async()=>{
 let unavailable=false;
 ctx.fetch=async(url,options)=>{requests.push([url,JSON.parse(options.body||'{}')]);if(unavailable)return{ok:false,json:async()=>({error:'Preuve périmée'})};return{ok:true,json:async()=>({limit:100,services:[{id:'files',name:'Fichiers',scope:'Serveur',status:'stopped'},{id:'dns',name:'DNS',scope:'Infrastructure',status:'unknown'}],events:[{at:123,text:'FTP upload : FTP_DATA_BLOCKED'}]})}};
 vm.runInContext('serviceInspection()',ctx);await tick();const root=contents.at(-1);
 assert(find(root,e=>e.textContent==='Arrêté'));assert(find(root,e=>e.textContent==='Non observé'));assert(byButton(root,'Ouvrir Fichiers'));
 await byButton(root,'Événements').onclick();assert(find(root,e=>e.textContent==='FTP upload : FTP_DATA_BLOCKED'));const search=find(root,e=>e.attributes['aria-label']==='Rechercher un service ou événement');search.value='aucun';search.oninput();assert(!find(root,e=>e.textContent==='FTP upload : FTP_DATA_BLOCKED'));search.value='';search.oninput();
 unavailable=true;await byButton(root,'Actualiser').onclick();assert(!find(root,e=>e.textContent==='FTP upload : FTP_DATA_BLOCKED'));assert(find(root,e=>e.textContent==='Preuve périmée'));
 assert(requests.every(([url,r])=>url.endsWith('desktop/inspection/state')&&r.source==='technician'),'Read-only tool must never ping or mutate');
 let vpnConnected=false;ctx.fetch=async(url,options)=>{requests.push([url,JSON.parse(options.body||'{}')]);if(url.endsWith('vpn-connect'))vpnConnected=true;return{ok:true,json:async()=>url.endsWith('/state')?{technician:{location:'office',connection:'wired',access:{reason:'OK'},locations:{office:{label:'Bureau'}},pending:null,vpn_connected:vpnConnected,vpn_expires_at:null}}:{result:{code:'OK'}}}};
 vm.runInContext('mobility()',ctx);await tick();const mobility=contents.at(-1);assert(!find(mobility,e=>e.attributes['aria-label']==='Mot de passe VPN'),'No password form in main overview');await byButton(mobility,'Raccordement…').onclick();const movement=contents.at(-1);assert(find(movement,e=>e.attributes['aria-label']==='Emplacement du portable'));await byButton(movement,'Déplacer et raccorder').onclick();assert(requests.some(([url,r])=>url.endsWith('technician/move')&&r.location==='office'&&r.connection==='wired'));await byButton(mobility,'VPN d’entreprise…').onclick();const vpn=contents.at(-1),secret=find(vpn,e=>e.attributes['aria-label']==='Mot de passe VPN');secret.value='training';await byButton(vpn,'Connecter le VPN').onclick();assert.equal(secret.value,'');assert(find(vpn,e=>e.textContent==='OK'),'VPN result visible in its window');
 console.log('Services UI: observed states, filtering, real journal, no ping or write, stale clearing OK');
})().catch(e=>{console.error(e);process.exitCode=1});`;
vm.runInNewContext(fixture+scenario,{require,__dirname,process,console,setImmediate,URLSearchParams},{filename:__filename});
