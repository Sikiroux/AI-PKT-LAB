const fs=require('fs'),vm=require('vm'),assert=require('assert');
class E{
 constructor(tag,text='',css=''){this.tagName=tag.toUpperCase();this.textContent=text||'';this.className=css;this.children=[];this.attrs={};this.dataset={};this.classList={add:c=>this.className+=' '+c}}
 append(...ns){for(const n of ns){n.remove();n.parentElement=this;this.children.push(n)}}
 prepend(...ns){this.append(...ns);this.children=[...ns,...this.children.filter(n=>!ns.includes(n))]}
 remove(){if(this.parentElement)this.parentElement.children=this.parentElement.children.filter(n=>n!==this);this.parentElement=null}
 replaceChildren(...ns){for(const n of this.children)n.parentElement=null;this.children=[];this.append(...ns)}
 before(n){const p=this.parentElement,i=p.children.indexOf(this);n.remove();n.parentElement=p;p.children.splice(i,0,n)}
 after(n){const p=this.parentElement,i=p.children.indexOf(this);n.remove();n.parentElement=p;p.children.splice(i+1,0,n)}
 setAttribute(k,v){this.attrs[k]=v}
 querySelectorAll(s){const all=this.children.flatMap(n=>[n,...n.querySelectorAll('*')]);return all.filter(n=>s==='*'||s.startsWith('.')&&n.className.split(' ').includes(s.slice(1))||s==='[data-ticket-pane="intervention"]'&&n.dataset.ticketPane==='intervention'||n.tagName.toLowerCase()===s)}
 querySelector(s){return this.querySelectorAll(s)[0]}
 close(){this.closed=true}
}
const html=fs.readFileSync(__dirname+'/tickets.html','utf8');let saved=false,lastPayload,exported=false;
const ctx={el:(...a)=>new E(...a),siteIcon:n=>new E('svg',n),drafts:{},activeTicketDialog:null,render(){},act:async(path,payload)=>{lastPayload=payload;return saved},renderTicketTasks:(d,t)=>d.append(new E('p','tasks '+t.id)),renderResolution:(d,t)=>d.append(new E('p','resolution '+t.id)),exportReport:()=>exported=true,ticketActionButton:(host,t,label,build)=>{const b=new E('button',label);b.onclick=()=>{const d=new E('dialog'),head=new E('div','','dialog-heading');head.append(new E('h3',label));d.append(head);ctx.activeTicketDialog=d;build(d)};host.append(b);return b}};
vm.createContext(ctx);vm.runInContext(html.slice(html.indexOf('function renderCompactIntervention'),html.indexOf('function renderFollowups')),ctx);vm.runInContext(html.slice(html.indexOf('function renderTicketNotes'),html.indexOf('function renderResolution')),ctx);
vm.runInContext(html.slice(html.indexOf('function renderTicketTasks'),html.indexOf('function renderTicketPriority')),ctx);
(async()=>{
 const main=new E('div'),pane=new E('section');pane.dataset.ticketPane='intervention';main.append(pane);const t={id:'T1',status:'en_cours',notes:'Texte enregistré',tasks:[]};ctx.renderCompactIntervention(main,t);
 assert(pane.querySelector('.intervention-toolbar'));assert.equal(pane.querySelectorAll('textarea').length,0);
 const btn=pane.querySelector('.intervention-toolbar').children[0];btn.onclick();let dialog=ctx.activeTicketDialog,field=dialog.querySelector('textarea');assert.equal(field.value,t.notes);assert(dialog.className.includes('report-editor'));
 field.value='Mes actions et résultats réellement observés';field.oninput();let save=dialog.querySelectorAll('button').find(b=>b.textContent==='Enregistrer le compte rendu');await save.onclick();assert.equal(lastPayload.action,'notes');assert(!dialog.closed);assert.equal(ctx.drafts.T1,field.value,'Refused save preserves draft');
 dialog.close();btn.onclick();dialog=ctx.activeTicketDialog;field=dialog.querySelector('textarea');assert.equal(field.value,ctx.drafts.T1,'Reopening restores draft');saved=true;save=dialog.querySelectorAll('button').find(b=>b.textContent==='Enregistrer le compte rendu');await save.onclick();assert(dialog.closed);assert.equal(ctx.drafts.T1,undefined);
 pane.querySelector('.intervention-export').onclick();assert(exported);
 pane.querySelector('.intervention-toolbar').children[1].onclick();const taskDialog=ctx.activeTicketDialog;
 taskDialog.querySelectorAll('button').find(b=>b.textContent==='Ajouter une tâche').onclick();assert(taskDialog.querySelector('textarea'),'Task entry opens inside the current modal');taskDialog.querySelector('textarea').value='Vérifier la file';await taskDialog.querySelectorAll('button').find(b=>b.textContent==='Créer la tâche').onclick();assert.equal(lastPayload.action,'task_add');assert(taskDialog.closed);

 ctx.renderCompactIntervention(main,{...t,status:'clos'});pane.querySelector('.intervention-toolbar').children[0].onclick();assert(ctx.activeTicketDialog.querySelector('textarea').readOnly);assert(!ctx.activeTicketDialog.querySelectorAll('button').some(b=>b.textContent==='Enregistrer le compte rendu'));
 ctx.renderCompactIntervention(main,{...t,stage:'queued'});assert(!pane.querySelector('.intervention-toolbar').children.some(b=>b.textContent==='Proposer une résolution'));
 console.log('Compact intervention: report modal, saved text, draft recovery, failed/successful save, export, closed read-only and queued guards OK');
})().catch(e=>{console.error(e);process.exitCode=1});
