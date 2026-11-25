const fs=require('fs'),vm=require('vm');
const fixtureSource=fs.readFileSync(__dirname+'/test_desktop_ui.js','utf8').split('(async()=>{')[0];
const scenario=`
Element.prototype.focus=function(){ctx.document.activeElement=this};
const saved=new Map();ctx.sessionStorage={getItem:key=>saved.get(key)||null,setItem:(key,value)=>saved.set(key,value)};
const originalFetch=ctx.fetch;ctx.fetch=async(url,options)=>{const response=await originalFetch(url,options);if(url.endsWith('files/action')&&JSON.parse(options.body).request.action==='list'){const data=await response.json();data.result.data.push({id:'second-file',name:'Zeta.txt',read_only:false});return {...response,json:async()=>data}}return response};
(async()=>{
 vm.runInContext('explorer()',ctx);await tick();const root=contents.at(-1),file=byButton(root,'Shared.txt'),open=byButton(root,'Ouvrir'),props=byButton(root,'Propriétés');
 assert(open.disabled);assert(props.disabled);const before=requests.length;
 file.onkeydown({key:'Home',preventDefault(){}});assert.equal(requests.length,before,'Keyboard selection never reads the file');assert.equal(file.attributes['aria-pressed'],'true');assert.equal(file.tabIndex,0);assert(!open.disabled);assert(!props.disabled);
 file.onkeydown({key:'ArrowDown',preventDefault(){}});const second=byButton(root,'Zeta.txt');assert.equal(second.attributes['aria-pressed'],'true');assert.equal(ctx.document.activeElement,second);second.onkeydown({key:'ArrowUp',preventDefault(){}});assert.equal(file.attributes['aria-pressed'],'true');file.onkeydown({key:'End',preventDefault(){}});assert.equal(second.attributes['aria-pressed'],'true');second.onkeydown({key:'Home',preventDefault(){}});assert.equal(file.attributes['aria-pressed'],'true');
 file.onkeydown({key:'Enter',altKey:true,preventDefault(){}});await tick();assert.equal(requests.length,before,'Alt+Enter shows list properties without network access');assert(!requests.some(([url,r])=>url.endsWith('files/action')&&r.request?.action==='read'));
 const search=find(root,e=>e.attributes['aria-label']==='Rechercher un fichier');search.value='absent';search.oninput();assert(open.disabled);assert(props.disabled);assert(find(root,e=>e.textContent==='Aucun résultat.'));
 search.value='Shared';search.oninput();assert(open.disabled,'Clearing a filter does not silently reselect its former hidden target');const visible=byButton(root,'Shared.txt');await visible.onclick();assert(!open.disabled);
 const shell=find(root,e=>e.className==='file-browser');shell.onkeydown({key:'f',ctrlKey:true,preventDefault(){}});assert.equal(ctx.document.activeElement,search);
 const rowsBefore=requests.length;shell.onkeydown({key:'F5',preventDefault(){}});await tick();assert.equal(requests.length,rowsBefore+2,'Refresh rereads shared state and listing, without opening content');assert(!requests.some(([url,r])=>url.endsWith('files/action')&&r.request?.action==='read'));
 byButton(root,'Shared.txt').onkeydown({key:'Enter',preventDefault(){}});await tick();assert(requests.some(([url,r])=>url.endsWith('files/action')&&r.request?.action==='read'),'Enter explicitly opens content');
 assert([...saved.entries()].some(([key,value])=>key.endsWith('explorer-shared')&&JSON.parse(value).search==='Shared'&&JSON.parse(value).highlight==='file'));vm.runInContext('localFiles()',ctx);await tick();const localRoot=contents.at(-1);assert.equal(find(localRoot,e=>e.attributes['aria-label']==='Rechercher un fichier').value,'','Local and shared searches are isolated');
 console.log('Explorer keyboard: read-only selection, properties, hidden-selection clearing, search focus, refresh and explicit opening OK');
})().catch(e=>{console.error(e);process.exitCode=1});
`;
vm.runInNewContext(fixtureSource+scenario,{require,__dirname,process,console,setImmediate,URLSearchParams},{filename:__filename});
