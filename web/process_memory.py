"""Read Windows process memory without injecting commands into Packet Tracer."""
import copy
import ctypes
from ctypes import wintypes
import os
import threading
import time

class Counters(ctypes.Structure):
 _fields_=[('cb',wintypes.DWORD),('PageFaultCount',wintypes.DWORD)]+[(n,ctypes.c_size_t) for n in ('PeakWorkingSetSize','WorkingSetSize','QuotaPeakPagedPoolUsage','QuotaPagedPoolUsage','QuotaPeakNonPagedPoolUsage','QuotaNonPagedPoolUsage','PagefileUsage','PeakPagefileUsage','PrivateUsage')]
class CountersEx2(ctypes.Structure):
 _fields_=Counters._fields_+[('PrivateWorkingSetSize',ctypes.c_size_t),('SharedCommitUsage',ctypes.c_uint64)]

def query_memory(get_info,handle):
 # EX2 is documented on Windows 10/11 22H2 with September 2023 updates.
 # A sentinel also detects systems which accept cb but fill only older fields.
 missing=ctypes.c_size_t(-1).value
 counters=CountersEx2();counters.cb=ctypes.sizeof(counters);counters.PrivateWorkingSetSize=missing
 if get_info(handle,ctypes.byref(counters),counters.cb):
  private=counters.PrivateWorkingSetSize
  private=private if private!=missing and private<=counters.WorkingSetSize else None
 else:
  counters=Counters();counters.cb=ctypes.sizeof(counters)
  if not get_info(handle,ctypes.byref(counters),counters.cb):return None
  private=None
 return {'working_set_bytes':counters.WorkingSetSize,'private_bytes':counters.PrivateUsage,'private_working_set_bytes':private,'private_working_set_reason':'' if private is not None else 'Compteur privé résident indisponible sur ce Windows.'}

def read_packet_tracer_memory():
 if os.name!='nt':return {'available':False,'reason':'Mesure automatique disponible sous Windows uniquement.'}
 class Entry(ctypes.Structure):
  _fields_=[('dwSize',wintypes.DWORD),('cntUsage',wintypes.DWORD),('th32ProcessID',wintypes.DWORD),('th32DefaultHeapID',ctypes.c_size_t),('th32ModuleID',wintypes.DWORD),('cntThreads',wintypes.DWORD),('th32ParentProcessID',wintypes.DWORD),('pcPriClassBase',wintypes.LONG),('dwFlags',wintypes.DWORD),('szExeFile',wintypes.WCHAR*260)]
 kernel=ctypes.WinDLL('kernel32',use_last_error=True);psapi=ctypes.WinDLL('psapi',use_last_error=True)
 kernel.CreateToolhelp32Snapshot.argtypes=[wintypes.DWORD,wintypes.DWORD];kernel.CreateToolhelp32Snapshot.restype=wintypes.HANDLE
 kernel.Process32FirstW.argtypes=[wintypes.HANDLE,ctypes.POINTER(Entry)];kernel.Process32FirstW.restype=wintypes.BOOL
 kernel.Process32NextW.argtypes=kernel.Process32FirstW.argtypes;kernel.Process32NextW.restype=wintypes.BOOL
 kernel.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD];kernel.OpenProcess.restype=wintypes.HANDLE
 kernel.CloseHandle.argtypes=[wintypes.HANDLE];kernel.CloseHandle.restype=wintypes.BOOL
 psapi.GetProcessMemoryInfo.argtypes=[wintypes.HANDLE,ctypes.c_void_p,wintypes.DWORD];psapi.GetProcessMemoryInfo.restype=wintypes.BOOL
 handle=kernel.CreateToolhelp32Snapshot(2,0)
 if handle==ctypes.c_void_p(-1).value:raise ctypes.WinError(ctypes.get_last_error())
 processes=[];failures=[]
 try:
  entry=Entry();entry.dwSize=ctypes.sizeof(entry);ok=kernel.Process32FirstW(handle,ctypes.byref(entry))
  while ok:
   if entry.szExeFile.lower() in ('packettracer.exe','packettracer8.exe','packettracer9.exe'):
    pid=entry.th32ProcessID;process=kernel.OpenProcess(0x0400|0x0010,False,pid)
    if not process:failures.append({'pid':pid,'error':ctypes.get_last_error()})
    else:
     try:
      memory=query_memory(psapi.GetProcessMemoryInfo,process)
      if memory is not None:processes.append(dict(pid=pid,name=entry.szExeFile,**memory))
      else:failures.append({'pid':pid,'error':ctypes.get_last_error()})
     finally:kernel.CloseHandle(process)
   ok=kernel.Process32NextW(handle,ctypes.byref(entry))
 finally:kernel.CloseHandle(handle)
 return {'available':bool(processes) and not failures,'reason':('Lecture incomplète ou accès refusé.' if failures else '' if processes else 'Processus Packet Tracer introuvable.'),'processes':processes,'failures':failures}

class ProcessMemoryMonitor:
 def __init__(self,reader=read_packet_tracer_memory,clock=time.monotonic,background=True):
  self.reader=reader;self.clock=clock;self.lock=threading.RLock();self.closed=threading.Event();self.started=None;self.ended=None;self.samples=[];self.thread=None
  if background and os.name=='nt':
   self.thread=threading.Thread(target=self._loop,daemon=True);self.thread.start()
 def begin(self):
  with self.lock:self.started=self.clock();self.ended=None;self.samples=[];self.sample()
 def finish(self):
  with self.lock:self.ended=self.clock();self.sample()
 def sample(self):
  with self.lock:
   if self.started is None:return
   try:value=self.reader()
   except Exception as e:value={'available':False,'reason':str(e)}
   self.samples.append(dict(value,elapsed=round(self.clock()-self.started,2),phase='after' if self.ended is not None else 'test'))
   self.samples=self.samples[-400:]
 def _loop(self):
  while not self.closed.wait(2):
   with self.lock:
    if self.started is not None and (self.ended is None or self.clock()-self.ended<=180):self.sample()
 def snapshot(self):
  with self.lock:
   return {'interval_seconds':2,'followup_seconds':180,'samples':copy.deepcopy(self.samples),'supported':os.name=='nt'}
 def close(self):self.closed.set()
