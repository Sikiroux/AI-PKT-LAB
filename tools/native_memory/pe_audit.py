"""Read-only PE64 audit. Does not load or execute the inspected binary."""
import struct,hashlib,json,subprocess,bisect
from pathlib import Path
class PE:
 def __init__(self,path):
  self.path=Path(path);self.b=self.path.read_bytes();h=self.u32(60);self.opt=h+24
  assert self.b[:2]==b'MZ' and self.b[h:h+4]==b'PE\0\0' and self.u16(self.opt)==0x20b
  self.base=self.u64(self.opt+24);self.sections=[]
  for i in range(self.u16(h+6)):
   q=self.opt+self.u16(h+20)+40*i;vs,va,size,offset=struct.unpack_from('<IIII',self.b,q+8);self.sections.append((va,size,offset))
  self.imports={};ir,_=self.directory(1);q=self.off(ir)
  while True:
   ilt,_,_,name,iat=struct.unpack_from('<IIIII',self.b,q);q+=20
   if not name:break
   dll=self.string(self.off(name));j=0
   while True:
    val=self.u64(self.off(ilt or iat)+j*8)
    if not val:break
    self.imports[self.base+iat+j*8]=dll+'!'+(self.string(self.off(val)+2) if val<2**63 else '#'+str(val&65535));j+=1
  pr,ps=self.directory(3);self.functions=[]
  if pr:
   for p in range(self.off(pr),self.off(pr)+ps-11,12):
    start,end,_=struct.unpack_from('<III',self.b,p)
    if start<end:self.functions.append((self.base+start,self.base+end))
  self.functions.sort();self.starts=[a for a,b in self.functions]
 def u16(self,p):return struct.unpack_from('<H',self.b,p)[0]
 def u32(self,p):return struct.unpack_from('<I',self.b,p)[0]
 def u64(self,p):return struct.unpack_from('<Q',self.b,p)[0]
 def directory(self,n):return struct.unpack_from('<II',self.b,self.opt+112+8*n)
 def off(self,r):
  for va,size,p in self.sections:
   if va<=r<va+size:return p+r-va
  raise ValueError(hex(r))
 def at(self,v):return self.off(v-self.base)
 def string(self,p):return self.b[p:self.b.index(0,p)].decode('ascii',errors='replace')
 def bounds(self,v):
  i=bisect.bisect_right(self.starts,v)-1
  if i>=0 and self.functions[i][0]<=v<self.functions[i][1]:return self.functions[i]
  return v,v+128
 def rtti(self,vtable):
  col=self.u64(self.at(vtable)-8);p=self.at(col);td=self.u32(p+12);return self.string(self.off(td)+16)
 def disasm(self,v):
  a,b=self.bounds(v);out=subprocess.check_output(['objdump','-d','-M','intel','--start-address='+hex(a),'--stop-address='+hex(b),str(self.path)],text=True)
  for addr,name in self.imports.items():out=out.replace('# '+hex(addr)+'\n','# '+hex(addr)+' '+name+'\n')
  return out
if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('binary');p.add_argument('output');args=p.parse_args();pe=PE(args.binary);folder=Path(args.output);folder.mkdir(parents=True,exist_ok=True)
 addresses=[0x1403fab80,0x142299d00,0x14236ce93,0x14261b938,0x142249770,0x142272510,0x142272380,0x142272410,0x14275ecf0,0x14276b130,0x142793280,0x143a544f0,0x143ccdb8c]
 manifest={'sha256':hashlib.sha256(pe.b).hexdigest(),'image_base':hex(pe.base),'addresses':{hex(v):[hex(x) for x in pe.bounds(v)] for v in addresses},'imports':{hex(k):v for k,v in pe.imports.items() if any(s in v for s in ['QJSEngine','QJSValue','QObject@@','malloc','free','HeapAlloc','HeapFree'])},'rtti':{}}
 for v in [0x144c36048]:
  try:manifest['rtti'][hex(v)]=pe.rtti(v)
  except (ValueError,struct.error):manifest['rtti'][hex(v)]='unresolved'
 for v in addresses:(folder/(hex(v)+'.asm.txt')).write_text(pe.disasm(v))
 (folder/'manifest.json').write_text(json.dumps(manifest,indent=2))
 print(json.dumps({'sha256':manifest['sha256'],'rtti':manifest['rtti'],'functions':manifest['addresses']},indent=2))
