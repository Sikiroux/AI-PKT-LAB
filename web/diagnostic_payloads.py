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

# Phase 3 diagnostics only: fresh PT process per probe, unchanged topology.
# All native references, including network, links, endpoints and owners, are
# retained once. This is NOT a production cache invalidation strategy.
_PHASE3_BUILD=r'''var G=(function(){return this;})();var c=G.__pktlabPhase3;var objects=0,state='reused';
if(!c){var net=ipc.network();objects++;c={net:net,devices:[],device_count:net.getDeviceCount(),link_count:net.getLinkCount(),port_count:0};
for(var i=0;i<c.device_count;i++){var d=net.getDeviceAt(i);objects++;var row={device:d,ports:[]};var n=d.getPortCount();
for(var j=0;j<n;j++){var p=d.getPortAt(j);objects++;var link=p.getLink(),peer=null;if(link){objects++;var one=link.getPort1(),two=link.getPort2();objects+=2;var owner1=one.getOwnerDevice(),owner2=two.getOwnerDevice();objects+=2;peer=owner1.getName()===d.getName()?{port:two,owner:owner2}:{port:one,owner:owner1};}
row.ports.push({port:p,link:link,peer:peer});c.port_count++;}c.devices.push(row);}G.__pktlabPhase3=c;state='built';}'''

def _phase3(body):
 return '(function(){try{'+_PHASE3_BUILD+body+'}catch(e){reportResult(JSON.stringify({error:String(e)}));}})();'

INVENTORY_PROBES.update({
 'inventory_cached_all':_phase3(_READ_PORT+r'''
if(c.net.getDeviceCount()!==c.device_count||c.net.getLinkCount()!==c.link_count)throw Error('Topologie modifiée pendant le test ; redémarrer cet essai.');
var devices=[];for(var i=0;i<c.devices.length;i++){var row=c.devices[i],ports=[];for(var j=0;j<row.ports.length;j++){var saved=row.ports[j],out=readPort(saved.port);out.linked=!!saved.link;out.peer=saved.peer?{device:saved.peer.owner.getName(),port:saved.peer.port.getName()}:null;ports.push(out);}devices.push({name:row.device.getName(),model:row.device.getModel(),serial:row.device.getSerialNumber(),ports:ports});}
reportResult(JSON.stringify({devices:devices,link_count:c.link_count,objects:objects,cache:state,cached_devices:c.device_count,cached_ports:c.port_count}));'''),
 'inventory_cached_hold':_phase3(r'''reportResult(JSON.stringify({devices:[],objects:objects,cache:state,cached_devices:c.device_count,cached_ports:c.port_count}));'''),
})

# Short, ordered commands locate the first failed boundary under aggressive GC.
_TRACE_PREFIX="(function(){try{var c=(function(){return this;})().__pktlabPhase3;if(!c)throw Error('Cache absent');"
def _trace(body):
 return _TRACE_PREFIX+body+"}catch(e){reportResult(JSON.stringify({error:String(e)}));}})();"
GC_TRACE_STEPS=[
 ('initial_inventory',INVENTORY_PROBES['inventory_cached_all']),
 ('transport_ack','reportResult(JSON.stringify({devices:[],stage:"transport_ack"}));'),
 ('cache_metadata',_trace('reportResult(JSON.stringify({devices:[],cached_devices:c.device_count,cached_ports:c.port_count}));')),
 ('network_counts',_trace('reportResult(JSON.stringify({devices:[],device_count:c.net.getDeviceCount(),link_count:c.net.getLinkCount()}));')),
 ('device_names',_trace('var names=[];for(var i=0;i<c.devices.length;i++)names.push(c.devices[i].device.getName());reportResult(JSON.stringify({devices:[],names:names}));')),
 ('first_port',_trace(_READ_PORT+'var p=c.devices[0]&&c.devices[0].ports[0];reportResult(JSON.stringify({devices:[],port:p?readPort(p.port):null}));')),
 ('read_values',_trace(_READ_PORT+'var values=[];for(var i=0;i<c.devices.length;i++){var ports=[];for(var j=0;j<c.devices[i].ports.length;j++)ports.push(readPort(c.devices[i].ports[j].port));values.push({ports:ports});}c.traceValues=values;reportResult(JSON.stringify({devices:[],rows:values.length}));')),
 ('serialize_values',_trace('reportResult(JSON.stringify({devices:c.traceValues||[]}));')),
]
INVENTORY_PROBES['inventory_gc_trace']=GC_TRACE_STEPS[0][1]

GC_TRANSPORT_STEPS=[('ack_before_inventory',GC_TRACE_STEPS[1][1]),GC_TRACE_STEPS[0],('ack_after_inventory',GC_TRACE_STEPS[1][1])]
INVENTORY_PROBES['inventory_gc_transport']=GC_TRANSPORT_STEPS[0][1]

# Matched batches: same loop count and small response, no topology writes.
TRIAGE_BATCH=100
for _name,_setup,_call in (
 ('triage_control','var value=0;','value=k;'),
 ('triage_scalar','var net=ipc.network(),value=0;','value=net.getDeviceCount();'),
 ('triage_object','var net=ipc.network(),value=null;if(net.getDeviceCount()<1)throw Error("Reseau vide");','value=net.getDeviceAt(0);'),
 ('triage_cached_property','var G=(function(){return this;})();if(!G.__triageDevice){var net=ipc.network();if(net.getDeviceCount()<1)throw Error("Reseau vide");G.__triageDevice=net.getDeviceAt(0);}var value=null;','value=G.__triageDevice.getName();'),
):
 INVENTORY_PROBES[_name]='(function(){try{'+_setup+'for(var k=0;k<100;k++){'+_call+'}reportResult(JSON.stringify({devices:[],batch_operations:100,probe:"'+_name+'"}));}catch(e){reportResult(JSON.stringify({error:String(e)}));}})();'
