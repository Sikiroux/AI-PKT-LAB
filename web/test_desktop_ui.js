// Integration checks for desktop apps without a browser or external packages.
const fs=require('fs'),vm=require('vm'),assert=require('assert');
class Element{
 constructor(tag){this.tagName=tag;this.children=[];this.dataset={};this.attributes={};this.style={};this.value='';this.textContent=''}
 append(...children){this.children.push(...children)}
 replaceChildren(...children){this.children=children}
 setAttribute(key,value){this.attributes[key]=value}
 remove(){}
}
const elements=[],requests=[];let discard=false,listFailure=false;
const create=tag=>{const e=new Element(tag);elements.push(e);return e};
const fixture={documents_share_id:'share',devices:{server:{name:'SRV-FILES'}},service:{local_files:[{name:'Local.txt',size:8}],mapped_drive:{path:'\\\\SRV-FILES\\Documents'},applications:['terminal','settings','login','documents']},applications:{documents:'Documents',terminal:'Terminal',settings:'Paramètres',login:'Session'},network:{client:[{name:'FastEthernet0',ip:'192.168.1.10',mask:'255.255.255.0',linked:true,protocol_up:true}]}};
const ctx={document:{createElement:create,createTextNode:x=>x,getElementById:()=>create('div')},location:{hash:''},console,confirm:()=>discard,innerWidth:1200,innerHeight:800,fetch:async(url,options)=>{requests.push([url,JSON.parse(options.body||'{}')]);const req=requests.at(-1)[1];let result=fixture;if(url.endsWith('files/action')){const a=req.request;result={revision:7,result:{allowed:!listFailure,code:listFailure?'NETWORK_DOWN':'OK',data:a.action==='list'?[{id:'file',name:'Shared.txt',read_only:false}]:{id:'file',name:'Shared.txt',content:'Initial'}}}}if(url.endsWith('read-local'))result={name:'Local.txt',content:'Local text'};return{ok:true,json:async()=>result}}};
vm.createContext(ctx);const html=fs.readFileSync(__dirname+'/desktop.html','utf8');const source=html.match(/<script>\s*const technician=([\s\S]*?)<\/script>/)[0].replace(/^<script>/,'').replace(/<\/script>$/,'').split('async function boot()')[0].replace('__TECHNICIAN__','false').replace('__TOKEN__','test').replace('__API_BASE__','/workspace');vm.runInContext(source,ctx);
const contents=[];ctx.contents=contents;vm.runInContext("check=async()=>{};core={make:()=>({raise(){},focus(){},on(){},render(fn){const el=document.createElement('div');contents.push(el);fn(el)}})}",ctx);
const tick=()=>new Promise(r=>setImmediate(r));
const find=(root,predicate)=>{if(predicate(root))return root;for(const e of root.children||[]){if(typeof e==='object'){const match=find(e,predicate);if(match)return match}}};
const byButton=(root,text)=>find(root,e=>e.tagName==='button'&&e.textContent===text);
(async()=>{
 vm.runInContext('explorer()',ctx);await tick();const shared=contents[0];await byButton(shared,'Shared.txt').onclick();const editor=find(shared,e=>e.tagName==='textarea');editor.value='Draft';editor.oninput();await byButton(shared,'Nouveau document').onclick();assert.equal(editor.value,'Draft','Cancelled discard must preserve text');
 await byButton(shared,'Enregistrer').onclick();const write=requests.find(([url,req])=>req.request?.action==='write')[1].request;assert.equal(write.file_id,'file');assert.equal(write.expected_revision,7);assert.equal(write.content,'Draft');
 listFailure=true;await byButton(shared,'Actualiser').onclick();assert(!byButton(shared,'Shared.txt'),'Failed refresh must remove stale listing');assert(find(shared,e=>e.textContent==='NETWORK_DOWN'));listFailure=false;
 vm.runInContext('localFiles()',ctx);await tick();const local=contents[1];await byButton(local,'Local.txt').onclick();assert.equal(find(local,e=>e.tagName==='textarea').value,'Local text');await byButton(local,'Enregistrer').onclick();assert(requests.some(([url,req])=>url.endsWith('save-local')&&req.payload.name==='Local.txt'));
 vm.runInContext('endpointSettings()',ctx);await tick();const settings=contents[2];assert(find(settings,e=>e.textContent==='192.168.1.10'));await byButton(settings,'Applications').onclick();assert(byButton(settings,'Désinstaller'));assert(!byButton(settings,'Installer'));await byButton(settings,'Lecteur réseau').onclick();assert(find(settings,e=>e.tagName==='input'&&e.value===fixture.service.mapped_drive.path));
 console.log('Desktop apps: shared revision, unsaved draft, unavailable listing, local save and settings navigation OK');
})().catch(e=>{console.error(e);process.exitCode=1});
