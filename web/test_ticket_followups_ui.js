const fs=require('fs'),vm=require('vm'),assert=require('assert');
const html=fs.readFileSync(__dirname+'/tickets.html','utf8');
const source=html.slice(html.indexOf('function renderFollowups('),html.indexOf('function render(){'));
class Element{constructor(tag,text,css){this.tag=tag;this.text=text;this.css=css;this.children=[];this.attrs={};this.value=''}append(...children){this.children.push(...children)}setAttribute(k,v){this.attrs[k]=v}}
const requests=[],messages=[],ctx={el:(...args)=>new Element(...args),followupDrafts:{},state:{site:{environment_id:'A'}},msg:(...args)=>messages.push(args),render:()=>{},act:async(path,data)=>{requests.push([path,data]);return ctx.success}};ctx.success=false;vm.createContext(ctx);vm.runInContext(source,ctx);
const find=(node,pred)=>pred(node)?node:node.children.map(n=>find(n,pred)).find(Boolean);
(async()=>{
 const ticket={id:'T1',status:'en_cours',assigned_to:'Technicien de la session',followups:[{kind:'followup',date:'2026-10-09',author:'Technicien',text:'<script>reste du texte</script>'}]};
 const host=new Element('div');ctx.renderFollowups(host,ticket);
 assert(find(host,n=>n.text==='<script>reste du texte</script>'),'History is text, not injected markup');
 assert(find(host,n=>n.text==='Attribué à : Technicien de la session'));
 const text=find(host,n=>n.tag==='textarea'),kind=find(host,n=>n.tag==='select'),send=find(host,n=>n.text==='Ajouter au suivi');
 await send.onclick();assert.equal(requests.length,0,'Empty submission stays local');
 text.value='Correction proposée';kind.value='solution';text.oninput();
 await send.onclick();assert.equal(ctx.followupDrafts['A:T1'].text,'Correction proposée','Failed POST keeps draft');assert.equal(requests[0][1].entry_kind,'solution');assert.equal(requests[0][1].id,'T1');
 ctx.state.site.environment_id='B';const switched=new Element('div');ctx.renderFollowups(switched,ticket);assert.equal(find(switched,n=>n.tag==='textarea').value,'','Same ticket ID in another environment must not inherit draft');ctx.state.site.environment_id='A';
 ctx.success=true;await send.onclick();assert(!ctx.followupDrafts['A:T1'],'Successful POST clears sent draft');
 const closed=new Element('div');ctx.renderFollowups(closed,{...ticket,status:'clos'});assert(!find(closed,n=>n.tag==='textarea'));assert(find(closed,n=>n.text==='Historique conservé en lecture seule.'));
 const legacy=new Element('div');ctx.renderFollowups(legacy,{id:'old',status:'nouveau'});assert(find(legacy,n=>n.text==='Aucun suivi enregistré.'));assert(find(legacy,n=>n.text==='Attribué à : Non attribué'));
 console.log('Ticket followups: safe history, draft retention, target identity, legacy and closed states OK');
})().catch(e=>{console.error(e);process.exitCode=1});
