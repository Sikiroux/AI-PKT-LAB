"""Experimental single-request polling, injected only in the owned test instance."""
POLL_FIX=r'''
if(!window.__netopsPollFix){
 if(typeof pollCommands!=='function'||typeof bridgeUrl!=='function'||typeof S==='undefined')emit('poll_fix_unsupported');
 else{
  window.__netopsPollFix=true;var busy=false,timer=null;
  function schedule(ms){if(timer!==null)return;timer=setTimeout(function(){timer=null;pollCommands();},ms);}
  pollCommands=function(){
   if(busy)return;
   if(!S.bridgeUp){schedule(500);return;}
   busy=true;var x=new XMLHttpRequest(),settled=false;
   function finish(ms){busy=false;schedule(ms);}
   function fail(){if(settled)return;settled=true;emit('poll_retry');finish(500);}
   try{
    var url=bridgeUrl('/next');url+=(url.indexOf('?')>=0?'&':'?')+'netops_poll=1';
    x.open('GET',url,true);x.timeout=0;
    x.onload=function(){
     if(settled)return;settled=true;x.timeout=0;
     var status=x.status,batch=x.responseText||'';
     if(status===401){if(typeof handleUnauthorized==='function')handleUnauthorized();finish(1000);return;}
     if(status!==200||!batch){finish(status===200?0:500);return;}
     // Leave the XMLHttpRequest event before entering native script execution.
     setTimeout(function(){
      try{$se('runCode',batch);if(typeof S.commandCount==='number')S.commandCount+=batch.split('\n').length;if(typeof updateCommandCount==='function')updateCommandCount();}
      catch(e){emit('poll_execution_error');}
      finally{finish(0);}
     },0);
    };
    x.onerror=x.ontimeout=x.onabort=fail;x.send();
   }catch(e){fail();}
  };
  emit('poll_fix_installed');
  // The old loop's next scheduled call enters this replacement. Do not create
  // another chain while the request which installed us is still finishing.
 }
}
'''
