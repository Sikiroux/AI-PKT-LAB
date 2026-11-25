"""One bounded sequence, fresh owned PT process and copied project per trial."""
import copy
import json
import os
from pathlib import Path
import shutil
import subprocess
import threading
import time
from diagnostic_payloads import INVENTORY_PROBES
from process_memory import read_packet_tracer_memory

MODES=('inventory_cached_all',)
FILE_SCRIPT='try{reportResult(JSON.stringify({file:String(ipc.appWindow().getActiveFile().getSavedFilename()||""),devices:ipc.network().getDeviceCount()}));}catch(e){reportResult(JSON.stringify({error:String(e)}));}'

def executable():
 explicit=os.environ.get('NETOPS_PACKET_TRACER_EXE')
 if explicit and Path(explicit).is_file():return Path(explicit)
 found=[]
 for var in ('ProgramFiles','ProgramFiles(x86)'):
  root=os.environ.get(var)
  if root:
   for pattern in ('Cisco Packet Tracer*/bin/PacketTracer.exe','Cisco Packet Tracer*/PacketTracer.exe'):
    found.extend(Path(root).glob(pattern))
 if not found:raise ValueError('PacketTracer.exe introuvable. Définis NETOPS_PACKET_TRACER_EXE avec son chemin.')
 return max(found,key=lambda p:p.stat().st_mtime)

def packet_tracer_environment(native_profile):
 result=os.environ.copy()
 if native_profile or os.environ.get('NETOPS_TRIAGE_PROFILE')=='1':result.pop('QV4_MM_AGGRESSIVE_GC',None)
 else:result['QV4_MM_AGGRESSIVE_GC']='1'
 return result

