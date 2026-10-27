const fs=require('fs'),vm=require('vm');
const fixtureSource=fs.readFileSync(__dirname+'/test_desktop_ui.js','utf8').split('(async()=>{')[0];
const scenario=String.raw`
(async()=>{
 vm.runInContext('printingApp()',ctx);await tick();const printers=contents.at(-1);
 assert(find(printers,e=>e.textContent.includes('Mode hors connexion désactivé')),'Configuration mode must not claim measured reachability');
 await byButton(printers,'Ouvrir la file').onclick();const jobs=contents.at(-1);
 const search=find(jobs,e=>e.attributes['aria-label']==='Rechercher un travail'),filter=find(jobs,e=>e.attributes['aria-label']==='Afficher les travaux');
 assert(find(jobs,e=>e.textContent==='Papier épuisé · PAPER_EMPTY'));const before=requests.length;search.value='absent';search.oninput();assert(!find(jobs,e=>e.textContent==='Office job'));assert(find(jobs,e=>e.textContent==='Aucun travail ne correspond aux filtres.'));assert.equal(requests.length,before);
 search.value='OFFICE';search.oninput();assert(find(jobs,e=>e.textContent==='Office job'));filter.value='printed';filter.onchange();assert(!find(jobs,e=>e.textContent==='Office job'));filter.value='pending';filter.onchange();assert(find(jobs,e=>e.textContent==='Office job'));assert(!find(jobs,e=>e.textContent==='PDF job'));assert.equal(requests.length,before,'Filters must not issue a network request or mutation');
 await byButton(printers,'Actualiser les travaux').onclick();assert.equal(find(jobs,e=>e.attributes['aria-label']==='Rechercher un travail').value,'OFFICE');assert.equal(find(jobs,e=>e.attributes['aria-label']==='Afficher les travaux').value,'pending');
 console.log('Printer queue: local filters, empty result, independent queue and preserved query OK');
})().catch(e=>{console.error(e);process.exitCode=1});`;
vm.runInNewContext(fixtureSource+scenario,{require,__dirname,console,process,setImmediate,URLSearchParams});
