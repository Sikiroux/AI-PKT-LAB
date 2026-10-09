const fs=require('fs'),vm=require('vm'),assert=require('assert');
const html=fs.readFileSync(__dirname+'/tickets.html','utf8');
class Element{constructor(tag='div',text){this.tag=tag;this.textContent=text||'';this.children=[];this.dataset={};this.value='';this.attrs={};this.hidden=false}append(...items){this.children.push(...items)}replaceChildren(...items){this.children=items}setAttribute(k,v){this.attrs[k]=v}focus(){this.focused=true}click(){if(this.onclick)this.onclick()}}
const nodes={};for(const id of [...html.matchAll(/id="([^"]+)"/g)].map(m=>m[1]))nodes[id]=new Element();
const names=['overview','devices','file','diagnostic'],tabs=names.map(n=>{const t=nodes['site-tab-'+n];t.dataset.siteTab=n;return t});
const ctx={$:id=>nodes[id],el:(tag,text)=>new Element(tag,text),document:{activeElement:null,createElement:tag=>new Element(tag),querySelectorAll:query=>query==='[data-site-tab]'?tabs:[]},state:{connected:false,site:null}};
vm.createContext(ctx);vm.runInContext(html.slice(html.indexOf('function selectSiteTab('),html.indexOf('refresh().catch')),ctx);
ctx.selectSiteTab('devices');assert(!nodes['site-devices'].hidden);assert(nodes['site-overview'].hidden);assert.equal(nodes['site-tab-devices'].attrs['aria-selected'],'true');
let prevented=false;tabs[1].onkeydown({key:'ArrowRight',preventDefault(){prevented=true}});assert(prevented);assert(nodes['site-tab-file'].focused);assert(!nodes['site-file'].hidden);
ctx.renderSiteOverview();assert.equal(nodes.siteBridgeStat.textContent,'Déconnecté');assert.equal(nodes.siteFileName.textContent,'Aucun fichier associé');assert(nodes.siteCopyPath.disabled);
ctx.state.site={file:'C:\\Formation\\entreprise.pkt',inventory_at:'2026-10-09 06:45:00',inventory:[{name:'PC-01',model:'PC-PT',present:true,ports:[{ip:'10.0.0.1'}]},{name:'SRV-01',model:'Server-PT',present:false,ports:[{ip:'10.0.0.2'}]}]};
nodes.siteDeviceSearch.value='srv';ctx.renderSiteOverview();assert.equal(nodes.siteFileName.textContent,'entreprise.pkt');assert.equal(nodes.siteInventoryStat.textContent,'1');assert.equal(nodes.siteInventoryCount.textContent,'1 équipement(s) affiché(s) sur 2');assert(!nodes.siteCopyPath.disabled);
vm.runInContext(html.slice(html.indexOf('function renderInventory('),html.indexOf('function ticketMatchesSearch(')),ctx);ctx.renderInventory();assert.equal(nodes.inventoryTable.children[0].children.length,2);assert.equal(nodes.inventoryTable.children[0].children[1].children[0].textContent,'SRV-01');
let copied=0,checked=0;nodes.copyContextPath.onclick=()=>copied++;nodes.checkReady.onclick=()=>checked++;nodes.siteCopyPath.click();nodes.siteRunDiagnostic.click();assert.equal(copied,1);assert.equal(checked,1);
console.log('Site tabs: keyboard navigation, unknown state, actual inventory, search, file path and shared actions OK');
