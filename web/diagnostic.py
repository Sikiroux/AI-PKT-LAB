"""Diagnostic local PT. Python 3.10+, bibliotheque standard uniquement."""
import ipaddress
import json
import secrets
import threading
import time
import webbrowser
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from vendor.live_bridge import PTCommandBridge, report_result_js, next_rid

ROOT = Path(__file__).resolve().parent
SNAPSHOT_JS = r"""
try {
 var net=ipc.network(), devices=[], links=[];
 for(var i=0;i<net.getDeviceCount();i++){
  var d=net.getDeviceAt(i), ports=[];
  for(var j=0;j<d.getPortCount();j++){
   var p=d.getPortAt(j);
   function read(n){try{return typeof p[n]==='function'?p[n]():null;}catch(e){return null;}}
   var peer=null;try{var link=p.getLink();if(link){var one=link.getPort1(),two=link.getPort2(),other=one.getOwnerDevice().getName()===d.getName()?two:one;peer={device:other.getOwnerDevice().getName(),port:other.getName()};}}catch(e){}
   ports.push({peer:peer,ssid:read('getSSID')||read('getSsid')||read('getWirelessSSID'),name:p.getName(),up:read('isPortUp'),protocol_up:read('isProtocolUp'),ip:read('getIpAddress'),mask:read('getSubnetMask'),wireless:read('isWirelessPort'),dhcp_client:read('isDhcpClientOn'),ip_editable:typeof p.setIpSubnetMask==='function',linked:!!p.getLink()});
  }
  devices.push({name:d.getName(),model:d.getModel(),serial:d.getSerialNumber(),ports:ports});
 }
 var filename=null;try{filename=String(ipc.appWindow().getActiveFile().getSavedFilename()||"");}catch(e){}
 reportResult(JSON.stringify({devices:devices,link_count:net.getLinkCount(),saved_filename:filename}));
}catch(e){reportResult(JSON.stringify({error:String(e)}));}
"""

def checks(snapshot, baseline, name, mode, network):
    device=next((d for d in snapshot['devices'] if d['name']==name),None)
    out=[]
    def add(label, value, detail=''):
        out.append({'label':label,'status':'inconnu' if value is None else ('valide' if value else 'non satisfait'),'detail':detail})
    add('Equipement present',device is not None, ('Poste détecté : '+name) if device else (name+' introuvable. Vérifie le Display Name dans Packet Tracer. Noms détectés : '+', '.join(d['name'] for d in snapshot['devices'])))
    if not device:return out
    identity=device.get('serial')
    old={d.get('serial') for d in baseline['devices']} if baseline else set()
    add('Nouvel equipement depuis le point de depart', identity not in old if baseline and identity else None,'Comparaison par numero de serie, pas uniquement par nom.')
    ports=device['ports']; active=[p for p in ports if p.get('up') and p.get('ip') not in (None,'','0.0.0.0')]
    if mode=='wifi':
        radios=[p for p in ports if p.get('wireless') is True or p['name'].lower().startswith('wireless')]
        active=[p for p in active if p in radios]
        add('Interface Wi-Fi presente',bool(radios))
        add('Interface Wi-Fi active et adressee',bool(active))
        wired=[p for p in ports if p not in radios and p.get('linked') and p.get('up')]
        add('Aucune liaison filaire active',not wired,'Condition du test : le portable doit communiquer uniquement en Wi-Fi.')
        ssid_known=[p for p in radios if isinstance(p.get('ssid'),str) and p['ssid']]
        wrong=any(p['ssid']!='Agence-Lab' or (p.get('peer') and p['peer'].get('device')!='AP1') for p in ssid_known)
        confirmed=any(p['ssid']=='Agence-Lab' and p.get('peer',{}).get('device')=='AP1' and p.get('protocol_up') is True for p in ssid_known if p.get('peer'))
        add('SSID et point d acces attendus',False if wrong else (True if confirmed else None),'Lecture conditionnelle du SSID et de la liaison à AP1 ; sinon confirmation manuelle nécessaire.')
    else:
        add('Interface filaire active et raccordee',any(p.get('linked') and p.get('up') and not p.get('wireless') for p in ports))
    addressed=[p for p in ports if p.get('ip') not in (None,'','0.0.0.0')]
    if mode=='wifi':addressed=[p for p in addressed if p in radios]
    net=ipaddress.ip_network(network,strict=False)
    def member(p):
        try:address=ipaddress.ip_address(p['ip']);return address in net and address not in (net.network_address,net.broadcast_address)
        except ValueError:return False
    add('Adresse dans le reseau attendu',any(member(p) for p in addressed),str(net))
    return out

