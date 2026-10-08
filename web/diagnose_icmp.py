"""Diagnostic de compatibilité ICMP en lecture seule, via le pont déjà lancé."""
import json
import uuid
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from vendor.bridge_token import get_bridge_token
from vendor.live_bridge import DEFAULT_PORT, report_result_js

SCRIPT = r'''(function(report){
var result={diagnostic:"icmp-process-compatibility-v1",devices:[]};
try{
 var net=ipc.network();
 for(var i=0;i<net.getDeviceCount();i++){
  var dev=net.getDeviceAt(i), row={name:String(dev.getName()),model:String(dev.getModel()),attempts:[]};
  // Aucun ping créé ou lancé : seule la récupération des objets est testée.
  for(var k=0;k<2;k++){
   var name=k===0?"Icmp":"IcmpProcess",attempt={process:name};
   try{
    var p=dev.getProcess(name);
    attempt.present=!!p;
    attempt.create_ping_available=!!p&&typeof p.createPingProcess==="function";
    attempt.get_ping_available=!!p&&typeof p.getPingProcess==="function";
   }catch(e){attempt.error=String(e);}
   row.attempts.push(attempt);
  }
  result.devices.push(row);
 }
}catch(e){result.error=String(e);}
report(JSON.stringify(result));
})(reportResult);'''


def collect(port=DEFAULT_PORT):
    token = get_bridge_token()
    rid = 'icmp-diagnostic-' + uuid.uuid4().hex
    base = f'http://127.0.0.1:{port}'
    code = report_result_js(port, token, rid) + SCRIPT
    request = Request(base + '/queue?' + urlencode({'t': token}),
                      data=code.encode('utf-8'), headers={'Content-Type': 'text/plain'})
    with urlopen(request, timeout=5) as response:
        if response.status != 200:
            raise RuntimeError('Le pont a refusé le diagnostic.')
    with urlopen(base + '/result?' + urlencode({'t': token, 'rid': rid, 'wait': 15}), timeout=20) as response:
        if response.status == 204:
            raise RuntimeError('Packet Tracer ne répond pas. Vérifie que MCP BUILDER est ouvert.')
        result = json.loads(response.read().decode('utf-8'))
    if not isinstance(result, dict) or result.get('diagnostic') != 'icmp-process-compatibility-v1':
        raise RuntimeError('Réponse de diagnostic inattendue.')
    return result


def main():
    print('Garde le logiciel web, Packet Tracer et MCP BUILDER ouverts.')
    print('Diagnostic en lecture seule : aucun ping, aucune modification réseau.\n')
    try:
        result = collect()
        destination = Path(__file__).resolve().parent / 'diagnostic-icmp.json'
        destination.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
        print(json.dumps(result, ensure_ascii=False, indent=2))
        print('\nRapport enregistré :', destination)
    except HTTPError as error:
        print('Échec HTTP', error.code, ': pont indisponible ou authentification refusée.')
        return 1
    except (URLError, OSError, ValueError, RuntimeError) as error:
        print('Diagnostic impossible :', error)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
