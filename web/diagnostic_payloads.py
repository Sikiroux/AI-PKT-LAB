"""Fixed control scripts and optional v5 webview log cleanup, no network writes."""
import json

OK_SCRIPT='reportResult("OK");'
PAYLOAD_SIZE=42072
PAYLOAD_SCRIPT='(function(){var s=new Array(42073).join("x");reportResult(s);})();'
# Runs only in the extension webview. Preserves errors, script history, counters,
# editor contents and in-flight bridge traffic. ACK returns through known runCode.
CLEANUP_WEBVIEW=r'''(function(){var result;try{if(typeof S==='undefined'||!S.logs||typeof renderLog!=='function'){result={supported:false,error:'Nettoyage non compatible avec cette extension.'};}else{var before=S.logs.length;var panel=document.getElementById('logPanel');var lines=panel?panel.querySelectorAll('.log-line').length:0;S.logs=S.logs.filter(function(e){return e.type==='err';});renderLog();result={supported:true,removed:before-S.logs.length,errors_kept:S.logs.length,displayed_before:lines};}}catch(e){result={supported:false,error:String(e)};}try{$se('runCode','reportResult('+JSON.stringify(JSON.stringify(result))+');');}catch(e){}})();'''
CLEANUP_SCRIPT='window.webview.evaluateJavaScriptAsync('+json.dumps(CLEANUP_WEBVIEW)+');'

# Independent inventory probes: no implicit full snapshot or network writes.
def _probe(body):
 return "try{var net=ipc.network();"+body+"}catch(e){reportResult(JSON.stringify({error:String(e)}));}"

INVENTORY_PROBES={
 'inventory_count':_probe("reportResult(JSON.stringify({device_count:net.getDeviceCount()}));"),
 'inventory_identity':_probe("var devices=[];var count=net.getDeviceCount();for(var i=0;i<count;i++){var d=net.getDeviceAt(i);devices.push({name:d.getName(),model:d.getModel(),serial:d.getSerialNumber()});}reportResult(JSON.stringify({devices:devices}));"),
 'inventory_ports':_probe("var devices=[];var count=net.getDeviceCount();for(var i=0;i<count;i++){var d=net.getDeviceAt(i),ports=[];var pc=d.getPortCount();for(var j=0;j<pc;j++){var p=d.getPortAt(j);function read(n){try{return typeof p[n]==='function'?p[n]():null;}catch(e){return null;}}ports.push({name:p.getName(),ssid:read('getSSID')||read('getSsid')||read('getWirelessSSID'),up:read('isPortUp'),protocol_up:read('isProtocolUp'),ip:read('getIpAddress'),mask:read('getSubnetMask'),wireless:read('isWirelessPort'),dhcp_client:read('isDhcpClientOn'),ip_editable:typeof p.setIpSubnetMask==='function'});}devices.push({ports:ports});}reportResult(JSON.stringify({devices:devices}));"),
 'inventory_links':_probe("var devices=[];var count=net.getDeviceCount();for(var i=0;i<count;i++){var d=net.getDeviceAt(i),ports=[];var pc=d.getPortCount();for(var j=0;j<pc;j++){var p=d.getPortAt(j),peer=null;try{var link=p.getLink();if(link){var one=link.getPort1(),two=link.getPort2(),other=one.getOwnerDevice().getName()===d.getName()?two:one;peer={device:other.getOwnerDevice().getName(),port:other.getName()};}}catch(e){}ports.push({peer:peer,linked:!!p.getLink()});}devices.push({ports:ports});}reportResult(JSON.stringify({devices:devices,link_count:net.getLinkCount()}));")
}

# Phase 2: does each retrieval of a PT object leave memory behind, and does
# reusing the same wrappers between calls keep memory flat? Each probe reports
# how many objects it retrieved from the API ("objects") so growth per object
# can be computed from the journal. The cache lives on the Script Engine's
# global object and is rebuilt only when the device or link count changes.
_GLOBAL="var G=(function(){return this;})();"
_READ_PORT=("function readPort(p){function read(n){try{return typeof p[n]==='function'?p[n]():null;}catch(e){return null;}}"
 "return {name:p.getName(),ssid:read('getSSID')||read('getSsid')||read('getWirelessSSID'),up:read('isPortUp'),protocol_up:read('isProtocolUp'),"
 "ip:read('getIpAddress'),mask:read('getSubnetMask'),wireless:read('isWirelessPort'),dhcp_client:read('isDhcpClientOn'),ip_editable:typeof p.setIpSubnetMask==='function'};}")
_CACHE=(_GLOBAL+"var objects=0;var sig=net.getDeviceCount()+':'+net.getLinkCount();var cache=G.__pktlabCache;var state='reused';"
 "if(!cache||cache.sig!==sig){cache={sig:sig,devices:[]};var count=net.getDeviceCount();for(var i=0;i<count;i++){var d=net.getDeviceAt(i),ports=[];objects++;"
 "var pc=d.getPortCount();for(var j=0;j<pc;j++){ports.push(d.getPortAt(j));objects++;}cache.devices.push(ports);}G.__pktlabCache=cache;state='built';}")
REPEAT_OBJECTS=244  # same number of objects per cycle as inventory_ports on the test network
INVENTORY_PROBES.update({
 'inventory_repeat_same':_probe("var n=0;if(net.getDeviceCount()>0){for(var k=0;k<"+str(REPEAT_OBJECTS)+";k++){net.getDeviceAt(0);n++;}}reportResult(JSON.stringify({devices:[],objects:n}));"),
 'inventory_cached_ports':_probe(_READ_PORT+_CACHE+"var devices=[];for(var a=0;a<cache.devices.length;a++){var out=[];for(var b=0;b<cache.devices[a].length;b++)out.push(readPort(cache.devices[a][b]));devices.push({ports:out});}reportResult(JSON.stringify({devices:devices,objects:objects,cache:state}));"),
 'inventory_cached_link_flag':_probe(_CACHE+"var devices=[];for(var a=0;a<cache.devices.length;a++){var out=[];for(var b=0;b<cache.devices[a].length;b++){var link=null;try{link=cache.devices[a][b].getLink();}catch(e){}if(link)objects++;out.push({linked:!!link});}devices.push({ports:out});}reportResult(JSON.stringify({devices:devices,objects:objects,cache:state}));"),
 'inventory_ports_gc':_probe(_GLOBAL+_READ_PORT+"var objects=0,devices=[];var count=net.getDeviceCount();for(var i=0;i<count;i++){var d=net.getDeviceAt(i),ports=[];objects++;var pc=d.getPortCount();for(var j=0;j<pc;j++){ports.push(readPort(d.getPortAt(j)));objects++;}devices.push({ports:ports});}"
  "var gcName=typeof G.gc==='function'?'gc':(typeof G.collectGarbage==='function'?'collectGarbage':(typeof G.CollectGarbage==='function'?'CollectGarbage':null));var gcError=null;if(gcName){try{G[gcName]();}catch(e){gcError=String(e);}}"
  "reportResult(JSON.stringify({devices:devices,objects:objects,gc:gcName,gc_error:gcError}));"),
})
