const fs=require('fs'),vm=require('vm'),assert=require('assert');
const html=fs.readFileSync(__dirname+'/tickets.html','utf8');
const source=html.slice(html.indexOf('function renderResolution('),html.indexOf('function render(){'));
class E{constructor(tag,text){this.tag=tag;this.text=text;this.children=[];this.value='';this.checked=false}append(...c){this.children.push(...c)}prepend(...c){this.children.unshift(...c)}setAttribute(){}}
const requests=[],ctx={el:(...args)=>new E(...args),state:{site:{environment_id:'env'}},reopenDrafts:{},statuses:{resolu:'Résolu',clos:'Clos'},act:async(path,data)=>requests.push([path,data])};vm.createContext(ctx);vm.runInContext(source,ctx);
const find=(el,pred)=>pred(el)?el:el.children.map(c=>find(c,pred)).find(Boolean);
(async()=>{
 const open=new E('div');ctx.renderResolution(open,{id:'T1',status:'en_cours',kind:'pc'});await find(open,e=>e.text==='Vérifier et marquer résolu').onclick();assert.equal(requests.at(-1)[1].action,'resolve');assert.equal(requests.at(-1)[1].id,'T1');
 const solved=new E('div');ctx.renderResolution(solved,{id:'T2',status:'resolu',kind:'workspace',resolved:'date',resolution:{id:'current',text:'Solution'}});assert(find(solved,e=>e.text==='Solution'));const check=find(solved,e=>e.tag==='input');check.checked=true;await find(solved,e=>e.text==='Confirmer et clôturer').onclick();assert.equal(requests.at(-1)[1].resolution_id,'current');assert.equal(requests.at(-1)[1].confirmation,true);
 const reason=find(solved,e=>e.tag==='textarea');reason.value='Le problème est revenu';await find(solved,e=>e.text==='Rouvrir le ticket').onclick();assert.equal(requests.at(-1)[1].action,'reopen');assert.equal(requests.at(-1)[1].reason,reason.value);
 const queued=new E('div');ctx.renderResolution(queued,{stage:'queued'});assert.equal(queued.children.length,0);
 const manual=new E('div');ctx.renderResolution(manual,{id:'M',status:'en_cours',kind:'service'});find(manual,e=>e.tag==='input').checked=true;await find(manual,e=>e.text==='Vérifier et marquer résolu').onclick();assert.equal(requests.at(-1)[1].manual_tests,true);
 console.log('Resolution UI: explicit confirmation, revision identity, reopen reason, manual declaration and queued guard OK');
})().catch(e=>{console.error(e);process.exitCode=1});
