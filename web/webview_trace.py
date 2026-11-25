"""Diagnostic-only webview boundaries. Never logs code, URLs, or credentials."""
import json
SCRIPT=r'''(function(){if(window.__netopsWebTrace)return;window.__netopsWebTrace=true;
var X=XMLHttpRequest,open=X.prototype.open,send=X.prototype.send;
function emit(stage,info){if(window.__netopsTraceQuiet)return;try{var x=new X();open.call(x,'POST',__TRACE_URL__,true);x.setRequestHeader('Content-Type','text/plain');send.call(x,JSON.stringify({stage:stage,info:info||''}));}catch(e){}}
X.prototype.open=function(method,url){this.__netopsNext=String(url).indexOf('/next')>=0;return open.apply(this,arguments);};
X.prototype.send=function(){if(this.__netopsNext){var x=this;['load','error','timeout','abort'].forEach(function(kind){x.addEventListener(kind,function(){if(kind==='load'&&!(x.responseText||''))return;emit('next_'+kind,kind==='load'?String(x.status)+':'+String((x.responseText||'').length):'');});});}return send.apply(this,arguments);};
try{if(typeof $se==='function'){var original=$se;$se=function(){var target=arguments[0];if(target!=='runCode')return original.apply(this,arguments);emit('runCode_enter');try{var out=original.apply(this,arguments);emit('runCode_return');return out;}catch(e){emit('runCode_throw',String(e).slice(0,240));throw e;}};emit('installed');}else emit('install_missing_se');}catch(e){emit('install_error',String(e).slice(0,240));}
})();'''
def install_script(port,token,repair=False):
 url=f'http://127.0.0.1:{port}/result?t={token}&rid=netops-webview-trace'
 code=SCRIPT
 if repair:
  from webview_poll_fix import POLL_FIX
  code=code.rsplit('})();',1)[0]+POLL_FIX+'})();'
 code=code.replace('__TRACE_URL__',json.dumps(url))
 return 'window.webview.evaluateJavaScriptAsync('+json.dumps(code)+');'
