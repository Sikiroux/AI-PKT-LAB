const fs=require('fs'),vm=require('vm'),assert=require('assert');
const html=fs.readFileSync(__dirname+'/tickets.html','utf8');
class E{constructor(){this.children=[];this.textContent='';this.style={}}append(...c){this.children.push(...c)}replaceChildren(...c){this.children=c}}
let fail='',refreshFail=false,blocked=false,calls=0,refreshes=0,opened=0,release,hold=false,lastMessage='',lastTab;
const ctx={busy:false,state:{site:{environment_id:'A'}},window:{open(){opened++;if(blocked)return null;return lastTab={closed:false,location:{href:''},document:{body:new E(),createElement:()=>new E()},opener:{}}}},request:async()=>{calls++;if(hold)await new Promise(r=>release=r);if(fail)throw Error(fail);return{}},refresh:async()=>{refreshes++;if(refreshFail)throw Error('Liste indisponible')},disable:v=>ctx.busy=v,msg:t=>lastMessage=t,encodeURIComponent,console};
vm.createContext(ctx);vm.runInContext(html.slice(html.indexOf('async function openTicketDesktop'),html.indexOf('async function act(')),ctx);
const ticket={name:'PC-DIR-02',target_serial:'serial 5'};
(async()=>{
 fail='Bureau simulé inconnu pour ce poste.';await ctx.openTicketDesktop(ticket);assert(lastTab.document.body.children[0].children.some(e=>e.textContent===fail));assert.equal(lastTab.location.href,'');assert(lastMessage.includes(fail));assert(!ctx.busy);
 fail='';refreshFail=true;await ctx.openTicketDesktop(ticket);assert.equal(lastTab.location.href,'/workspace/desktop?client_serial=serial%205#A');assert.equal(lastTab.opener,null);assert(lastMessage.includes('Poste ouvert ; actualisation'));assert(!lastTab.closed);
 blocked=true;const old=calls;await ctx.openTicketDesktop(ticket);assert.equal(calls,old);assert(lastMessage.includes('navigateur bloque'));blocked=false;refreshFail=false;
 hold=true;const pending=ctx.openTicketDesktop(ticket);await Promise.resolve();const count=opened;await ctx.openTicketDesktop(ticket);assert.equal(opened,count);ctx.state.site.environment_id='B';release();await pending;hold=false;assert.equal(lastTab.location.href,'');assert(lastMessage.includes('entreprise active a changé'));assert(!ctx.busy);
 console.log('Ticket remote opening: rejection retained, blocked popup, refresh isolation, double click and environment switch OK');
})().catch(e=>{console.error(e);process.exitCode=1});
