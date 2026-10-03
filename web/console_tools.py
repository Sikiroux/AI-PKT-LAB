"""Diagnostic et nettoyage du tampon SW1 sans commande IOS non prise en charge.
L'API expose la lecture des historiques, mais aucun effacement n'est presume.
"""
CLEAN_JS = r'''try {
 var c=ipc.network().getDevice("SW1").getCommandLine();
 var r={display:false,history:false,reason:"",method:"flush + lecture des historiques",counts:{user:null,config:null}};
 function count(getter){
  if(typeof c[getter]!=="function")return null;
  var h=c[getter](),items=h && h.history;
  if(!items || typeof items.length!=="number")return null;
  var n=0;for(var i=0;i<items.length;i++)if(String(items[i]).replace(/^\s+|\s+$/g,""))n++;
  return n;
 }
 r.counts.user=count("getUserHistory");r.counts.config=count("getConfigHistory");
 r.history=r.counts.user===0 && r.counts.config===0;
 if(typeof c.flush==="function"){
  var output=String(c.getOutput());c.flush(output.split("\n").length);
  var left=String(c.getOutput()).replace(/^\s+|\s+$/g,"");
  r.display=left==="" || /^[\w.-]+[>#]$/.test(left);
 }
 if(r.counts.user===null || r.counts.config===null)r.reason="Historique illisible via le pont : masquage non confirme.";
 else if(!r.history)r.reason="Historique encore present. Aucun effacement fiable disponible dans cette version.";
 else if(!r.display)r.reason="Tampon de console non vide apres nettoyage.";
 reportResult(JSON.stringify(r));
}catch(e){reportResult(JSON.stringify({display:false,history:false,reason:"Diagnostic de console impossible : "+String(e),method:"flush + lecture des historiques"}));}'''

def cleaned(report):return report.get('display') is True and report.get('history') is True
