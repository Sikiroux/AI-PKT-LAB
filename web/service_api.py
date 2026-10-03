"""Adaptateurs conditionnels : aucune API de service n’est présumée disponible."""
import json
SERVICES={
 'http':dict(title='Intranet indisponible',test='Ouvrir la page HTTP depuis PC-ADMIN et un second poste.',processes=['HTTPServer','HttpServer','HTTP Server']),
 'dns':dict(title='Les noms des services ne fonctionnent plus',test='Résoudre le nom attendu depuis un client, puis ouvrir le service par son nom.',processes=['DNSServer','DnsServer','DNS Server']),
 'dhcp':dict(title='Les nouveaux postes ne reçoivent plus de bail',test='Renouveler le bail d’un poste test ; relever IP, masque, passerelle et DNS, puis tester ses accès.',processes=['DHCPServer','DhcpServer','DHCP Server']),
}
def probe(engine,name,serial,service):
 if service not in SERVICES:raise ValueError('Service inconnu.')
 data=dict(device=name,serial=serial,processes=SERVICES[service]['processes'])
 code='''try {var v=VALUES,d=ipc.network().getDevice(v.device),result={supported:false};
 if(!d||d.getSerialNumber()!==v.serial)throw new Error("Identité incorrecte");
 var readers=["isEnabled","getEnabled","isOn"],writers=["setEnabled","setOn"];
 for(var i=0;i<v.processes.length&&!result.supported;i++){var p=null;try{p=d.getProcess(v.processes[i]);}catch(e){}if(!p)continue;
 for(var r=0;r<readers.length&&!result.supported;r++){if(typeof p[readers[r]]!=="function")continue;var state;try{state=p[readers[r]]();}catch(e){continue;}
 if(typeof state!=="boolean")continue;
 for(var w=0;w<writers.length;w++){if(typeof p[writers[w]]==="function"){result={supported:true,enabled:state,process:v.processes[i],reader:readers[r],writer:writers[w]};break;}}}}
 reportResult(JSON.stringify(result));}catch(e){reportResult(JSON.stringify({supported:false,error:String(e)}));}'''.replace('VALUES',json.dumps(data))
 try:result=json.loads(engine.call(code))
 except Exception:return dict(supported=False)
 if not isinstance(result,dict) or result.get('supported') is not True or type(result.get('enabled')) is not bool:return dict(supported=False)
 if result.get('process') not in data['processes'] or result.get('reader') not in ('isEnabled','getEnabled','isOn') or result.get('writer') not in ('setEnabled','setOn'):raise ValueError('Adaptateur de service invalide.')
 return dict(result,device=name,serial=serial,service=service)

def write(engine,adapter,enabled):
 if type(enabled) is not bool:raise ValueError('État booléen requis.')
 # Validate persisted adapter identities before constructing any JavaScript.
 service=adapter['service']
 if service not in SERVICES or adapter['process'] not in SERVICES[service]['processes'] or adapter['reader'] not in ('isEnabled','getEnabled','isOn') or adapter['writer'] not in ('setEnabled','setOn'):raise ValueError('Adaptateur invalide.')
 data=dict(adapter,expected=enabled)
 code='''try {var v=VALUES,d=ipc.network().getDevice(v.device);if(!d||d.getSerialNumber()!==v.serial)throw new Error("Identité incorrecte");
 var p=d.getProcess(v.process);if(!p||typeof p[v.reader]!=="function"||typeof p[v.writer]!=="function")throw new Error("API indisponible");
 var before=p[v.reader]();if(typeof before!=="boolean")throw new Error("État illisible");p[v.writer](v.expected);
 reportResult(JSON.stringify({enabled:p[v.reader]()}));}catch(e){reportResult(JSON.stringify({error:String(e)}));}'''.replace('VALUES',json.dumps(data))
 result=json.loads(engine.call(code))
 if type(result.get('enabled')) is not bool or result['enabled'] is not enabled:raise RuntimeError('Modification du service non confirmée.')
 return result
