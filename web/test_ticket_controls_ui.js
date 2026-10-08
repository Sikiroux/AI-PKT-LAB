// Les résultats restent disponibles, mais séparés du suivi métier.
const fs=require('fs'),vm=require('vm'),assert=require('assert');
const html=fs.readFileSync(__dirname+'/tickets.html','utf8');
const start=html.indexOf('if(t.checks.length){');
const end=html.indexOf("\nif(t.kind==='wifi'",start);
assert(start>=0&&end>start);
function el(tag,text,css){return {tag,text,css,children:[],append(...items){this.children.push(...items)}}}
for(const complete of [false,true]){
 const d=el('div'),t={checked:'2026-10-08',complete,checks:[{label:'Réseau',status:'inconnu',detail:'Observation périmée'}]};
 vm.runInNewContext(html.slice(start,end),{el,d,t});
 assert.equal(d.children.length,1);
 const panel=d.children[0];assert.equal(panel.tag,'details');assert(!panel.open);
 assert.equal(panel.children[0].tag,'summary');
 assert(panel.children[0].text.includes(complete?'validés':'à examiner'));
 const result=panel.children.find(x=>x.css?.includes('check'));
 assert.equal(result.text,'Réseau : inconnu');
 assert.equal(result.children[0].children[1].text,'Observation périmée');
}
console.log('Ticket controls: collapsed pedagogical panel preserves results and evidence OK');
