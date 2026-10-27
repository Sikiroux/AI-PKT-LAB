const fs=require('fs'),vm=require('vm'),assert=require('assert');
const html=fs.readFileSync(__dirname+'/tickets.html','utf8');
class E{
 constructor(tag,text,css=''){this.tagName=tag.toUpperCase();this.textContent=text||'';this.children=[];this.attrs={};this.dataset={};this.classList={contains:c=>css.split(' ').includes(c)}}
 append(...nodes){for(const n of nodes){if(n.parent)n.parent.children=n.parent.children.filter(x=>x!==n);this.children.push(n);n.parent=this}}
 setAttribute(k,v){this.attrs[k]=v}
 querySelector(s){return this.children.find(n=>'[aria-controls="'+n.attrs['aria-controls']+'"]'===s)}
 click(){this.onclick?.()}
 focus(){this.focused=true}
}
const ctx={el:(...a)=>new E(...a),siteIcon:()=>new E('svg'),ticketTabSelection:{},state:{site:{environment_id:'A'}}};
vm.createContext(ctx);vm.runInContext(html.slice(html.indexOf('function organiseTicketDetail'),html.indexOf('function renderFollowups')),ctx);
function build(id='T1',checks=[]){const d=new E('div'),title=new E('h3','Demande'),description=new E('p','Symptôme','desc'),context=new E('section','Ressource et résultat');context.dataset.ticketArea='request';const dialogue=new E('section','Échanges avec le demandeur'),controls=new E('details','Contrôles pédagogiques'),notes=new E('section','Compte rendu');notes.dataset.ticketArea='intervention';d.append(title,description,context,dialogue,controls,notes);ctx.organiseTicketDetail(d,{id,checks});return {d,description,context,dialogue,controls,notes,tabs:d.children.find(n=>n.attrs.role==='tablist'),panels:d.children.filter(n=>n.attrs.role==='tabpanel')}}
const a=build();assert.equal(a.panels.length,4);assert.equal(a.panels.filter(p=>!p.hidden).length,1);assert(a.panels[0].children.includes(a.description));assert(a.panels[0].children.includes(a.context));assert(!a.d.children.includes(a.description));assert(a.panels[1].children.includes(a.dialogue));assert(a.panels[2].children.includes(a.notes));assert(a.panels[3].children.includes(a.controls));
a.tabs.children[2].click();assert.equal(ctx.ticketTabSelection['A:T1'],'intervention');assert.equal(a.panels[2].hidden,false);assert.equal(a.tabs.children[2].attrs['aria-selected'],'true');assert.equal(a.panels[0].hidden,true);
assert.equal(build().panels[2].hidden,false,'Same company retains work pane');ctx.state.site.environment_id='B';assert.equal(build().panels[0].hidden,false,'Other company starts on the request');ctx.state.site.environment_id='A';
let prevented=0;a.tabs.children[2].onkeydown({key:'End',preventDefault(){prevented++}});assert.equal(a.panels[3].hidden,false);assert(a.tabs.children[3].focused);a.tabs.children[3].onkeydown({key:'ArrowRight',preventDefault(){prevented++}});assert.equal(a.panels[0].hidden,false);assert.equal(prevented,2);assert.equal(a.tabs.children[0].tabIndex,0);assert.equal(a.tabs.children[1].tabIndex,-1);
const b=build('T2',[{status:'valide'},{status:'inconnu'}]);const summary=b.d.children.find(n=>n.classList.contains('ticket-check-summary'));assert.equal(summary.dataset.tone,'unknown');assert(summary.textContent.includes('1 / 2'));summary.click();assert.equal(b.panels[3].hidden,false);assert.equal(b.panels.filter(p=>!p.hidden).length,1);
ctx.ticketTabSelection['A:T3']='obsolete';assert.equal(build('T3').panels[0].hidden,false,'Invalid remembered pane has a safe fallback');
console.log('Ticket detail: four panes, isolated request, environment-scoped persistence, keyboard tabs and read-only verification shortcut OK');