class MemorySuite:
 def __init__(self,diagnostic,folder):
  self.diag=diagnostic;self.folder=Path(folder);self.lock=threading.RLock();self.cancel=threading.Event();self.thread=None;self.process=None
  self.data={'running':False,'phase':'ready','runs':[],'plan':list(MODES),'experiment':'aggressive_gc_cached_ten_minutes','limits':{'call_timeout_seconds':60,'test_seconds':600,'followup_seconds':180,'private_commit_bytes':2*1024**3}}
  if os.environ.get('NETOPS_NATIVE_MEMORY_PROFILE')=='1':
   self.data['limits']['test_seconds']=180;self.data['experiment']='native_heap_capture'
  self.modes=None
  if os.environ.get('NETOPS_TRIAGE_PROFILE')=='1':
   self.modes=('triage_control','triage_scalar','triage_object','triage_cached_property')
   self.data.update(plan=list(self.modes),experiment='matched_api_triage',internal_evidence={'ipc_allocations':'not_measured','qt_connections':'not_measured','javascript_retention':'not_measured'})
   self.data['limits'].update(test_seconds=120,followup_seconds=60)
 def snapshot(self):
  with self.lock:return copy.deepcopy(self.data)
 def save(self):
  with self.lock:
   if not self.data.get('report_file'):return
   p=Path(self.data['report_file']);tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(self.data,ensure_ascii=False,indent=2),encoding='utf-8');tmp.replace(p)
 def start(self):
  with self.lock:
   if self.data['running'] or self.diag.snapshot()['running']:raise ValueError('Un diagnostic est déjà en cours.')
   if os.name!='nt':raise ValueError('Suite automatique disponible sous Windows uniquement.')
   memory=read_packet_tracer_memory()
   if memory.get('processes') or memory.get('failures'):raise ValueError('Sauvegarde ton réseau et ferme toutes les fenêtres Packet Tracer avant de lancer la suite.')
   state=self.diag.controller.workspace.state or {};source=Path(state.get('network_file') or '')
   if not source.is_file() or source.suffix.lower()!='.pkt':raise ValueError('Aucune entreprise .pkt enregistrée. Ouvre une entreprise dans NetOps normal avant ce lancement.')
   exe=executable();self.folder.mkdir(parents=True,exist_ok=True)
   import tempfile
   session=Path(tempfile.mkdtemp(prefix='suite-',dir=self.folder));baseline=session/'entreprise-source.pkt';shutil.copy2(source,baseline)
   self.cancel.clear();self.data.update(running=True,phase='starting',runs=[],source=str(source),started_at=time.strftime('%Y-%m-%d %H:%M:%S'),report_file=str(session/'diagnostic-complet.json'),error=None,note='Chaque essai utilise une copie identique et un nouveau processus PT. Surveillance normale et nettoyage expérimental exclus.')
   self.thread=threading.Thread(target=self.run,args=(exe,baseline,session),daemon=True);self.thread.start()
  return self.snapshot()
 def stop(self):
  self.cancel.set();self.diag.stop();return self.snapshot()
 def _wait(self,seconds):return not self.cancel.wait(seconds)
 def _close_owned(self):
  p=self.process
  if p is None:return
  if p.poll() is None:
   # Only the process tree we launched, with a disposable copied project.
   result=subprocess.run(['taskkill','/PID',str(p.pid),'/T','/F'],capture_output=True,timeout=15,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
   try:p.wait(timeout=10)
   except subprocess.TimeoutExpired:raise RuntimeError('Le processus de test ne se ferme pas ; suite arrêtée.')
  self.process=None
 def _memory_guard(self):
  m=read_packet_tracer_memory()
  if not m.get('available'):raise RuntimeError('Mesure mémoire indisponible ; suite arrêtée par précaution : '+m.get('reason',''))
  if sum(p['private_bytes'] for p in m['processes'])>=self.data['limits']['private_commit_bytes']:raise RuntimeError('Limite de 2 Gio engagés atteinte ; essai interrompu et processus de test fermé.')
 def run(self,exe,baseline,session):
  try:
   for index,mode in enumerate(self.modes or MODES):
    if self.cancel.is_set():break
    with self.lock:self.data.update(index=index+1,current=mode,phase='opening')
    trial=session/('%02d-%s.pkt'%(index+1,mode));shutil.copy2(baseline,trial)
    # No ordinary PT instance is allowed to be adopted or terminated.
    m=read_packet_tracer_memory()
    if m.get('processes') or m.get('failures'):raise RuntimeError('Un processus Packet Tracer est encore ouvert ; aucune fermeture de processus non identifié.')
    # Scope this experimental Qt option to the owned PT process only.
    native_profile=os.environ.get('NETOPS_NATIVE_MEMORY_PROFILE')=='1' or os.environ.get('NETOPS_TRIAGE_PROFILE')=='1'
    child_env=packet_tracer_environment(native_profile)
    self.diag.controller.engine.bridge.diagnostic_light_trace=False
    self.diag.controller.engine.bridge.diagnostic_poll_lease=False
    self.diag.controller.engine.bridge.diagnostic_poll_repair=True
    self.process=subprocess.Popen([str(exe),str(trial)],env=child_env)
    began=False;entry={'mode':mode,'file':str(trial),'experiment':self.data['experiment'],'process_environment':{} if native_profile else {'QV4_MM_AGGRESSIVE_GC':'1'}}
    try:
     deadline=time.monotonic()+90;connected=False
     while not self.cancel.is_set() and time.monotonic()<deadline:
      if self.process.poll() is not None:raise RuntimeError('Le lanceur Packet Tracer s’est terminé. Impossible de garantir la propriété du processus ; suite arrêtée.')
      if self.diag.controller.engine.bridge.is_connected:
       with self.diag.controller.engine.lock:opened=json.loads(self.diag.controller.engine.call(FILE_SCRIPT))
       if os.path.normcase(os.path.normpath(opened.get('file','')))==os.path.normcase(os.path.normpath(str(trial))):connected=True;entry['opened']=opened;break
      self._wait(2)
     if self.cancel.is_set():break
     if not connected:raise RuntimeError('Bridge ou ouverture du fichier non confirmé après 90 secondes. Active MCP BUILDER si Packet Tracer le demande.')
     # Disable extra webview events and per-call marker installation for RAM profiling.
     bridge=self.diag.controller.engine.bridge
     if hasattr(bridge,'diagnostic_snapshot'):
      if not bridge.diagnostic_poll_lease:raise RuntimeError('Lecture HTTP exclusive non confirmée ; mesure RAM annulée.')
      with self.diag.controller.engine.lock:
       ready=self.diag.controller.engine.call('window.webview.evaluateJavaScriptAsync("window.__netopsTraceQuiet=true;");reportResult("ready");')
      if ready!='ready':raise RuntimeError('Préparation du profil mémoire non confirmée.')
      bridge.diagnostic_light_trace=True
     entry['instrumentation']='light: no per-call script markers, no webview event posts'
     # Verify connectivity by reading the filename, never infer it from a heartbeat.
     with self.lock:self.data['phase']='testing'
     self.diag.call_timeout=self.data['limits']['call_timeout_seconds']
     entry['call_timeout_seconds']=self.diag.call_timeout
     self.diag.start(mode,duration=self.data['limits']['test_seconds']);began=True
     while self.diag.snapshot()['running']:
      if self.cancel.is_set():self.diag.stop()
      self._memory_guard();self._wait(1)
     self.diag.thread.join(timeout=20)
     failure=self.diag.snapshot().get('error')
     if self.diag.snapshot().get('errors'):
      with self.lock:self.data['error']=failure or 'Le diagnostic a échoué.'
     with self.lock:self.data['phase']='followup_failed' if self.data.get('error') else 'followup'
     until=time.monotonic()+self.data['limits']['followup_seconds']
     while not self.cancel.is_set() and time.monotonic()<until:self._memory_guard();self._wait(2)
     entry['status']='cancelled' if self.cancel.is_set() else 'failed' if self.diag.snapshot().get('errors') else 'completed'
    except Exception as e:
     entry.update(status='error',error=str(e));raise
    finally:
     if began:
      self.diag.stop();self.diag.thread.join(timeout=20);entry['diagnostic']=self.diag.snapshot();entry['memory_summary']=memory_summary(entry['diagnostic'])
     with self.lock:self.data['runs'].append(entry)
     self.save();self._close_owned();self.diag.call_timeout=None;self.diag.controller.engine.bridge.diagnostic_poll_repair=False
    # Let stale bridge heartbeat expire before launching the next owned instance.
    self._wait(11)
  except Exception as e:
   with self.lock:self.data['error']=str(e)
  finally:
   try:self._close_owned()
   except Exception as e:
    with self.lock:self.data['error']=str(e)
   with self.lock:self.data.update(running=False,phase='error' if self.data.get('error') else 'cancelled' if self.cancel.is_set() else 'completed',finished_at=time.strftime('%Y-%m-%d %H:%M:%S'))
   self.save()
   if os.environ.get('NETOPS_TRIAGE_PROFILE')=='1' and self.data.get('report_file'):
    import zipfile
    report=Path(self.data['report_file'])
    with zipfile.ZipFile(report.with_suffix('.zip'),'w',zipfile.ZIP_DEFLATED) as archive:
     archive.write(report,report.name)


def memory_summary(diag):
 """Separate initial acquisition, repeated reads, and follow-up; never sum PIDs."""
 samples=diag.get('process_memory',{}).get('samples',[])
 initial=diag.get('memory_after_initial_inventory',{})
 summaries=[]
 for process in initial.get('processes',[]):
  pid=process['pid'];start=next((p for p in (samples[0].get('processes',[]) if samples else []) if p['pid']==pid),None)
  rows=[(s,p) for s in samples for p in s.get('processes',[]) if p['pid']==pid and p.get('private_bytes') is not None]
  during=[(s,p) for s,p in rows if s['phase']=='test' and s['elapsed']>=30]
  test=[(s,p) for s,p in rows if s['phase']=='test']
  end=test[-1][1] if test else None
  slope=None
  if len(during)>1:
   xs=[s['elapsed'] for s,p in during];ys=[p['private_bytes'] for s,p in during];mx=sum(xs)/len(xs);my=sum(ys)/len(ys);den=sum((x-mx)**2 for x in xs)
   if den:slope=sum((x-mx)*(y-my) for x,y in zip(xs,ys))/den*60
  summaries.append(dict(pid=pid,initial_acquisition_private_bytes=process['private_bytes']-start['private_bytes'] if start else None,repeated_reads_private_bytes=end['private_bytes']-process['private_bytes'] if end else None,slope_after_30s_bytes_per_minute=slope,final_private_bytes=rows[-1][1]['private_bytes'] if rows else None))
 timings=[e['seconds'] for e in diag.get('events',[]) if e.get('kind')=='bridge_call' and isinstance(e.get('seconds'),(int,float))]
 repeated=sorted(timings[1:]);n=len(repeated)
 timing={'successful_calls':len(timings),'initial_seconds':timings[0] if timings else None,'repeated_mean_seconds':sum(repeated)/n if n else None,'repeated_max_seconds':repeated[-1] if n else None,'repeated_median_seconds':(repeated[(n-1)//2]+repeated[n//2])/2 if n else None}
 for summary in summaries:
  delta=summary.get('repeated_reads_private_bytes')
  summary['private_bytes_per_completed_reread']=delta/n if delta is not None and n else None
 return {'command_timing':timing,'per_process':summaries,'object_retrievals':diag.get('object_retrievals'),'value_changes':diag.get('value_changes',0),'note':'Une valeur stable sans modification du réseau ne prouve pas la détection des changements. Aucun verdict automatique de fuite corrigée.'}
