const {app,BrowserWindow,dialog,screen}=require('electron');
const {spawn}=require('node:child_process');
const fs=require('node:fs'),path=require('node:path'),http=require('node:http'),net=require('node:net');
const {ORIGIN,allowed,windowKey,bounds}=require('./policy.cjs');
const {Workspaces}=require('./workspaces.cjs');const workspaces=new Workspaces();
const root=path.resolve(__dirname,'..');let backend,main,exiting=false,closing=false,preferences={};
const diagnosticMode=process.env.NETOPS_MEMORY_DIAGNOSTIC==='1';
if(diagnosticMode){
 const os=require('node:os');
 const profile=path.join(app.getPath('appData'),'NetOps-Diagnostics');
 fs.mkdirSync(profile,{recursive:true});
 app.setPath('userData',profile);
 // Each launch has a writable Chromium cache, separate from normal NetOps.
 app.setPath('sessionData',fs.mkdtempSync(path.join(os.tmpdir(),'netops-diagnostic-cache-')));
}
const lock=app.requestSingleInstanceLock();
if(!lock)app.quit();
else{
 app.on('second-instance',()=>{if(main){if(main.isMinimized())main.restore();main.show();main.focus()}});
 app.whenReady().then(start).catch(async e=>{await dialog.showMessageBox({type:'error',message:'Démarrage impossible',detail:e.message});exiting=true;if(backend)backend.kill();app.quit()});
 app.on('before-quit',e=>{if(!exiting&&main&&!main.isDestroyed()){e.preventDefault();main.close()}});
 app.on('window-all-closed',()=>{if(exiting)app.quit()});
}
function preferencesPath(){return path.join(app.getPath('userData'),'windows.json')}
function save(){try{fs.writeFileSync(preferencesPath(),JSON.stringify(preferences))}catch{}}
function configure(win,key,isMain=false,initialURL=null){
 if(initialURL)workspaces.track(win,initialURL);
 const remembered=preferences[key];
 win.setMenuBarVisibility(false);
 win.webContents.setWindowOpenHandler(({url})=>workspaces.reuse(url)?{action:'deny'}:allowed(url,true)?{action:'allow',outlivesOpener:true,overrideBrowserWindowOptions:{...bounds(preferences[windowKey(url)],screen.getAllDisplays()),autoHideMenuBar:true,show:false,webPreferences:{nodeIntegration:false,contextIsolation:true,sandbox:true}}}:{action:'deny'});
 win.webContents.on('will-navigate',(e,url)=>{if(!allowed(url))e.preventDefault()});
 win.webContents.on('will-redirect',(e,url)=>{if(!allowed(url))e.preventDefault()});
 win.webContents.on('did-create-window',(child,{url})=>configure(child,windowKey(url),false,url));
 // An about:blank placeholder can acquire its final URL asynchronously.
 win.webContents.on('did-navigate',(_,url)=>{if(allowed(url)){workspaces.track(win,url);key=isMain?'main':windowKey(url);const restored=preferences[key];if(!isMain&&restored){win.setBounds(bounds(restored,screen.getAllDisplays()));if(restored.maximized)win.maximize()}}});
 win.once('ready-to-show',()=>{if(remembered?.maximized)win.maximize();win.show()});
 const remember=()=>{if(win.isDestroyed()||win.isMinimized())return;preferences[key]={...win.getNormalBounds(),maximized:win.isMaximized()};save()};
 win.on('resize',remember);win.on('move',remember);win.on('maximize',remember);win.on('unmaximize',remember);
 if(isMain)win.on('close',e=>{if(exiting)return;e.preventDefault();requestQuit()});
}
async function requestQuit(){
 if(closing)return;closing=true;
 try{
  const answer=await dialog.showMessageBox(main,{type:'question',buttons:['Continuer à travailler','Quitter le simulateur'],defaultId:0,cancelId:0,message:'Quitter le simulateur et fermer ses bureaux ?',detail:'Les données enregistrées sont conservées. Enregistre les brouillons ouverts avant de quitter.'});
  if(answer.response!==1)return;
  const result=await main.webContents.executeJavaScript(`(async()=>{const r=await fetch('/quit',{method:'POST',headers:{'Content-Type':'application/json','X-Diagnostic-Token':TOKEN},body:'{}'});const v=await r.json();return {ok:r.ok,message:v.error||v.message};})()`);
  if(!result.ok)throw Error(result.message||'Arrêt refusé');
  exiting=true;for(const w of BrowserWindow.getAllWindows())w.destroy();app.quit();
 }catch(e){await dialog.showMessageBox(main,{type:'error',message:'Le simulateur reste ouvert',detail:e.message})}finally{closing=false}
}
async function freePort(){await new Promise((resolve,reject)=>{const probe=net.createServer();probe.once('error',()=>reject(Error('Le port 8765 est déjà utilisé. Ferme la version navigateur avant de lancer le prototype bureau.')));probe.listen(8765,'127.0.0.1',()=>probe.close(resolve))})}
function ready(){return new Promise(resolve=>{const req=http.get(ORIGIN,r=>{r.resume();resolve(r.statusCode===200)});req.on('error',()=>resolve(false));req.setTimeout(1000,()=>{req.destroy();resolve(false)})})}
async function start(){
 try{preferences=JSON.parse(fs.readFileSync(preferencesPath(),'utf8'))}catch{}
 await freePort();
 const command=process.env.NETOPS_PYTHON||(process.platform==='win32'?'py':'python3');
 const args=process.platform==='win32'&&!process.env.NETOPS_PYTHON?['-3']:[];
 backend=spawn(command,[...args,'-u',path.join(root,'web','tickets_app.py')],{cwd:root,env:{...process.env,NETOPS_DESKTOP:'1'},windowsHide:true,stdio:['ignore','pipe','pipe']});
 let diagnostic='',failure;backend.stdout.on('data',b=>{diagnostic=(diagnostic+b).slice(-6000);if(diagnosticMode)process.stdout.write(b)});backend.stderr.on('data',b=>{diagnostic=(diagnostic+b).slice(-6000);if(diagnosticMode)process.stderr.write(b)});
 backend.on('error',e=>failure=e.message);
 backend.on('exit',code=>{failure='Le moteur Python est arrêté (code '+code+'). '+diagnostic;if(main&&!exiting){exiting=true;if(code!==0)dialog.showErrorBox('Moteur arrêté',failure);app.quit()}});
 const deadline=Date.now()+30000;while(!await ready()){if(failure)throw Error(failure);if(Date.now()>deadline)throw Error('Le moteur ne répond pas après 30 secondes. '+diagnostic);await new Promise(r=>setTimeout(r,250))}
 main=new BrowserWindow({...bounds(preferences.main,screen.getAllDisplays()),show:false,autoHideMenuBar:true,title:'NetOps Lab',webPreferences:{nodeIntegration:false,contextIsolation:true,sandbox:true}});
 configure(main,'main',true);if(!preferences.main)main.maximize();await main.loadURL(ORIGIN);
}
