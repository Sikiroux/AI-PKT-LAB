"""ICMP IPC direct : aucun enterCommand, aucun changement du mode Simulation.
Méthodes documentées Cisco 8.1 ; essai réel PT 9 encore requis.
"""
import ipaddress
import json

def script(pairs, accelerate=False):
    jobs=[dict(source=str(source),target=str(ipaddress.ip_address(target))) for source,target in pairs]
    return r'''(function(report){
var jobs=JOBS, results=[], pending=jobs.length, stage="mode Simulation", active=0;
function finish(i,value){if(results[i])return;results[i]=value;pending--;if(pending===0)report(JSON.stringify(results));}
function fail(i,step,e){finish(i,{status:"inconnu",detail:"Contrôle discret : "+step+" : "+String(e),method:"icmp_ipc"});}
function startOne(i){
 var p=null,step="appareil source";
 try{
 var j=jobs[i],dev=ipc.network().getDevice(j.source);
 step="processus Icmp";var icmp=dev.getProcess("Icmp");
 step="interface source";var ports=[];
 for(var k=0;k<dev.getPortCount();k++){
  var port=dev.getPortAt(k),address=null;
  try{address=String(port.getIpAddress()||"");}catch(ignore){}
  if(address&&address!=="0.0.0.0")ports.push(port.getName());
 }
 if(ports.length!==1){fail(i,step,"Interface source absente ou ambiguë");return;}
 step="createPingProcess";var id=icmp.createPingProcess(j.target,2,1000,100,ports[0]);
 step="getPingProcess";p=icmp.getPingProcess(id);
 var completed=function(src,args){
  if(results[i])return;
  try{
   var sent=Number(p.getSentCount()),total=Number(p.getTotalCount()),received=Number(p.getReceivedCount());
   var valid=isFinite(sent)&&isFinite(total)&&isFinite(received)&&sent===total&&total>0&&received>=0&&received<=sent;
   finish(i,{status:valid?(received===total?"valide":"non satisfait"):"inconnu",detail:"ICMP IPC : "+received+" / "+total+" réponses",method:"icmp_ipc"});
  }catch(e){fail(i,"résultat donePing",e);}
  try{p.unregisterEvent("donePing",null,completed);}catch(ignore){}
 };
 step="registerEvent donePing";p.registerEvent("donePing",null,completed);
 step="start ping";p.start();active++;
 }catch(e){fail(i,step,e);if(p){try{p.cancel();}catch(ignore){}}}
}
try{
 if(!jobs.length)report("[]");
 else if(ipc.simulation().isSimulationMode()){
  for(var i=0;i<jobs.length;i++)fail(i,stage,"Mode Simulation actif : contrôle suspendu pour préserver l’exercice.");
 }else{
  for(var i=0;i<jobs.length;i++)startOne(i);
  stage="fastForwardTime";
  if(ACCELERATE&&pending>0&&active>0){
   try{ipc.appWindow().getRealtimeToolbar().fastForwardTime();}catch(ignore){}
  }
 }
}catch(e){for(var i=0;i<jobs.length;i++)if(!results[i])fail(i,stage,e);}
})(reportResult);
'''.replace('JOBS',json.dumps(jobs)).replace('ACCELERATE','true' if accelerate else 'false')

def run(engine,pairs,accelerate=False):
    pairs=list(pairs)
    try:
        rows=json.loads(engine.call(script(pairs,accelerate),timeout=12))
        if not isinstance(rows,list) or len(rows)!=len(pairs):raise RuntimeError(rows.get('error','Réponse ICMP invalide') if isinstance(rows,dict) else 'Réponse ICMP invalide')
        if any(r.get('status') not in ('valide','non satisfait','inconnu') for r in rows):raise RuntimeError('Statut ICMP invalide')
        return rows
    except Exception as e:
        return [dict(status='inconnu',detail='Contrôle discret indisponible ou délai dépassé : '+str(e),method='icmp_ipc') for _ in pairs]