class Engine:
    def __init__(self,bridge):self.bridge=bridge;self.lock=threading.Lock();self.baseline=None
    def call(self,code,timeout=15):
        if not self.bridge.is_connected:raise RuntimeError('Pont non connecte. Dans Packet Tracer, ouvrir Extensions > MCP BUILDER et laisser sa fenetre ouverte.')
        rid=next_rid();self.bridge._queue.put_nowait(report_result_js(self.bridge.port,self.bridge.token,rid)+code)
        result=self.bridge.take_result(rid,timeout)
        if result is None:raise RuntimeError('Aucune reponse de Packet Tracer. Fermer une eventuelle boite de dialogue erreur et reessayer.')
        return result
    def snapshot(self):
        data=json.loads(self.call(SNAPSHOT_JS))
        if 'error' in data:raise RuntimeError(data['error'])
        return data
    def ping(self,name,target):
        target=str(ipaddress.ip_address(target));dev=json.dumps(name);cmd=json.dumps('ping '+target)
        arm=f"var cl=ipc.network().getDevice({dev}).getCommandLine();var o=String(cl.getOutput());var m=o.match(/Packets: Sent|Success rate/g);var base=m?m.length:0;cl.enterCommand({cmd});reportResult(String(base));"
        base=int(self.call(arm));deadline=time.monotonic()+25
        poll=f"var cl=ipc.network().getDevice({dev}).getCommandLine();var o=String(cl.getOutput());var m=o.match(/Packets: Sent|Success rate/g);reportResult(JSON.stringify({{done:!!m&&m.length>{base},output:o}}));"
        while time.monotonic()<deadline:
            time.sleep(.7);r=json.loads(self.call(poll,5))
            if r['done']:
                import re
                text=r['output'];pc=list(re.finditer(r'Packets:\s*Sent\s*=\s*(\d+),\s*Received\s*=\s*(\d+)',text));ios=list(re.finditer(r'Success rate is (\d+) percent',text))
                if pc:
                    sent,received=map(int,pc[-1].groups());ok=sent>0 and received==sent
                elif ios:ok=int(ios[-1].group(1))==100
                else:return {'label':'Ping depuis le poste','status':'inconnu','detail':text[-1800:]}
                return {'label':'Ping depuis le poste','status':'valide' if ok else 'non satisfait','detail':text[-1800:]}
        return {'label':'Ping depuis le poste','status':'inconnu','detail':'Delai depasse : aucun nouveau resultat complet. Reessayer apres convergence.'}

def run():
    bridge=PTCommandBridge();bridge.start();engine=Engine(bridge);ui_token=secrets.token_urlsafe(32)
    class Handler(BaseHTTPRequestHandler):
        def send(self,code,data,ctype='application/json'):
            body=data.encode() if isinstance(data,str) else json.dumps(data,ensure_ascii=False).encode();self.send_response(code);self.send_header('Content-Type',ctype+'; charset=utf-8');self.send_header('Content-Length',str(len(body)));self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(body)
        def do_GET(self):
            if self.headers.get('Host') not in ('127.0.0.1:8765','localhost:8765'):return self.send(403,{'error':'Host refuse'})
            if self.path=='/':return self.send(200,(ROOT/'interface.html').read_text(encoding='utf-8').replace('__UI_TOKEN__',ui_token),'text/html')
            if self.path=='/status':return self.send(200,{'connected':bridge.is_connected,'baseline':bool(engine.baseline)})
            self.send(404,{'error':'Page inconnue'})
        def do_POST(self):
            if self.headers.get('Host') not in ('127.0.0.1:8765','localhost:8765') or not secrets.compare_digest(self.headers.get('X-Diagnostic-Token',''),ui_token):return self.send(403,{'error':'Acces refuse'})
            try:
                n=int(self.headers.get('Content-Length','0'))
                if n<0 or n>8192:raise ValueError('Requete trop grande')
                data=json.loads(self.rfile.read(n) or b'{}')
                with engine.lock:
                    if self.path in ('/inspect','/baseline'):
                        snapshot=engine.snapshot()
                        if self.path=='/baseline':
                            engine.baseline=snapshot;(ROOT/'etat-depart.json').write_text(json.dumps(snapshot,indent=2),encoding='utf-8')
                        return self.send(200,snapshot)
                    if self.path=='/verify':
                        snapshot=engine.snapshot();result=checks(snapshot,engine.baseline,data['name'],data['mode'],data['network'])
                        if any(c['label']=='Equipement present' and c['status']=='valide' for c in result):result.append(engine.ping(data['name'],data['target']))
                        return self.send(200,{'checks':result,'complete':all(c['status']=='valide' for c in result),'snapshot':snapshot})
                    self.send(404,{'error':'Action inconnue'})
            except Exception as e:self.send(400,{'error':str(e)})
        def log_message(self,*args):pass
    server=ThreadingHTTPServer(('127.0.0.1',8765),Handler)
    print('Diagnostic : http://127.0.0.1:8765\nPont : port 54321. Ouvrir Extensions > MCP BUILDER dans Packet Tracer.\nLaisser cette console ouverte. Ctrl+C pour arreter.')
    webbrowser.open('http://127.0.0.1:8765')
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close();bridge.stop()
if __name__=='__main__':
    try:run()
    except OSError as e:print('Impossible de demarrer :',e,'\nFermer les autres ponts utilisant 54321 ou 8765.');raise SystemExit(1)
