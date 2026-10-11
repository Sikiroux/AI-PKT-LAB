const fs=require('fs'),vm=require('vm'),assert=require('assert');
const html=fs.readFileSync(__dirname+'/desktop.html','utf8');
let notice;const ctx={document:{getElementById:()=>notice,createElement:()=>({style:{},setAttribute(){}}),body:{append(n){notice=n}}}};
vm.createContext(ctx);
for(const name of ['transportNotice','networkNotice']){const start=html.indexOf('function '+name+'(');vm.runInContext(html.slice(start,html.indexOf('\n',start)),ctx)}
ctx.transportNotice('Preuve périmée',false);assert.equal(notice.style.pointerEvents,'none');assert.equal(notice.style.inset,'12px 12px auto');
ctx.transportNotice('Échec constaté',true);assert.equal(notice.style.pointerEvents,'auto');assert.equal(notice.style.inset,'0');
ctx.transportNotice('');assert.equal(notice.style.display,'none');
const message=ctx.networkNotice({network_health:{reason:'expired',last_known_status:'passed',last_known_at:100}});
assert(message.includes('périmée'));assert(message.includes('Dernier résultat'));assert(message.includes('nouveau contrôle'));
assert(ctx.networkNotice({network_health:{reason:'transport'}}).includes('indisponible'));
console.log('Network monitor UI: non-blocking uncertainty, explicit failure, dated history and fresh-check requirement OK');
