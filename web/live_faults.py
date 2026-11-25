"""Mutations IPv4 limitées à un PC statique et rétablissement exact des valeurs."""
import ipaddress,json,random
KINDS=('port_down','ip_wrong','mask_wrong')
def choices(device):
 port=next((p for p in device.get('ports',[]) if p.get('name')=='FastEthernet0'),None)
 out=['port_down']
 if not port or port.get('dhcp_client') is not False or port.get('ip_editable') is not True:return out
 try:
  address=ipaddress.IPv4Address(port['ip']);net=ipaddress.IPv4Network((port['ip'],port['mask']),strict=False)
  if address in net and address not in (net.network_address,net.broadcast_address) and net.prefixlen==24:out+=['ip_wrong','mask_wrong']
 except (ValueError,KeyError):pass
 return out

def plan(device,fault,snapshot,seed,target='192.168.50.10'):
 allowed=choices(device)
 if fault=='random':fault=random.Random(seed).choice(allowed)
 if fault not in allowed:raise ValueError('Panne incompatible : les mutations IPv4 exigent un PC statique et une API lisible/modifiable.')
 if fault=='port_down':return dict(kind=fault)
 p=next(p for p in device['ports'] if p['name']=='FastEthernet0')
 before={'ip':p['ip'],'mask':p['mask']};after=dict(before)
 if fault=='mask_wrong':
  address=ipaddress.ip_address(p['ip'])
  masks=[]
  for prefix in (30,29,28,27,26,25):
   net=ipaddress.ip_network((p['ip'],prefix),strict=False)
   if address not in (net.network_address,net.broadcast_address) and ipaddress.ip_address(target) not in net:masks.append(str(net.netmask))
  if not masks:raise ValueError('Aucun masque de panne compatible avec cette adresse.')
  after['mask']=masks[0]
 else:
  used={p.get('ip') for d in snapshot['devices'] for p in d.get('ports',[])}
  oldnet=ipaddress.ip_network((p['ip'],p['mask']),strict=False)
  addresses=[str(ipaddress.IPv4Address('192.168.250.0')+i) for i in range(20,240)]
  addresses=[a for a in addresses if a not in used and ipaddress.ip_address(a) not in oldnet]
  if not addresses:raise ValueError('Aucune adresse de panne disponible.')
  after['ip']=random.Random(seed).choice(addresses)
 return dict(kind=fault,device=device['name'],serial=device['serial'],port='FastEthernet0',before=before,after=after)

def apply_js(injection,restore=False):
 values=injection['before' if restore else 'after']
 for field in ('ip','mask'):ipaddress.IPv4Address(values[field])
 data={k:injection[k] for k in ('device','serial','port')};data.update(values)
 expected=injection['after' if restore else 'before']
 guard='if(p.getIpAddress()!=='+json.dumps(expected['ip'])+' || p.getSubnetMask()!=='+json.dumps(expected['mask'])+')throw new Error("Configuration modifiée depuis le point de départ ; modification annulée");'
 return '''try {var v=VALUES,d=ipc.network().getDevice(v.device);
 if(!d || d.getSerialNumber()!==v.serial)throw new Error("Identité du PC incorrecte");
 var p=d.getPort(v.port);if(typeof p.setIpSubnetMask!=="function" || typeof p.isDhcpClientOn!=="function" || p.isDhcpClientOn())throw new Error("PC statique requis");
 GUARD
 p.setIpSubnetMask(v.ip,v.mask);reportResult("ok");
 }catch(e){reportResult(JSON.stringify({error:String(e)}));}'''.replace('VALUES',json.dumps(data)).replace('GUARD',guard)

def matches(snapshot,injection,restore=False):
 devices=[d for d in snapshot['devices'] if d.get('serial')==injection['serial'] or d.get('name')==injection['device']]
 if len(devices)!=1:return False
 d=devices[0]
 if d.get('serial')!=injection['serial'] or d.get('name')!=injection['device']:return False
 ports=[p for p in d.get('ports',[]) if p.get('name')==injection['port']]
 p=ports[0] if len(ports)==1 else None
 values=injection['before' if restore else 'after']
 return bool(p and p.get('dhcp_client') is False and all(p.get(k)==v for k,v in values.items()))
