const fs=require('fs'),vm=require('vm'),assert=require('assert');
class E{constructor(tag,text){this.tag=tag;this.text=text;this.children=[];this.dataset={};this.attrs={};this.value=''}append(...n){this.children.push(...n)}replaceChildren(...n){this.children=n}setAttribute(k,v){this.attrs[k]=v}}
const requests=[],dialogs=[],ctx={el:(t,x)=>new E(t,x),severities:{faible:'Faible',moderee:'Modérée',elevee:'Élevée',critique:'Critique'},act:async(p,d)=>{requests.push(d);return true},ticketActionButton:(parent,t,title,build)=>{const b=new E('button',title);b.onclick=()=>{const d=new E('dialog');d.close=()=>{};build(d);dialogs.push(d)};parent.append(b)}};vm.createContext(ctx);
const html=fs.readFileSync(__dirname+'/tickets.html','utf8');vm.runInContext(html.slice(html.indexOf('function renderTicketTimeline'),html.indexOf('function render(){')),ctx);
const find=(node,p)=>p(node)?node:node.children.map(c=>find(c,p)).find(Boolean);
(async()=>{
 const t={id:'T1',status:'en_cours',timeline:[{kind:'followup',date:'now',text:'<script>texte</script>',visibility:'private'}],tasks:[{id:'task-1',text:'Vérifier DNS',minutes:10,status:'todo',revision:2}],classification:{urgency:'moderee',impact:'faible',priority:'critique',suggested:'faible',source:'manual',reason:'Contrat prioritaire'}};
 const feed=new E('div');ctx.renderTicketTimeline(feed,t);assert(find(feed,n=>n.text==='<script>texte</script>'));find(feed,n=>n.text==='Suivis publics').onclick();assert(!find(feed,n=>n.text==='<script>texte</script>'));
 const host=new E('div');ctx.renderTicketTasks(host,t);const select=find(host,n=>n.tag==='select');select.value='done';await select.onchange();assert.equal(requests[0].task_id,'task-1');assert.equal(requests[0].expected_revision,2);assert.equal(requests[0].id,'T1');
 const closed=new E('div');ctx.renderTicketTasks(closed,{...t,status:'clos'});assert(find(closed,n=>n.tag==='select').disabled);assert(!find(closed,n=>n.text==='Ajouter une tâche'));
 const priority=new E('div');ctx.renderTicketPriority(priority,t);find(priority,n=>n.text==='Qualifier la priorité').onclick();const d=dialogs[0],selects=d.children.filter(n=>n.tag==='select');selects[0].value='critique';selects[1].value='critique';selects[0].onchange();assert.equal(selects[2].value,'critique');await find(d,n=>n.text==='Enregistrer la qualification').onclick();assert.equal(requests[1].action,'classify');assert.equal(requests[1].id,'T1');
 console.log('Ticket processing UI: safe timeline, filters, scoped tasks, read-only history and matrix OK');
})().catch(e=>{console.error(e);process.exit(1)});
