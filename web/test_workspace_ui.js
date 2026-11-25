// Role/target selection checks for the workstation list (no browser dependency).
const fs=require('fs'),vm=require('vm'),assert=require('assert');
class Element{constructor(tag){this.tagName=tag;this.children=[];this.value='';this.attributes={};this.classList={remove(){},add(){}}}append(...v){this.children.push(...v)}replaceChildren(...v){this.children=[...v]}setAttribute(k,v){this.attributes[k]=v}getAttribute(k){return this.attributes[k]}removeAttribute(k){delete this.attributes[k]}set src(v){this.attributes.src=v}}
const dom=new Map(),get=id=>{if(!dom.has(id))dom.set(id,new Element('div'));return dom.get(id)};
const ctx={window:{self:1,top:1},document:{getElementById:get,createElement:t=>new Element(t),querySelectorAll:()=>[get('connectTarget'),get('openTechnician')]}};vm.createContext(ctx);
const html=fs.readFileSync(__dirname+'/workspace.html','utf8'),script=html.match(/<script>([\s\S]*?)<\/script>/)[1].split('async function state()')[0];vm.runInContext(script,ctx);
const s={environment_id:'one',company:'Agence',seed:'seed',remote_session:false,checks:{remote:{allowed:false}},workstations:[{name:'PC-COMPTA',serial:'client',role:'client',remote_supported:true,remote_connected:false,ticket_target:true,user:'Alice',ip:'192.168.1.20',status:'passed'},{name:'PC-STOCK',serial:'other',role:'client',remote_supported:false,user:'Bob',ip:'192.168.1.30',status:'unknown'},{name:'LT-TECH',serial:'tech',role:'technician',remote_supported:false,user:'Technicien',ip:'192.168.1.40',status:'passed'}]};ctx.s=s;vm.runInContext('render(s)',ctx);
assert.equal(get('workstationList').children.length,2,'Technician has separate entry');assert.equal(get('connectTarget').textContent,'Prendre la main sur PC-COMPTA');assert(get('workstationList').children[1].disabled,'PT inventory entry without simulated desktop cannot connect');
get('workstationSearch').value='bob';vm.runInContext('render(s)',ctx);assert.equal(get('workstationList').children.length,1);assert.equal(get('connectTarget').textContent,'Prendre la main sur PC-COMPTA','Filtering must not silently change connection target');
get('workstationSearch').value='notfound';vm.runInContext('render(s)',ctx);assert.equal(get('workstationList').children[0].textContent,'Aucun poste ne correspond à cette recherche.');
s.environment_id='two';vm.runInContext('render(s)',ctx);assert.equal(get('workstationSearch').value,'','New environment clears old search');assert.equal(get('workstationList').children.length,2);
s.remote_session=true;s.checks.remote.allowed=true;s.workstations[0].remote_connected=true;vm.runInContext('render(s)',ctx);assert.equal(get('osjsDesktop').getAttribute('src'),'__API_BASE__/desktop?client_serial=client#two');s.checks.remote.allowed=false;s.workstations[0].status='unknown';vm.runInContext('render(s)',ctx);assert.equal(get('osjsDesktop').getAttribute('src'),'__API_BASE__/desktop?client_serial=client#two','Unknown proof preserves the loaded remote desktop');assert.equal(get('desktop').hidden,false);s.checks.remote.allowed=false;s.workstations[0].status='failed';vm.runInContext('render(s)',ctx);assert.equal(get('desktop').hidden,false);assert.equal(get('osjsDesktop').getAttribute('src'),'__API_BASE__/desktop?client_serial=client#two','Failure suspends actions but preserves remote windows');
vm.runInContext('render(null)',ctx);assert(get('connectTarget').disabled);assert.equal(get('workstationList').children.length,0);
console.log('Workstation list: separate technician, supported targets, search identity, environment reset, connection loss and empty state OK');

// A failed connection must show the backend diagnostic, without a success banner.
get('notice').scrollIntoView=()=>{get('notice').scrolled=true;};
ctx.fetch=async(url,opts)=>opts?{ok:false,json:async()=>({error:'Contrôle discret : registerEvent donePing : invalid string position'})}:{ok:false};
vm.runInContext(html.match(/<script>([\s\S]*?)<\/script>/)[1].split('async function state()')[1].split("$('workstationSearch').oninput")[0].replace(/^/, 'async function state()'),ctx);
(async()=>{await vm.runInContext("call('action',{action:'connect'})",ctx);assert(get('notice').textContent.includes('registerEvent donePing'));assert(get('notice').scrolled);console.log('Connection refusal: backend error remains visible and scrolled into view OK');})().catch(e=>{console.error(e);process.exitCode=1;});

// Registry identity is read-only and follows the selected serial.
s.environment_id='one';s.workstations[0].employee_id='employee-1';s.workstations[0].asset_id='asset-1';
s.company_registry={people:{'employee-1':{id:'employee-1',display_name:'Mina',username:'mina.compta',account_id:'u1',account_present:true}},assets:{'asset-1':{id:'asset-1',name:'PC-COMPTA',serial:'client'}}};
vm.runInContext('render(s)',ctx);assert.equal(get('identityCard').hidden,false);assert(get('identitySummary').children.some(x=>x.textContent==='Compte : mina.compta'));assert(get('identityReferences').textContent.includes('Compte : u1'));
vm.runInContext('render(null)',ctx);assert(get('identityCard').hidden);assert.equal(get('identityReferences').textContent,'');
console.log('Registry identity: account linkage follows target and clears on environment loss OK');
let embeddedClass='';const embeddedContext={window:{self:1,top:2},document:{body:{classList:{add:c=>embeddedClass=c}},getElementById:get}};vm.createContext(embeddedContext);vm.runInContext(script,embeddedContext);assert.equal(embeddedClass,'workspace-embedded');console.log('Embedded overview: parent window detected without changing standalone display OK');
