const {allowed}=require('./policy.cjs');
function identity(url){if(!allowed(url))return null;const u=new URL(url);if(u.pathname==='/workspace/technician')return 'technician:'+u.hash;if(u.pathname==='/workspace/desktop'&&u.searchParams.get('client_serial'))return 'client:'+u.hash+':'+u.searchParams.get('client_serial');return null}
function command(url){const u=new URL(url),app=u.searchParams.get('app');if(u.pathname!='/workspace/technician')return null;if(app==='messaging')return 'messagingApp('+JSON.stringify(u.searchParams.get('ticket'))+')';if(app==='documentation')return 'documentationApp('+JSON.stringify(u.searchParams.get('article'))+')';const functions={directory:'directory',dns:'dnsConsole',files:'fileAdmin',printing:'printingApp',ftp:'ftpAdmin',workstations:'workstationCards',services:'serviceInspection',corporate:'corporateApp',deployment:'deploymentApp'};return functions[app]?functions[app]+'()':null}
class Workspaces{
 constructor(){this.windows=new Map()}
 track(win,url){const id=identity(url);if(!id)return;this.windows.set(id,win);win.once('closed',()=>{if(this.windows.get(id)===win)this.windows.delete(id)})}
 reuse(url){const id=identity(url),win=id&&this.windows.get(id);if(!win||win.isDestroyed())return false;if(win.isMinimized())win.restore();win.show();win.flashFrame?.(true);win.focus();win.once('focus',()=>win.flashFrame?.(false));win.flashFrame?.(false);const script=command(url);if(script){const run=()=>win.webContents.executeJavaScript(script).catch(()=>{});if(win.webContents.isLoadingMainFrame?.())win.webContents.once('did-finish-load',run);else run()}return true}
}
module.exports={identity,command,Workspaces};
