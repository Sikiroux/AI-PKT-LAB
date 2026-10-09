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

(async()=>{
 directoryFixture.revision=7;
 directoryFixture.computers={pc:{id:'pc',name:'PC-01',device_id:'client',ou_id:'it',domain_joined:true}};
 directoryFixture.policy={lockout_threshold:3,lockout_seconds:60,password_max_age_seconds:86400};
 directoryFixture.audit=[{at:100,operation:'unlock_user',user_id:'alice',code:'OK'}];
 vm.runInContext('directory()',ctx);await tick();const root=contents[0];
 await byButton(root,'Groupes').onclick();await byButton(root,'Propriétés de l’objet').onclick();const props=contents.at(-1);
 await byButton(props,'Membres').onclick();assert(byButton(props,'Retirer alice'));
 await byButton(props,'Ajouter ce membre').onclick();
 let req=requests.filter(([u])=>u.endsWith('directory/operation')).at(-1)[1];
 assert.equal(req.payload.group_id,'readers');assert.equal(req.payload.user_id,'bob');assert.equal(req.expected_revision,7);
 await byButton(root,'Ordinateurs').onclick();
 await byButton(root,'Propriétés de l’objet').onclick();assert(find(props,e=>e.textContent==='Joint au domaine (simulation)'));await byButton(props,'Emplacement').onclick();
 await byButton(props,'Déplacer l’ordinateur').onclick();
 req=requests.filter(([u])=>u.endsWith('directory/operation')).at(-1)[1];
 assert.equal(req.operation,'move_object');assert.equal(req.payload.object_type,'computer');assert.equal(req.payload.object_id,'pc');
 const mutations=requests.filter(([u])=>u.endsWith('directory/operation')).length;
 await byButton(root,'Historique').onclick();assert(find(root,e=>e.textContent==='unlock_user'));
 await byButton(root,'Stratégie').onclick();assert(find(root,e=>e.textContent==='1 jours'));
 assert.equal(requests.filter(([u])=>u.endsWith('directory/operation')).length,mutations,'Read-only tabs must not change AD');
 await byButton(root,'Utilisateurs').onclick();
 await byButton(root,'Propriétés de l’objet').onclick();await byButton(props,'Général').onclick();const name=find(props,e=>e.tagName==='input'&&e.value==='Alice Client');
 assert(name);name.value='Alice Modifiée';
 await byButton(props,'Enregistrer les propriétés').onclick();
 req=requests.filter(([u])=>u.endsWith('directory/operation')).at(-1)[1];
 assert.equal(req.payload.user_id,'alice');assert.equal(req.payload.display_name,'Alice Modifiée');assert.equal(req.expected_revision,7);
 console.log('Directory console navigation and revision payload: OK');
})().catch(e=>{console.error(e);process.exitCode=1});
