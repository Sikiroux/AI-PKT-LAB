const fs=require('fs'),vm=require('vm'),assert=require('assert');
const html=fs.readFileSync(__dirname+'/tickets.html','utf8');
class Element{constructor(tag,text,css){this.tagName=tag;this.textContent=text||'';this.className=css||'';this.children=[]}append(...nodes){this.children.push(...nodes)}}
const ctx={el:(...args)=>new Element(...args)};vm.createContext(ctx);vm.runInContext(html.slice(html.indexOf('function appendRequestContext'),html.indexOf('function isPreparedTicket')),ctx);
function texts(e){return [e.textContent,...e.children.flatMap(texts)]}
const ticket={request_context:{requester:'Mina',station:'PC-CPT-05',serial:'SN5',complaint:'Impossible d’ouvrir le partage',resource:'\\\\SRV-FILES\\Documents',resource_scope:'remote',expected_result:'Ouvrir le document',urgency_label:'Activité bloquée',priority_reason:'Travail en attente'},impact:{affected_count:1}};
const host=new Element('aside');ctx.appendRequestContext(host,ticket);assert(texts(host).includes(ticket.request_context.resource));assert(texts(host).includes('Ressource distante'));assert(texts(host).includes('Ouvrir le document'));assert(!texts(host).includes('Urgence déclarée'),'Impact is not repeated');const details=host.children.find(x=>x.tagName==='details');assert(details);assert(texts(details).includes('Numéro de série : SN5'));
const legacy=new Element('aside');ctx.appendRequestContext(legacy,{request_context:{requester:'Alex',station:'PC-01',complaint:'Ancien signalement'}});assert(!texts(legacy).includes('undefined'));assert(texts(legacy).includes('Numéro de série : Non renseigné'));assert(texts(legacy).includes('À qualifier'));ctx.appendRequestContext(legacy,{});
console.log('Ticket context: resource, expected result, folded metadata, no duplicate urgency and legacy fallback OK');
