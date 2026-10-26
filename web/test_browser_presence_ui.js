const fs=require('fs'),vm=require('vm'),assert=require('assert');
const html=fs.readFileSync(__dirname+'/desktop.html','utf8');
const ctx={URLSearchParams,expectedClient:'pc A',expectedEnvironment:'env1',document:{visibilityState:'visible'}};vm.createContext(ctx);
vm.runInContext(html.slice(html.indexOf('function stateQuery('),html.indexOf('async function api(')),ctx);
let q=new URLSearchParams(ctx.stateQuery('state').slice(1));assert.equal(q.get('visible'),'1');assert.equal(q.get('client_serial'),'pc A');assert.equal(q.get('environment_id'),'env1');
ctx.document.visibilityState='hidden';q=new URLSearchParams(ctx.stateQuery('state').slice(1));assert(!q.has('visible'));assert.equal(q.get('client_serial'),'pc A');
assert.equal(ctx.stateQuery('action',{}),'');
ctx.document.visibilityState='visible';assert(!new URLSearchParams(ctx.stateQuery('files/state').slice(1)).has('visible'));
console.log('Browser presence: visibility, scope and read-only query OK');
