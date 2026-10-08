"""ICMP IPC direct : aucun enterCommand, aucun changement du mode Simulation.
Méthodes documentées Cisco 8.1 ; essai réel PT 9 encore requis.
"""
import ipaddress
import json

def script(pairs, accelerate=False):
    jobs=[dict(source=str(source),target=str(ipaddress.ip_address(target))) for source,target in pairs]
    return r'''try {
var jobs=JOBS, results=[], pending=jobs.length, processes=[];
function finish(i,value){if(results[i])return;results[i]=value;pending--;if(pending===0)reportResult(JSON.stringify(results));}
function startOne(i){
 var j=jobs[i],dev=ipc.network().getDevice(j.source),icmp=dev.getProcess("Icmp");
 var ports=[];
 for(var k=0;k<dev.getPortCount();k++){
  var port=dev.getPortAt(k),address=null;
  try{address=String(port.getIpAddress()||"");}catch(ignore){}
  if(address&&address!=="0.0.0.0")ports.push(port.getName());
 }
 if(ports.length!==1){finish(i,{status:"inconnu",detail:"Interface source absente ou ambiguë : contrôle ICMP non lancé.",method:"icmp_ipc"});return;}
 var id=icmp.createPingProcess(j.target,2,1000,100,ports[0]),p=icmp.getPingProcess(id);processes.push(p);
 var completed=function(received,delay){
  var sent=Number(p.getSentCount()),total=Number(p.getTotalCount());
  finish(i,{status:sent===total&&total>0?(Number(received)===total?"valide":"non satisfait"):"inconnu",detail:"ICMP IPC : "+received+" / "+total+" réponses",method:"icmp_ipc"});
  try{p.donePing.disconnect(completed);}catch(ignore){}
 };
 p.donePing.connect(completed);p.start();
}
if(!jobs.length)reportResult("[]");
else if(ipc.simulation().isSimulationMode()){
 for(var i=0;i<jobs.length;i++)finish(i,{status:"inconnu",detail:"Mode Simulation actif : contrôle suspendu pour préserver l’exercice.",method:"icmp_ipc"});
}else{
 for(var i=0;i<jobs.length;i++)startOne(i);
 if(ACCELERATE&&pending>0)ipc.appWindow().getRealtimeToolbar().fastForwardTime();
}
}catch(e){for(var k=0;k<processes.length;k++){try{processes[k].cancel();}catch(ignore){}}reportResult(JSON.stringify({error:String(e)}));}
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
