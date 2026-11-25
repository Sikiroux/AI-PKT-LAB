const fs=require('fs'),vm=require('vm');
const fixture=fs.readFileSync(__dirname+'/test_desktop_ui.js','utf8').split('(async()=>{')[0];
const scenario=String.raw`
(async()=>{
 const storage=new Map();ctx.sessionStorage={getItem:k=>storage.get(k)||null,setItem:(k,v)=>storage.set(k,v)};
 Element.prototype.focus=function(){ctx.document.activeElement=this};
 const host=create('div');ctx.host=host;
 vm.runInContext("var frame=consoleFrame(host,[['one','Première',p=>p.textContent='A'],['two','Deuxième',p=>p.textContent='B']]);frame.set({})",ctx);
 const second=byButton(host,'Deuxième');second.onclick();assert.equal(ctx.frame.main.textContent,'B');
 const host2=create('div');ctx.host2=host2;vm.runInContext("var frame2=consoleFrame(host2,[['one','Première',p=>p.textContent='A'],['two','Deuxième',p=>p.textContent='B']]);frame2.set({})",ctx);assert.equal(ctx.frame2.main.textContent,'B','Console section survives reopening');
 byButton(host2,'Deuxième').onkeydown({key:'Home',preventDefault(){}});assert.equal(ctx.frame2.main.textContent,'A');
 let release;const pending=ctx.frame2.run(()=>new Promise(r=>release=r));assert(ctx.frame2.main.inert);byButton(host2,'Première').onkeydown({key:'End',preventDefault(){}});assert.equal(ctx.frame2.main.textContent,'A','Pending mutation freezes navigation');release();await pending;assert.equal(ctx.frame2.main.inert,false);
 vm.runInContext('printingApp()',ctx);await tick();const printers=contents.at(-1);await byButton(printers,'Ouvrir la file').onclick();const queue=contents.at(-1),row=find(queue,e=>e.tagName==='tr'&&e.attributes['aria-selected']==='true');assert(row);row.onkeydown({key:'End',preventDefault(){}});assert.equal(row.attributes['aria-selected'],'true');
 const original=ctx.fetch;let failPrinting=false;
 ctx.fetch=async(url,options)=>{if(failPrinting&&String(url).includes('printing/state'))throw Error('Pont interrompu');return original(url,options)};
 failPrinting=true;discard=true;await byButton(queue,'Annuler #1').onclick();assert(find(printers,e=>e.textContent.includes('Modification enregistrée. Actualisation indisponible')),'Confirmed cancellation survives failed refresh');
 assert.equal(requests.filter(([url,req])=>url.endsWith('printing/operation')&&req.operation==='cancel_job').length,1);
 ctx.fetch=original;vm.runInContext('endpointSettings()',ctx);await tick();const settings=contents.at(-1);byButton(settings,'Réseau').onkeydown({key:'End',preventDefault(){}});assert.equal(byButton(settings,'Personnalisation').attributes['aria-pressed'],'true');
 vm.runInContext('ftpClient()',ctx);await tick();const ftp=contents.at(-1);byButton(ftp,'Connexion…').onclick();await byButton(contents.at(-1),'Se connecter').onclick();await byButton(ftp,'Remote.txt').onclick();const remote=byButton(ftp,'Remote.txt');remote.onkeydown({key:'Home',preventDefault(){}});assert.equal(ctx.document.activeElement.textContent,'Local.txt');assert.equal(ctx.document.activeElement.attributes['aria-pressed'],'true');await byButton(ftp,'Remote.txt').onclick();
 ctx.fetch=async(url,options)=>{if(String(url).includes('endpoint/state'))throw Error('Lecture indisponible');return original(url,options)};
 await byButton(ftp,'Télécharger vers le poste').onclick();assert(find(ftp,e=>e.textContent.includes('Téléchargement simulé terminé. Actualisation locale indisponible')));assert(find(ftp,e=>e.textContent==='Terminé'));assert.equal(requests.filter(([url])=>url.endsWith('ftp/download')).length,1);
 console.log('Consolidation: console persistence/keyboard/pending, printer keyboard and confirmed actions after refresh failure OK');
})().catch(e=>{console.error(e);process.exitCode=1});`;
vm.runInNewContext(fixture+scenario,{require,__dirname,console,process,setImmediate,URLSearchParams});
