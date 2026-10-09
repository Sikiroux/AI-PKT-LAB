const fs=require('fs'),vm=require('vm'),assert=require('assert');
const html=fs.readFileSync(__dirname+'/tickets.html','utf8');
class Element{constructor(){this.value='';this.open=false;this.listeners={};this.isConnected=true}focus(){this.focused=true}showModal(){this.open=true}close(){this.open=false;this.listeners.close?.()}setAttribute(k,v){this[k]=v}addEventListener(k,f){this.listeners[k]=f}}
const nodes={};for(const m of html.matchAll(/id="([^"]+)"/g))nodes[m[1]]=new Element();
const origin=new Element();let calls=0,resolve,reject,route,refreshes=0;
const ctx={$:id=>nodes[id],document:{activeElement:origin},busy:false,disable(v){ctx.busy=v},request(){calls++;return new Promise((a,b)=>{resolve=a;reject=b})},refresh:async()=>{refreshes++},loadEnvironments:async()=>{},page:n=>route=n,msg(){},renderContext(){},Date};
vm.createContext(ctx);vm.runInContext(html.slice(html.indexOf('let companyCreating='),html.indexOf("$('homeEquipment').onclick")),ctx);
(async()=>{
ctx.openCompanyDialog();assert(nodes.homeCreation.open);assert(nodes.newEnvironmentSeed.focused);ctx.closeCompanyDialog();assert(!nodes.homeCreation.open);assert(origin.focused);
ctx.openCompanyDialog();nodes.newEnvironmentSeed.value='  seed-1  ';const event={preventDefault(){}};const first=ctx.createCompany(event);assert.equal(calls,1);assert(nodes.newEnvironmentSeed.disabled);assert.equal(nodes.homeCreation['aria-busy'],'true');assert(!nodes.companyCreationStatus.hidden);
await ctx.createCompany(event);assert.equal(calls,1);ctx.closeCompanyDialog();assert(nodes.homeCreation.open);let cancelled=false;nodes.homeCreation.listeners.cancel({preventDefault(){cancelled=true}});assert(cancelled);
reject(new Error('Création impossible'));await first;assert(nodes.homeCreation.open);assert(!nodes.companyCreationError.hidden);assert.equal(nodes.companyCreationError.textContent,'Création impossible');assert.equal(nodes.newEnvironmentSeed.value,'  seed-1  ');assert(!nodes.newEnvironmentSeed.disabled);assert(!ctx.busy);
const second=ctx.createCompany(event);resolve({});await second;assert.equal(calls,2);assert(!nodes.homeCreation.open);assert.equal(nodes.newEnvironmentSeed.value,'');assert.equal(route,'tickets');assert.equal(refreshes,1);
assert(html.includes('<dialog id="homeCreation"'));assert(html.includes('backdrop-filter:blur(5px)'));assert(html.includes('prefers-reduced-motion'));console.log('Company dialog: focus, cancellation, duplicate-submit guard, loading, failure retry and success OK');
})().catch(e=>{console.error(e);process.exitCode=1});
