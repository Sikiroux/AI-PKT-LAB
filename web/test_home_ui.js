const fs=require('fs'),vm=require('vm'),assert=require('assert');
const html=fs.readFileSync(__dirname+'/tickets.html','utf8');
class Element{constructor(tag,text){this.tag=tag;this.textContent=text||'';this.children=[];this.dataset={};this.value=''}append(...items){this.children.push(...items)}replaceChildren(...items){this.children=items}click(){this.onclick?.()}}
const nodes={};for(const m of html.matchAll(/id="([^"]+)"/g))nodes[m[1]]=new Element('div');
let page,tab,selected;
const ctx={$:id=>nodes[id],el:(tag,text)=>new Element(tag,text),siteIcon:name=>new Element('svg',name),state:{site:null,tickets:[],connected:false},statuses:{en_cours:'En cours',nouveau:'Nouveau'},page:n=>page=n,selectSiteTab:n=>tab=n,render(){selected=ctx.selected},renderInventory(){},renderSiteOverview(){}};
vm.createContext(ctx);vm.runInContext(html.slice(html.indexOf('function renderHome('),html.indexOf("$('homeCheck').onclick")),ctx);
ctx.renderHome(null,false);assert(nodes.homeCheck.disabled);assert.equal(nodes.homeNext.children[0].textContent,'Bienvenue dans ton espace de travail');
ctx.state.site={name:'Entreprise',file:'C:\\Lab\\site.pkt',inventory:[{}],ready:{status:'unknown'}};ctx.state.connected=true;
const t={id:'INC-02',status:'nouveau',title:'Accès',description:'Symptôme',request_context:{requester:'Nora',station:'PC-CPT-03'},created:'2026-10-09'};ctx.state.tickets=[t];ctx.renderHome(t,true);
assert.equal(nodes.homeNext.children[0].textContent,'PROCHAIN TICKET À TRAITER');assert.equal(nodes.homeNetworkFile.textContent,'site.pkt');assert.equal(nodes.homeHealth.children[1].children.at(-1).textContent,'À vérifier');assert.equal(nodes.homeHealth.children[2].dataset.tone,'unknown');
nodes.homeNext.children.at(-1).children[1].click();assert.equal(page,'site');assert.equal(tab,'devices');assert.equal(nodes.siteDeviceSearch.value,'PC-CPT-03');
nodes.homeNext.children.at(-1).children[0].click();assert.equal(page,'tickets');assert.equal(selected,'INC-02');
t.status='en_cours';ctx.renderHome(t,true);assert.equal(nodes.homeNext.children[0].textContent,'INTERVENTION EN COURS');ctx.renderHome(null,true);assert.equal(nodes.homeNext.children[0].textContent,'Aucun ticket ouvert');
console.log('Home: empty states, ticket status, target station, navigation and unverified network OK');
