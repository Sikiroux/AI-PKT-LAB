const fs=require('fs'),vm=require('vm'),assert=require('assert');
const html=fs.readFileSync(__dirname+'/tickets.html','utf8');
const code=html.slice(html.indexOf('function ticketMatchesSearch('),html.indexOf('function render(){'));
class Element{constructor(tag,text,cls){this.tag=tag;this.text=text;this.cls=cls;this.children=[];this.attrs={}}append(...items){this.children.push(...items)}replaceChildren(...items){this.children=items}setAttribute(key,value){this.attrs[key]=value}focus(){this.focused=true}scrollIntoView(){this.scrolled=true}}
const host=new Element('div'),detail=new Element('article'),ctx={$:id=>id==='detail'?detail:host,el:(...args)=>new Element(...args),selected:'A',statuses:{en_cours:'En cours',nouveau:'Nouveau'},severities:{moderee:'Modérée'},orderedTickets:items=>items,ticketStageText:t=>t.stage,render:()=>ctx.rendered=true};vm.createContext(ctx);vm.runInContext(code,ctx);
const tickets=[{id:'A',title:'Documents inaccessibles',name:'PC-COMPTA-01',status:'en_cours',stage:'prepared',request_context:{requester:'Mina'}},{id:'B',title:'<script>texte</script>',status:'nouveau',stage:'queued'}];
ctx.renderTicketList(tickets);
const table=host.children[1];assert.equal(table.tag,'table');assert.equal(table.children[0].children[0].children.length,6);
const rows=table.children[1].children;assert.equal(rows.length,2);assert.equal(rows[0].cls,'selected');assert.equal(rows[0].children[1].text,'Mina');assert.equal(rows[0].children[2].text,'PC-COMPTA-01');assert.equal(rows[1].children[1].text,'Non renseigné');assert.equal(rows[1].children[2].text,'À identifier');
const button=rows[1].children[0].children[0];assert.equal(button.text,'B · <script>texte</script>');button.onclick();assert.equal(ctx.selected,'B');assert(ctx.rendered);
assert(detail.focused&&detail.scrolled);assert.equal(detail.attrs.tabindex,'-1');
ctx.renderTicketList([]);assert.equal(host.children.length,2);assert.equal(host.children[1].cls,'empty');
console.log('Ticket table: identity, legacy fallbacks, selection, safe text and empty state OK');

assert(ctx.ticketMatchesSearch(tickets[0],'mina'));assert(ctx.ticketMatchesSearch(tickets[0],'COMPTA'));assert(!ctx.ticketMatchesSearch(tickets[1],'mina'));assert(ctx.ticketMatchesSearch(tickets[1],''));
