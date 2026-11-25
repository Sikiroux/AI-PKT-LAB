const fs=require('fs'),vm=require('vm'),assert=require('assert');
const html=fs.readFileSync(__dirname+'/tickets.html','utf8');
class E{constructor(tag,text){this.tag=tag;this.textContent=text||'';this.children=[];this.dataset={}}append(...c){this.children.push(...c)}}
const ctx={el:(t,s)=>new E(t,s),state:{site:{environment_id:'test & site'}},encodeURIComponent};vm.createContext(ctx);vm.runInContext(html.slice(html.indexOf('function renderTicketGuide'),html.indexOf('function organiseTicketDetail')),ctx);
const root=new E('div');ctx.renderTicketGuide(root,{name:'PC-TEST'});const text=e=>e.textContent+' '+e.children.map(text).join(' '),all=text(root);assert.equal(root.children[0].dataset.ticketArea,'guide');assert(all.includes('Desktop → IP Configuration'));assert(all.includes('Pont connecté'));assert(all.includes('Inactive'));assert(all.includes('documentation')||all.includes('Documentation'));assert(all.includes('plusieurs causes possibles'));const flatten=e=>[e,...e.children.flatMap(flatten)];const link=flatten(root).find(e=>e.tag==='a');assert.equal(link.href,'/workspace/technician?app=documentation#test%20%26%20site');assert.equal(link.rel,'noopener');assert(!all.includes('Formation!2026'),'Guide does not embed credentials');assert(html.includes("['guide','Guide','file']"));assert(html.includes('renderTicketGuide(d,t);organiseTicketDetail(d,t)'));assert(html.includes('Commencer la simulation'));console.log('Ticket guide: information locations, blocked access method, safe documentation link and integration OK');

const dnsRoot=new E('div');ctx.renderTicketGuide(dnsRoot,{name:'PC-DNS',live_family:'dns'});const dnsLinks=flatten(dnsRoot).filter(e=>e.tag==='a');assert(dnsLinks.some(e=>e.href.includes('article=dns#')));assert(dnsLinks.some(e=>e.href.includes('article=company-network#')));assert(dnsLinks.every(e=>e.rel==='noopener'));assert(!text(dnsRoot).includes('Formation!2026'));
const printRoot=new E('div');ctx.renderTicketGuide(printRoot,{workspace_goal:'print'});assert(flatten(printRoot).some(e=>e.tag==='a'&&e.href.includes('article=printing#')));
for(const family of ['endpoint','ad','dns','files','printing','ftp','peripherals']){
 const ticket={live_family:family,name:'PC-TEST',cause:'PRIVATE_CAUSE',injection:{secret:'PRIVATE_SECRET'}};
 const plan=ctx.ticketDiagnosticPlan(ticket);assert.equal(plan.checks.length,3);assert(plan.tool);assert(plan.article);
 const changed=ctx.ticketDiagnosticPlan({...ticket,cause:'OTHER_CAUSE',injection:{secret:'OTHER_SECRET'}});assert.deepEqual(plan,changed,'Guide must not depend on the private fault');
 const host=new E('div');ctx.renderTicketGuide(host,ticket);const content=text(host);assert(content.includes('Commencer ici'));assert(!content.includes('PRIVATE_CAUSE'));assert(!content.includes('PRIVATE_SECRET'));
 assert(flatten(host).some(e=>e.tag==='a'&&e.href.includes('app='+plan.tool+'#')));
}
assert.equal(ctx.ticketDiagnosticPlan({workspace_goal:'print'}).tool,'printing');assert.equal(ctx.ticketDiagnosticPlan({workspace_goal:'download'}).tool,'ftp');
const checks=(config,remote,server)=>[{label:'Configuration IPv4 de référence rétablie',status:config},{label:'Poste joignable depuis le technicien',status:remote},{label:'Serveur joignable depuis le poste',status:server}];
assert.equal(ctx.ticketNetworkInterpretation({}).tone,'unknown');
assert.equal(ctx.ticketNetworkInterpretation({checks:checks('valide','valide','inconnu')}).tone,'unknown');
assert.equal(ctx.ticketNetworkInterpretation({checks:checks('valide','valide','valide')}).tone,'passed');
assert(ctx.ticketNetworkInterpretation({checks:checks('non satisfait','valide','non satisfait')}).text.includes('masque'));
assert(ctx.ticketNetworkInterpretation({checks:checks('non satisfait','valide','valide')}).text.includes('configuration IPv4'));
const summary=new E('div');ctx.renderTicketNetworkSummary(summary,{live_family:'network',checks:checks('valide','valide','valide'),checked:'2026-10-27 10:00'});assert(text(summary).includes('pas une surveillance en direct'));assert(text(summary).includes('2026-10-27 10:00'));
const noNetwork=new E('div');ctx.renderTicketNetworkSummary(noNetwork,{live_family:'dns'});assert.equal(noNetwork.children.length,0);
