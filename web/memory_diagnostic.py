"""Bounded, opt-in isolation of PT calls. Never changes network configuration."""
import json
import hashlib
from process_memory import ProcessMemoryMonitor
from diagnostic_payloads import OK_SCRIPT, PAYLOAD_SCRIPT, CLEANUP_SCRIPT, INVENTORY_PROBES, GC_TRACE_STEPS, GC_TRANSPORT_STEPS
import copy
import threading
import time

class MemoryDiagnostic:
 def __init__(self,controller,clock=time.monotonic):
  self.memory=ProcessMemoryMonitor();self.controller=controller;self.clock=clock;self.lock=threading.RLock();self.stop_event=threading.Event();self.thread=None
  self.data={'mode':'pause','running':False,'phase':'ready','duration':180,'cycles':0,'calls':0,'errors':0,'request_bytes':0,'response_bytes':0,'events':[]}
  if hasattr(getattr(controller.engine,'bridge',None),'diagnostic_snapshot'):controller.engine.bridge.diagnostic_events=[]
  original=controller.engine.call
  def measured(code,*args,**kwargs):
   started=self.clock()
   with self.lock:
    self.data['calls']+=1;self.data['request_bytes']+=len(code.encode('utf-8'))
   try:
    if getattr(self,'call_timeout',None) is not None and not args and 'timeout' not in kwargs:kwargs['timeout']=self.call_timeout
    result=original(code,*args,**kwargs)
    self.record('bridge_call',seconds=round(self.clock()-started,3),response_bytes=len(str(result).encode('utf-8')))
    with self.lock:self.data['response_bytes']+=len(str(result).encode('utf-8'))
    return result
   except Exception as e:
    self.record('bridge_error',error=str(e));raise
  controller.engine.call=measured
 def record(self,kind,**values):
  with self.lock:
   if kind=='run_error':self.data['errors']+=1;self.data['error']=values.get('error')
   self.data['events'].append(dict(kind=kind,elapsed=round(self.clock()-self.data.get('started',self.clock()),3),**values))
   self.data['events']=self.data['events'][-(2000 if self.data.get('duration',180)>180 else 1000):]
 def snapshot(self):
  with self.lock:
   out=copy.deepcopy(self.data);out['elapsed']=round(max(0,self.clock()-out['started']),1) if out.get('running') else out.get('elapsed',0)
   if hasattr(getattr(self.controller.engine,'bridge',None),'diagnostic_snapshot'):out['transport']=self.controller.engine.bridge.diagnostic_snapshot()
   out['remaining']=round(max(0,out['duration']-out['elapsed']),1);out.pop('started',None);out['process_memory']=self.memory.snapshot();return out
 def start(self,mode,duration=180):
  if mode not in ('pause','inventory','pings','full','ok','payload','inventory_clean')+tuple(INVENTORY_PROBES):raise ValueError('Mode inconnu.')
  maximum=600 if mode=='inventory_cached_all' else 180
  if type(duration) is not int or not 1<=duration<=maximum:raise ValueError('Durée de 1 à '+str(maximum)+' secondes.')
  with self.lock:
   if self.thread and self.thread.is_alive():raise ValueError('Attends la fin du contrôle en cours.')
   if mode not in ('pause','ok','payload') and not self.controller.workspace.state:raise ValueError('Ouvre une entreprise existante dans NetOps normal avant ce diagnostic.')
   self.stop_event.clear();self.data=dict(mode=mode,running=True,phase='running',duration=duration,started=self.clock(),cycles=0,calls=0,errors=0,request_bytes=0,response_bytes=0,events=[],started_at=time.strftime('%Y-%m-%d %H:%M:%S'),environment_id=(self.controller.workspace.state or {}).get('environment_id'))
   self.memory.begin()
   self.thread=threading.Thread(target=self.run,daemon=True);self.thread.start()
  return self.snapshot()
 def stop(self):
  self.stop_event.set()
  with self.lock:
   if self.data['running']:self.data['phase']='stopping'
  return self.snapshot()
 def allowed(self):
  return not self.stop_event.is_set() and self.clock()-self.data['started']<self.data['duration']
 def run(self):
  c=self.controller;mode=self.data['mode'];state=None;found=None
  trace_steps=GC_TRANSPORT_STEPS if mode=='inventory_gc_transport' else GC_TRACE_STEPS
  try:
   if mode=='pings' and self.allowed():
    # Exactly one inventory, counted as setup; no repeated identity lookups.
    with c.lock,c.engine.lock:
     state=copy.deepcopy(c.workspace.state);found=c.identities(c.engine.snapshot(),partial=True)
    self.record('setup_inventory',devices=len(found))
   while self.allowed():
    if mode=='pause':self.stop_event.wait(min(.2,max(0,self.data['duration']-(self.clock()-self.data['started']))));continue
    with c.lock:
     if not self.allowed():break
     if mode=='full':c.observe()
     elif mode in ('ok','payload'):
      with c.engine.lock:response=c.engine.call(OK_SCRIPT if mode=='ok' else PAYLOAD_SCRIPT)
      expected='OK' if mode=='ok' else 'x'*42072
      if response!=expected:raise ValueError('Réponse fixe inattendue : essai interrompu.')
      self.record('fixed_response',bytes=len(response.encode('utf-8')))
     elif mode in INVENTORY_PROBES:
      script=INVENTORY_PROBES[mode]
      if mode in ('inventory_gc_trace','inventory_gc_transport'):
       step,script=trace_steps[self.data['cycles']];self.record('trace_started',step=step)
      with c.engine.lock:result=json.loads(c.engine.call(script))
      if mode in ('inventory_gc_trace','inventory_gc_transport'):self.record('trace_completed',step=step,response=result)
      if not isinstance(result,dict) or 'error' in result:raise ValueError('Lecture partielle échouée : '+str(result))
      if mode=='inventory_cached_all':
       digest=hashlib.sha256(json.dumps(result['devices'],sort_keys=True,ensure_ascii=False).encode()).hexdigest()
       with self.lock:
        previous=self.data.get('inventory_digest');self.data['inventory_digest']=digest
        self.data['value_changes']=self.data.get('value_changes',0)+(1 if previous and previous!=digest else 0)
        self.data['object_retrievals']=self.data.get('object_retrievals',0)+result.get('objects',0)
        if self.data['cycles']==0:
         self.memory.sample();self.data['initial_inventory_elapsed']=round(self.clock()-self.data['started'],3)
         self.data['memory_after_initial_inventory']=self.memory.snapshot()['samples'][-1]
       if previous and previous!=digest:self.record('inventory_values_changed',digest=digest)
      if mode=='inventory_count':
       if type(result.get('device_count')) is not int:raise ValueError('Comptage inattendu.')
       self.record('inventory_probe',probe=mode,devices=result['device_count'])
      else:
       if not isinstance(result.get('devices'),list):raise ValueError('Inventaire partiel inattendu.')
       self.record('inventory_probe',probe=mode,devices=len(result['devices']),ports=sum(len(d.get('ports',[])) for d in result['devices']),**{k:result[k] for k in ('objects','cache','gc','gc_error','cached_devices','cached_ports','batch_operations') if k in result})
     elif mode in ('inventory','inventory_clean'):
      with c.engine.lock:result=c.engine.snapshot()
      self.record('inventory',devices=len(result.get('devices',[])))
      if mode=='inventory_clean' and self.data['cycles']%10==0 and self.allowed():
       with c.engine.lock:cleanup=json.loads(c.engine.call(CLEANUP_SCRIPT))
       if not isinstance(cleanup,dict) or cleanup.get('supported') is not True:raise ValueError('Nettoyage non confirmé : '+str(cleanup))
       self.record('logs_cleaned',**cleanup)
     else:
      import network_observer
      with c.engine.lock:probes=network_observer.collect(c.engine,state,found,time.time,False)
      self.record('pings',statuses={k:v['status'] for k,v in probes.items()})
     with self.lock:self.data['cycles']+=1
    if mode in ('inventory_gc_trace','inventory_gc_transport') and self.data['cycles']>=len(trace_steps):break
    # Match the existing loop's one-second delay after completion.
    self.stop_event.wait(min(1,max(0,self.data['duration']-(self.clock()-self.data['started']))))
  except Exception as e:self.record('run_error',error=str(e))
  finally:
   with self.lock:
    self.memory.finish()
    self.data['elapsed']=round(self.clock()-self.data['started'],1);self.data['running']=False;self.data['phase']='stopped'
   self.record('stopped',requested=self.stop_event.is_set())

 def close(self):
  if getattr(self,'suite',None):
   self.suite.stop()
   if self.suite.thread:self.suite.thread.join(timeout=40)
  self.stop();self.memory.close()
