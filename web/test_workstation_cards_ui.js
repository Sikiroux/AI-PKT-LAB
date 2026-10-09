// Integration checks for desktop apps without a browser or external packages.
const fs=require('fs'),vm=require('vm'),assert=require('assert');
class Element{
 constructor(tag){this.tagName=tag;this.children=[];this.dataset={};this.attributes={};this.style={};this.value='';this.textContent='';this.classList={add(){},remove(){}}}
 append(...children){const empty=this.children.length===0;this.children.push(...children);for(const c of children)if(typeof c==='object')c.parentElement=this;if(this.tagName==='select'&&empty&&children[0])this.value=children[0].value}
 replaceChildren(...children){this.children=[];if(this.tagName==='select')this.value='';this.append(...children)}
 setAttribute(key,value){this.attributes[key]=value}
 remove(){}
}
const elements=[],requests=[];let discard=false,listFailure=false,ftpFailure=false,ftpRevision=22,directoryFailure=false;
const create=tag=>{const e=new Element(tag);elements.push(e);return e};
const fixture={documents_share_id:'share',devices:{server:{name:'SRV-FILES'}},service:{local_files:[{name:'Local.txt',size:8}],mapped_drive:{path:'\\\\SRV-FILES\\Documents'},applications:['terminal','settings','login','documents']},applications:{documents:'Documents',terminal:'Terminal',settings:'Paramètres',login:'Session'},network:{client:[{name:'FastEthernet0',ip:'192.168.1.10',mask:'255.255.255.0',linked:true,protocol_up:true}]}};
const directoryFixture={domain:{dns_name:'formation.test'},ous:{root:{id:'root',name:'Entreprise',parent_id:null},it:{id:'it',name:'IT',parent_id:'root'}},users:{alice:{id:'alice',display_name:'Alice Client',username:'alice',ou_id:'root',enabled:true,must_change_password:false},bob:{id:'bob',display_name:'Bob Technicien',username:'bob',ou_id:'it',enabled:true,must_change_password:false}},groups:{readers:{id:'readers',name:'Lecteurs',member_user_ids:['alice']}}};
const ctx={document:{createElement:create,createElementNS:(_,tag)=>create(tag),createTextNode:x=>x,getElementById:()=>create('div')},location:{hash:'',search:''},URLSearchParams,console,confirm:()=>discard,innerWidth:1200,innerHeight:800,fetch:async(url,options)=>{requests.push([url,JSON.parse(options.body||'{}')]);const req=requests.at(-1)[1];let result=fixture;if(url.endsWith('files/action')){const a=req.request;result={revision:7,result:{allowed:!listFailure,code:listFailure?'NETWORK_DOWN':'OK',data:a.action==='list'?[{id:'file',name:'Shared.txt',read_only:false}]:{id:'file',name:'Shared.txt',content:'Initial'}}}}if(url.endsWith('read-local'))result={name:'Local.txt',content:'Local text'};
if(url.includes('desktop/deployment/')){const stage=url.endsWith('operation')?'media':'idle';result={service:{stage,revision:stage==='media'?1:0,attempt:1,station:'PC-ATELIER',requirements:{image_id:'pro-base',locale:'fr-FR',keyboard:'fr-FR',account:'formation'},images:[{id:'pro-base',name:'Windows Pro',edition:'Pro'}]},result:{passed:false,checks:{}}}}
if(url.includes('desktop/printing/'))result={service:{default_queue:'office',spooler_running:true,printer:{paper_pages:50},queues:{office:{id:'office',name:'Bureau',port_ip:'192.168.1.50',driver_valid:true,paused:false,use_offline:false},pdf:{id:'pdf',name:'PDF',driver_valid:true,paused:false,use_offline:false}},jobs:[{id:1,queue_id:'office',name:'Office job',status:'blocked',detail:'PAPER_EMPTY'},{id:2,queue_id:'pdf',name:'PDF job',status:'printed',detail:'OK'}]}};
if(url.includes('desktop/ftp/')){if(url.endsWith('upload'))ftpRevision++;result={revision:ftpRevision,result:{allowed:!ftpFailure,code:ftpFailure?'FTP_DATA_BLOCKED':'226',files:[{name:'Remote.txt',size:12},{name:'Local.txt',size:8}]}}}
if(url.endsWith('directory/state')){if(directoryFailure)return{ok:false,json:async()=>({error:'Annuaire inaccessible'})};result={directory:directoryFixture,requester_id:'alice'}}
if(url.endsWith('directory/operation')){result={result:{code:'OK'}};if(req.operation==='create_user'){directoryFixture.users.new={id:'new',display_name:req.payload.display_name,username:req.payload.username,ou_id:req.payload.ou_id,enabled:true,must_change_password:true};result.result.user_id='new'}if(req.operation==='reset_password')result.result.temporary_password='Tmp-Test!';}
if(url.endsWith('directory/login')||url.endsWith('directory/change-password'))result={result:{code:'OK',allowed:true}};
return{ok:true,json:async()=>result}}};
vm.createContext(ctx);const html=fs.readFileSync(__dirname+'/desktop.html','utf8');const source=html.match(/<script>\s*const technician=([\s\S]*?)<\/script>/)[0].replace(/^<script>/,'').replace(/<\/script>$/,'').split('async function boot()')[0].replace('__TECHNICIAN__','false').replace('__TOKEN__','test').replace('__API_BASE__','/workspace');vm.runInContext(source,ctx);
const contents=[];ctx.contents=contents;vm.runInContext("check=async()=>{};core={make:()=>({state:{focused:false,minimized:false},setIcon(){},raise(){},focus(){},on(){},render(fn){const el=document.createElement('div');contents.push(el);fn(el)}})}",ctx);
const tick=()=>new Promise(r=>setImmediate(r));
const find=(root,predicate)=>{if(predicate(root))return root;for(const e of root.children||[]){if(typeof e==='object'){const match=find(e,predicate);if(match)return match}}};
const byButton=(root,text)=>find(root,e=>e.tagName==='button'&&e.textContent===text);

