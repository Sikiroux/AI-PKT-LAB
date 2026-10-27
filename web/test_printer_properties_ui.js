const fs=require('fs'),vm=require('vm');
const fixtureSource=fs.readFileSync(__dirname+'/test_desktop_ui.js','utf8').split('(async()=>{')[0];
const scenario=String.raw`
(async()=>{
 vm.runInContext('printingApp()',ctx);await tick();const printers=contents.at(-1);
 await byButton(printers,'Propriétés').onclick();const props=contents.at(-1);
 assert(find(props,e=>e.className==='printer-property-hero'&&find(e,c=>c.tagName==='svg')),'Property header includes its native application icon');
 assert(byButton(props,'Définir par défaut').disabled);assert(byButton(props,'Installer le pilote').disabled);
 const before=requests.length;let general=byButton(props,'Général');assert.equal(general.attributes.role,'tab');assert.equal(general.attributes['aria-selected'],'true');
 general.onkeydown({key:'ArrowRight',preventDefault(){}});let port=byButton(props,'Port');assert.equal(port.attributes['aria-selected'],'true');assert.equal(find(props,e=>e.attributes.role==='tabpanel').attributes['aria-labelledby'],port.id);assert.equal(requests.length,before,'Navigating tabs never probes or changes configuration');
 const target=find(props,e=>e.attributes['aria-label']==='Adresse IP du port');target.value='192.168.1.99';const picker=find(printers,e=>e.attributes['aria-label']==='Imprimante');picker.value='pdf';picker.onchange();await byButton(props,'Appliquer le port IP').onclick();const operation=requests.filter(([url,r])=>r.operation==='set_port').at(-1)[1];assert.equal(operation.payload.queue_id,'office','The property sheet stays tied to its printer');assert.equal(operation.payload.ip,'192.168.1.99');assert.equal(byButton(props,'Port').attributes['aria-selected'],'true');
 byButton(props,'Port').onkeydown({key:'End',preventDefault(){}});assert.equal(byButton(props,'Maintenance').attributes['aria-selected'],'true');byButton(props,'Maintenance').onkeydown({key:'Home',preventDefault(){}});assert.equal(byButton(props,'Général').attributes['aria-selected'],'true');
 await byButton(printers,'Propriétés').onclick();const pdf=contents.at(-1);await byButton(pdf,'Port').onclick();assert(byButton(pdf,'Appliquer le port IP').disabled);await byButton(pdf,'Maintenance').onclick();assert(byButton(pdf,'Charger le papier').disabled);
 console.log('Printer properties: icon, keyboard tabs, scoped operations, selected tab and PDF restrictions OK');
})().catch(e=>{console.error(e);process.exitCode=1});`;
vm.runInNewContext(fixtureSource+scenario,{require,__dirname,process,console,setImmediate,URLSearchParams},{filename:__filename});
