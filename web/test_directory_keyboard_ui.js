const fs=require('fs'),vm=require('vm');
const fixtureSource=fs.readFileSync(__dirname+'/test_desktop_ui.js','utf8').split('(async()=>{')[0];
const scenario=`
Element.prototype.focus=function(){ctx.document.activeElement=this};
const stored=new Map();ctx.sessionStorage={getItem:key=>stored.get(key)||null,setItem:(key,value)=>stored.set(key,value)};
(async()=>{
 vm.runInContext('directory()',ctx);await tick();const root=contents.at(-1),alice=byButton(root,'Alice Client · alice'),bob=byButton(root,'Bob Technicien · bob');const before=requests.length;
 alice.onkeydown({key:'End',preventDefault(){}});assert.equal(bob.attributes['aria-pressed'],'true');assert.equal(ctx.document.activeElement,bob);assert.equal(byButton(root,'Bob Technicien · bob'),bob,'Selection retains double-click target');assert.equal(requests.length,before);
 bob.onkeydown({key:'ArrowUp',preventDefault(){}});assert.equal(alice.attributes['aria-pressed'],'true');alice.onkeydown({key:'ArrowDown',preventDefault(){}});assert.equal(bob.attributes['aria-pressed'],'true');bob.onkeydown({key:'Home',preventDefault(){}});assert.equal(alice.tabIndex,0);assert.equal(bob.tabIndex,-1);
 bob.onkeydown({key:'F10',shiftKey:true,preventDefault(){}});const menu=find(root,e=>e.className==='desktop-context-menu');assert(!menu.hidden);assert.equal(ctx.document.activeElement,byButton(menu,'Propriétés'));menu.onkeydown({key:'ArrowDown',preventDefault(){}});assert.equal(ctx.document.activeElement,byButton(menu,'Actualiser l’annuaire'));menu.onkeydown({key:'Escape',preventDefault(){}});assert(menu.hidden);assert.equal(ctx.document.activeElement,bob);
 const search=find(root,e=>e.attributes['aria-label']==='Rechercher un utilisateur');search.value='Bob';search.oninput();assert(byButton(root,'Bob Technicien · bob'));assert(!byButton(root,'Alice Client · alice'));
 await byButton(root,'Groupes').onclick();assert.equal(search.value,'');search.value='Lecteurs';search.oninput();await byButton(root,'Utilisateurs').onclick();assert.equal(search.value,'Bob','Each view retains its query');
 const shell=find(root,e=>e.className==='service-app directory-console');shell.onkeydown({key:'f',ctrlKey:true,preventDefault(){}});assert.equal(ctx.document.activeElement,search);const previous=requests.length;shell.onkeydown({key:'F5',preventDefault(){}});await tick();assert.equal(requests.length,previous+1);assert.equal(search.value,'Bob');
 const selected=byButton(root,'Bob Technicien · bob');selected.onkeydown({key:'Enter',altKey:true,preventDefault(){}});await tick();assert(!requests.some(([url])=>url.endsWith('directory/operation')),'Opening properties is read-only');assert(contents.at(-1)!==root);
 vm.runInContext("windows.delete('directory');directory()",ctx);await tick();const reopened=contents.at(-1);assert.equal(find(reopened,e=>e.attributes['aria-label']==='Rechercher un utilisateur').value,'Bob');assert.equal(byButton(reopened,'Bob Technicien · bob').attributes['aria-pressed'],'true');
 console.log('Directory keyboard: stable selection, arrow keys, properties, per-view queries, refresh and scoped persistence OK');
})().catch(e=>{console.error(e);process.exitCode=1});
`;
vm.runInNewContext(fixtureSource+scenario,{require,__dirname,process,console,setImmediate,URLSearchParams},{filename:__filename});
