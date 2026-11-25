const fs=require('fs'),vm=require('vm');const fixture=fs.readFileSync(__dirname+'/test_desktop_ui.js','utf8').split('(async()=>{')[0];
const scenario=String.raw`
(async()=>{
 ctx.setInterval=()=>1;ctx.clearTimeout=()=>{};ctx.setTimeout=()=>1;const storage=new Map(),ids=new Map(),listeners={};ctx.localStorage={getItem:k=>storage.get(k)||null,setItem:(k,v)=>storage.set(k,v)};
 ctx.document.body=create('body');ctx.document.body.classList={add(){},remove(){}};Element.prototype.focus=function(){};ctx.document.getElementById=id=>{const attached=find(ctx.document.body,e=>e.id===id)||[...ids.values()].map(root=>find(root,e=>e.id===id)).find(Boolean);if(attached)return attached;if(!ids.has(id)){const e=create('div');e.matches=()=>false;ids.set(id,e)}return ids.get(id)};ctx.document.addEventListener=(name,fn)=>listeners[name]=fn;
 vm.runInContext('initializeDesktopChrome()',ctx);assert.equal(ctx.document.body.dataset.taskbar,'visible');vm.runInContext("setDesktopConnection('online')",ctx);assert.equal(ids.get('desktopTrayCompany')?.attributes['data-connection']||find(ids.get('bar'),e=>e.id==='desktopTrayCompany').attributes['data-connection'],'online');const handle=find(ctx.document.body,e=>e.id==='taskbarHandle');assert(handle.hidden);
 vm.runInContext("applyTaskbarMode('auto')",ctx);assert.equal(ctx.document.body.dataset.taskbar,'auto');assert.equal(vm.runInContext('taskbarMode()',ctx),'auto');assert(!handle.hidden);
 handle.onclick();assert.equal(handle.attributes['aria-expanded'],'true');listeners.keydown({ctrlKey:true,altKey:true,key:'t',preventDefault(){}});
 vm.runInContext("expectedEnvironment='other-company'",ctx);assert.equal(vm.runInContext('taskbarMode()',ctx),'visible','A different enterprise does not inherit the preference');
 vm.runInContext("endpointSettings('personalization')",ctx);await tick();const settings=contents.at(-1);const mode=find(settings,e=>e.attributes['aria-label']==='Comportement de la barre');assert(mode);mode.value='auto';mode.onchange();assert.equal(vm.runInContext('taskbarMode()',ctx),'auto');
 console.log('Taskbar: visible default, persisted per-environment preference, handle, keyboard and personalization setting OK');
})().catch(e=>{console.error(e);process.exitCode=1});`;
vm.runInNewContext(fixture+scenario,{require,__dirname,console,process,setImmediate,URLSearchParams});
