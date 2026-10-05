"""Mutations limitées aux câbles client/technicien ; aucune commande IOS."""
import json


def signature(snapshot,state):
    ignored={state['devices'][r]['serial'] for r in ('client','technician')}
    names={d['name'] for d in snapshot['devices'] if d.get('serial') in ignored}
    reserved={(p['device'],p['port']) for p in state.get('technician_locations',{}).values()}
    out={}
    for d in snapshot['devices']:
        if d.get('serial') in ignored:continue
        for p in d.get('ports',[]):
            if (p.get('peer') or {}).get('device') in names or (d['name'],p['name']) in reserved:continue
            key=str(d.get('serial'))+':'+p['name']
            out[key]={k:p.get(k) for k in ('ip','mask','linked','peer','up','protocol_up')}
    return out

def disconnect_js(device,port,peer):
    v=dict(name=device['name'],serial=device['serial'],port=port,peer=peer)
    return '''try {var v=VALUES,d=ipc.network().getDevice(v.name);if(!d||d.getSerialNumber()!==v.serial)throw new Error("Identité du poste modifiée");var p=d.getPort(v.port);if(!p||typeof p.deleteLink!=="function")throw new Error("API de câble absente");var l=p.getLink();if(!l)throw new Error("Liaison absente");var a=l.getPort1(),b=l.getPort2(),other=a.getOwnerDevice().getName()===v.name?b:a;if(other.getOwnerDevice().getName()!==v.peer.device||other.getName()!==v.peer.port)throw new Error("Liaison modifiée");p.deleteLink();reportResult(JSON.stringify({ok:p.getLink()===null}));}catch(e){reportResult(JSON.stringify({error:String(e)}));}'''.replace('VALUES',json.dumps(v))

def move_js(device,destination,mode='wired'):
    v=dict(name=device['name'],serial=device['serial'],destination=destination,mode=mode)
    return '''try {var v=VALUES,d=ipc.network().getDevice(v.name),dest=ipc.network().getDevice(v.destination.device);if(!d||d.getSerialNumber()!==v.serial||!dest||dest.getSerialNumber()!==v.destination.serial)throw new Error("Identité modifiée");var p=d.getPort("FastEthernet0"),c=d.getPort("RS232"),target=dest.getPort(v.destination.port);var lw=ipc.appWindow().getActiveWorkspace().getLogicalWorkspace();if(!p||typeof p.deleteLink!=="function"||(v.mode!=="none"&&(!target||typeof lw.createLink!=="function")))throw new Error("API de raccordement indisponible");var current=v.mode==="console"?c:p;if(v.mode!=="none"&&target.getLink() && (!current||!current.getLink()||target.getLink()!==current.getLink()))throw new Error("Port réservé occupé");if(v.mode==="wired" && (typeof p.setIpSubnetMask!=="function"||typeof d.setDefaultGateway!=="function"))throw new Error("Configure manuellement IP et passerelle dans Packet Tracer");if(v.mode==="console" && (!c||typeof c.deleteLink!=="function"))throw new Error("Port console indisponible");if(p.getLink())p.deleteLink();if(c&&c.getLink())c.deleteLink();if(v.mode==="wired"){p.setIpSubnetMask(v.destination.ip,v.destination.mask);d.setDefaultGateway(v.destination.gateway);lw.createLink(v.name,"FastEthernet0",v.destination.device,v.destination.port,8100);}else if(v.mode==="console"){lw.createLink(v.name,"RS232",v.destination.device,v.destination.port,8108);}reportResult(JSON.stringify({ok:true}));}catch(e){reportResult(JSON.stringify({error:String(e)}));}'''.replace('VALUES',json.dumps(v))
