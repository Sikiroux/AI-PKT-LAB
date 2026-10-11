const fs=require('fs'),vm=require('vm'),assert=require('assert');
const html=fs.readFileSync(__dirname+'/tickets.html','utf8'),start=html.indexOf('function ticketHints('),end=html.indexOf("const base",start);
const ctx={};vm.createContext(ctx);vm.runInContext(html.slice(start,html.indexOf("\n}",start)+3),ctx);
for(const family of ['ad','dns','files','printing','ftp','peripherals','onboarding','pc','wifi']){
 const hints=ctx.ticketHints({live_family:family,name:'PC-TEST'});assert.equal(hints.length,3);assert(hints.every(s=>s.length>50));
}
assert(ctx.ticketHints({arrival_plan:{target:'dns'},name:'PC-TEST'})[0].includes('résolution'));
assert(ctx.ticketHints({live_family:'endpoint',name:'PC-TEST'})[1].includes('quota'));
assert.notDeepEqual(ctx.ticketHints({live_family:'printing'}),ctx.ticketHints({live_family:'ftp'}));
console.log('Hints: service-specific diagnosis, validation and legacy workstation paths OK');
