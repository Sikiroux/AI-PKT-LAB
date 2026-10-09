const fs=require('fs'),vm=require('vm'),assert=require('assert');
const html=fs.readFileSync(__dirname+'/tickets.html','utf8'),source=html.match(/async function refresh\(\)\{[^\n]+/)[0];
let next={site:{environment_id:'B'},tickets:[]},pins=[],populates=0;
const ctx={state:{site:{environment_id:'A'}},selected:'old',drafts:{same:'Old notes'},followupDrafts:{same:'Old followup'},reopenDrafts:{same:'Old reason'},clientTargetsEnvironment:'A',request:async()=>next,render(){},renderPinnedTicket:force=>pins.push(force),populateClientTargets:async()=>populates++};vm.createContext(ctx);vm.runInContext(source,ctx);
(async()=>{await ctx.refresh();assert.equal(ctx.selected,null);for(const key of ['drafts','followupDrafts','reopenDrafts'])assert.equal(Object.keys(ctx[key]).length,0,'Changing company resets '+key);assert.equal(populates,1);assert.equal(pins[0],true);
ctx.selected='T2';ctx.drafts.T2='In progress';ctx.followupDrafts.T2='Draft';ctx.reopenDrafts.T2='Reason';await ctx.refresh();assert.equal(ctx.selected,'T2');assert.equal(ctx.drafts.T2,'In progress');assert.equal(ctx.followupDrafts.T2,'Draft');assert.equal(populates,1,'Same company keeps target catalogue');
console.log('Ticket refresh: environment isolation, draft retention in same company and forced post-action panel refresh OK');})().catch(e=>{console.error(e);process.exitCode=1});