let fail=false;
fixture.company='Entreprise test';fixture.workstations=[{name:'PC-01',serial:'serial-a',ip:'10.0.0.2',user:'Mina',remote_supported:true,role:'client',status:'unknown',employee_id:'employee'},{name:'PC-02',serial:'serial-b',user:'Paul',remote_supported:true,role:'client',status:'passed'},{name:'TECH',serial:'tech',role:'technician',remote_supported:false,status:'unknown'}];
fixture.company_registry={people:{employee:{username:'mina'}}};
ctx.window={open:(url)=>{ctx.opened=url}};
ctx.fetch=async(url,options)=>{const req=JSON.parse(options.body||'{}');requests.push([url,req]);if(fail)return{ok:false,json:async()=>({error:'Session indisponible'})};return{ok:true,json:async()=>fixture}};
(async()=>{
 vm.runInContext('workstationCards()',ctx);await tick();const root=contents[0];
 await byButton(root,'PC-01 · serial-a').onclick();assert(find(root,e=>e.textContent==='Compte associé : mina'));
 const search=find(root,e=>e.tagName==='input');search.value='Paul';search.oninput();
 await byButton(root,'Prendre la main sur PC-01').onclick();assert.equal(requests.at(-1)[1].target_serial,'serial-a');assert(ctx.opened.includes('serial-a'));
 search.value='';search.oninput();await byButton(root,'TECH · tech').onclick();assert(!byButton(root,'Prendre la main sur TECH'));
 fail=true;await byButton(root,'Actualiser les fiches').onclick();assert(!byButton(root,'PC-01 · serial-a'));assert(find(root,e=>e.textContent==='Session indisponible'));fail=false;
 fixture.company_documents=[{id:'company-resources',title:'Ressources de Entreprise test',category:'Entreprise',paragraphs:['PC-01 · adresse configurée : 10.0.0.2']}];await vm.runInContext("api('state')",ctx);
 const before=requests.length;vm.runInContext('documentationApp()',ctx);const docs=contents.at(-1);assert(find(docs,e=>e.textContent==='Repérer son environnement'));
 vm.runInContext("documentationApp('stock')",ctx);assert(find(docs,e=>e.tagName==='h2'&&e.textContent==='Préparer et remettre un matériel'));assert.equal(requests.length,before,'Documentation never probes PT');
 vm.runInContext("documentationApp('ticket-queue')",ctx);assert(find(docs,e=>e.tagName==='h2'&&e.textContent==='Comprendre la file des tickets'));assert.equal(requests.length,before);
 assert(byButton(docs,'Ressources de Entreprise test'));await byButton(docs,'Ressources de Entreprise test').onclick();assert(find(docs,e=>e.textContent==='PC-01 · adresse configurée : 10.0.0.2'));assert.equal(requests.length,before,'Company documentation uses cached state, without probes');
 const query=find(docs,e=>e.tagName==='input');query.value='inexistant';query.oninput();assert(find(docs,e=>e.textContent==='Aucune procédure ne correspond à cette recherche.'));
 assert(requests.filter(([url])=>url.endsWith('/action')).length===1,'Reading cards must not trigger a connection');
 console.log('Workstation cards and documentation: target identity, search, technician distinction, stale-view clearing and read-only documentation OK');
})().catch(e=>{console.error(e);process.exitCode=1});
