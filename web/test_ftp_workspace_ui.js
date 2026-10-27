const fs=require('fs'),vm=require('vm');
const fixtureSource=fs.readFileSync(__dirname+'/test_desktop_ui.js','utf8').split('(async()=>{')[0];
const scenario=String.raw`
(async()=>{
 vm.runInContext('ftpClient()',ctx);await tick();const ftp=contents.at(-1);
 const filter=label=>find(ftp,e=>e.attributes['aria-label']===label),localFilter=filter('Rechercher un fichier local'),remoteFilter=filter('Rechercher un fichier distant');
 assert(localFilter&&remoteFilter);assert.equal(localFilter.type,'search');const beforeFilter=requests.length;
 localFilter.value='absent';localFilter.oninput();assert(!byButton(ftp,'Local.txt'));assert(find(ftp,e=>e.textContent==='0 / 1 fichier(s)'));assert.equal(requests.length,beforeFilter,'Filtering is local and never probes or transfers');
 localFilter.value='';localFilter.oninput();assert(byButton(ftp,'Local.txt'));
 await byButton(ftp,'Connexion…').onclick();const connection=contents.at(-1);const password=find(connection,e=>e.attributes['aria-label']==='Mot de passe');password.value='Formation!2026';await byButton(connection,'Se connecter').onclick();assert.equal(password.value,'');
 const state=find(ftp,e=>e.className==='app-address ftp-status');assert.equal(state.dataset.state,'connected');assert(state.textContent.includes('Session FTP ouverte'));
 await byButton(ftp,'Remote.txt').onclick();assert(!byButton(ftp,'Télécharger vers le poste').disabled);
 const beforeSearch=requests.length;remoteFilter.value='Local';remoteFilter.oninput();assert(!byButton(ftp,'Remote.txt'));assert(byButton(ftp,'Télécharger vers le poste').disabled,'A hidden selected file cannot still be downloaded');assert.equal(requests.length,beforeSearch);
 remoteFilter.value='';remoteFilter.oninput();assert(byButton(ftp,'Télécharger vers le poste').disabled,'Clearing search does not restore a hidden selection');
 const selected=byButton(ftp,'Remote.txt');await selected.onclick();assert.equal(byButton(ftp,'Remote.txt'),selected,'Selection keeps the existing DOM row');assert(find(ftp,e=>e.className==='ftp-selection-info'&&e.textContent.includes('Remote.txt')));
 const transferPanel=find(ftp,e=>e.className==='ftp-transfer-panel');assert(!transferPanel.open);await byButton(ftp,'Télécharger vers le poste').onclick();assert(transferPanel.open);assert(find(transferPanel,e=>e.textContent==='Terminé'));
 const logins=requests.filter(([url])=>url.endsWith('ftp/login')).length;
 ftpFailure=true;ftpRefusal='NETWORK_UNKNOWN';await byButton(ftp,'Télécharger vers le poste').onclick();assert.equal(state.dataset.state,'unknown');assert(state.textContent.includes('Réseau non vérifié'));assert(state.textContent.includes('Session FTP ouverte'),'Unknown transport must not silently log out');
 ftpRefusal='FTP_SERVICE_STOPPED';await byButton(ftp,'Télécharger vers le poste').onclick();assert.equal(state.dataset.state,'failed');assert(state.textContent.includes('Service FTP indisponible'));
 assert.equal(requests.filter(([url])=>url.endsWith('ftp/login')).length,logins,'The UI must not reconnect automatically');
 ftpFailure=false;await byButton(ftp,'Actualiser les fichiers').onclick();assert.equal(state.dataset.state,'connected');
 ftpFailure=true;ftpRefusal='FTP_NOT_AUTHENTICATED';await byButton(ftp,'Actualiser les fichiers').onclick();assert.equal(state.dataset.state,'disconnected');assert(!byButton(ftp,'Remote.txt'));assert(byButton(ftp,'Télécharger vers le poste').disabled);
 console.log('FTP workspace: local searches, hidden-selection safety, transfer panel, session/transport distinction, explicit recovery and password clearing OK');
})().catch(e=>{console.error(e);process.exitCode=1});
`;
vm.runInNewContext(fixtureSource+scenario,{require,__dirname,process,console,setImmediate,URLSearchParams},{filename:__filename});
