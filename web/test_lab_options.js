const fs=require('fs'),vm=require('vm'),assert=require('assert');
const html=fs.readFileSync(__dirname+'/tickets.html','utf8');
const start=html.indexOf('function labOptions()'),end=html.indexOf('async function labRefresh',start);
const select={value:'example',options:[],replaceChildren(){this.options=[]},append(o){this.options.push(o)}};
const ctx={$:id=>id==='labScenario'?select:{value:id==='labMode'?'atelier':'2'},el:()=>({}),labState:{catalogue:[{id:'example',title:'Lab',topology:'lan',mode:'atelier',level:1},{id:'other',mode:'depannage',level:1}]}};
vm.createContext(ctx);vm.runInContext(html.slice(start,end),ctx);ctx.labOptions();
assert.equal(select.options.length,2);assert.equal(select.value,'example');
ctx.labState.catalogue=[];ctx.labOptions();assert.equal(select.options.length,1);
console.log('Lab catalogue: standalone refresh, filtering and empty state OK');
