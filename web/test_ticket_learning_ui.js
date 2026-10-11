const fs=require('fs'),vm=require('vm'),assert=require('assert');
const html=fs.readFileSync(__dirname+'/tickets.html','utf8');
class E{constructor(tag,text){this.tagName=tag;this.textContent=text||'';this.children=[]}append(...n){this.children.push(...n)}}
const requests=[];let approval=false;const ctx={el:(...a)=>new E(...a),ticketHints:()=>['Observer','Comparer','Retester'],act:(path,data)=>requests.push([path,data]),confirm:()=>approval};vm.createContext(ctx);vm.runInContext(html.slice(html.indexOf('function renderTicketLearning'),html.indexOf('function ticketHints')),ctx);
const flatten=e=>[e,...e.children.flatMap(flatten)],button=(e,text)=>flatten(e).find(n=>n.tagName==='button'&&n.textContent===text);
const t={id:'T1',live_incident:true,kind:'workspace',stage:'prepared',request_context:{resource:'\\\\SRV\\Documents',expected_result:'Lire le document'}};
const host=new E('div');ctx.renderTicketLearning(host,t);button(host,'Consulter cet indice').onclick();assert.equal(requests.at(-1)[1].action,'learning_hint');assert.equal(requests.at(-1)[1].level,1);
button(host,'Voir la correction de ce ticket').onclick();assert.equal(requests.length,1,'Cancellation never reveals');approval=true;button(host,'Voir la correction de ce ticket').onclick();assert.equal(requests.at(-1)[1].action,'learning_correction');assert.equal(requests.at(-1)[1].id,'T1');assert(!requests.some(x=>['resolve','close','restore'].includes(x[1].action)));
t.learning={hints:[1],correction:{title:'Chemin incorrect',steps:['Corriger','Retester','Contrôler'],limit:'Aucune réparation automatique'}};const revealed=new E('div');ctx.renderTicketLearning(revealed,t);assert(flatten(revealed).some(x=>x.textContent.includes('Ressource attendue')));assert(flatten(revealed).some(x=>x.textContent==='Chemin incorrect'));assert(!button(revealed,'Voir la correction de ce ticket'));
const legacy=new E('div');ctx.renderTicketLearning(legacy,{id:'OLD'});assert(!button(legacy,'Voir la correction de ce ticket'));assert(button(legacy,'Exporter le bilan des interventions'));
console.log('Learning UI: explicit reveal, cancellation, scoped hints, target context and no automatic resolution OK');
