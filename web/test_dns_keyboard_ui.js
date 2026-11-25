const fs=require('fs'),vm=require('vm');
const fixtureSource=fs.readFileSync(__dirname+'/test_desktop_ui.js','utf8').split('(async()=>{')[0].replace("replace('__TECHNICIAN__','false')","replace('__TECHNICIAN__','true')");
const scenario=String.raw`
Element.prototype.focus=function(){ctx.document.activeElement=this};const store=new Map();ctx.sessionStorage={getItem:k=>store.get(k)||null,setItem:(k,v)=>store.set(k,v)};
(async()=>{
 const records={a:{id:'a',name:'a.lab.test',type:'A',value:'192.168.1.50',ttl:300,enabled:true},z:{id:'z',name:'z.lab.test',type:'CNAME',value:'a.lab.test',ttl:300,enabled:true}};
 const original=ctx.fetch;ctx.fetch=async(url,options)=>{if(url.endsWith('dns/admin')){requests.push([url,{}]);return {ok:true,json:async()=>({documents_dns_name:'a.lab.test',service:{server:{zone:'lab.test'},records}})}}return original(url,options)};
 vm.runInContext('dnsConsole()',ctx);await tick();const root=contents.at(-1);await byButton(root,'Enregistrements').onclick();const first=byButton(root,'a.lab.test'),last=byButton(root,'z.lab.test'),before=requests.length;
 first.onkeydown({key:'ArrowDown',preventDefault(){}});assert.equal(ctx.document.activeElement,last);assert.equal(last.tabIndex,0);assert.equal(first.tabIndex,-1);assert.equal(byButton(root,'z.lab.test'),last);assert.equal(requests.length,before,'Arrow navigation is local only');
 last.onkeydown({key:'Home',preventDefault(){}});assert.equal(first.tabIndex,0);first.onkeydown({key:'End',preventDefault(){}});assert.equal(last.tabIndex,0);
 assert([...store.entries()].some(([k,v])=>k.endsWith('dns-record-view')&&JSON.parse(v).selected==='z'));
 last.onkeydown({key:'Enter',altKey:true,preventDefault(){}});await tick();const propertiesRoot=contents.at(-1);assert.equal(requests.length,before,'Opening properties never resolves or modifies DNS');
 const search=find(root,e=>e.attributes['aria-label']==='Rechercher un enregistrement');search.value='192.168.1.50';search.oninput();assert(byButton(root,'Propriétés de l’enregistrement').disabled,'Hidden selected records cannot be edited through toolbar');
 const table=find(root,e=>e.attributes['aria-label']==='Enregistrements de la zone');table.parentElement.onkeydown({key:'f',ctrlKey:true,preventDefault(){}});assert.equal(ctx.document.activeElement,search);
 table.parentElement.onkeydown({key:'F5',preventDefault(){}});await tick();assert.equal(requests.length,before+1);assert.equal(find(root,e=>e.attributes['aria-label']==='Rechercher un enregistrement').value,'192.168.1.50');
 vm.runInContext("windows.delete('dns');dnsConsole()",ctx);await tick();const reopened=contents.at(-1);await byButton(reopened,'Enregistrements').onclick();assert.equal(find(reopened,e=>e.attributes['aria-label']==='Rechercher un enregistrement').value,'192.168.1.50');assert(byButton(reopened,'Propriétés de l’enregistrement').disabled);
 await byButton(reopened,'a.lab.test').onclick();await byButton(propertiesRoot,'Enregistrer l’entrée').onclick();await tick();assert.equal(requests.filter(([url,r])=>url.endsWith('dns/operation')&&r.operation==='upsert_record').at(-1)[1].payload.record_id,'z','Properties keep their original record when list selection changes');
 console.log('DNS keyboard: local navigation, immutable DOM, properties, hidden selection, refresh and reopening filters OK');
})().catch(e=>{console.error(e);process.exitCode=1});`;
vm.runInNewContext(fixtureSource+scenario,{require,__dirname,process,console,setImmediate,URLSearchParams},{filename:__filename});
