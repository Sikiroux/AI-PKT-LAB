"""VLAN d’accès : lecture IOS fraîche, port conservé, VLAN isolé réservé au ticket."""
import json,re,time

def valid_port(port):
 if not re.fullmatch(r'(FastEthernet|GigabitEthernet)0/[0-9]+',port):raise ValueError('Port invalide.')
 return port

def parse_switchport(text,port):
 valid_port(port)
 name=re.search(r'^\s*Name:\s*(\S+)\s*$',text,re.M|re.I)
 def normalize(value):return value.replace('FastEthernet','Fa').replace('GigabitEthernet','Gi').lower()
 if not name or normalize(name.group(1))!=normalize(port):raise ValueError('Le résultat IOS ne correspond pas au port demandé.')
 fields={}
 for label,key in [('Switchport','enabled'),('Administrative Mode','admin'),('Operational Mode','operational'),('Access Mode VLAN','vlan')]:
  match=re.search(r'^\s*'+label+r':\s*([^\r\n]+)',text,re.M|re.I)
  if not match:raise ValueError('Lecture switchport incomplète : '+label)
  fields[key]=match.group(1).strip()
 match=re.fullmatch(r'(\d+)(?:\s+\([^\r\n]*\))?',fields['vlan'])
 if not match or not 1<=int(match.group(1))<=4094:raise ValueError('VLAN illisible.')
 fields['vlan']=int(match.group(1))
 if fields['enabled'].lower()!='enabled' or fields['operational'].lower() not in ('static access','access'):raise ValueError('Port d’accès actif requis ; les trunks sont exclus.')
 if fields['admin'].lower() not in ('static access','access','dynamic auto','dynamic desirable'):raise ValueError('Mode administratif non pris en charge.')
 return fields

def fresh_command(engine,command):
 before=engine.call('var c=ipc.network().getDevice("SW1").getCommandLine();var o=String(c.getOutput());c.enterCommand("end");c.enterCommand("enable");c.enterCommand('+json.dumps(command)+');reportResult(o);')
 deadline=time.monotonic()+5
 while time.monotonic()<deadline:
  output=engine.call('reportResult(String(ipc.network().getDevice("SW1").getCommandLine().getOutput()));')
  if not output.startswith(before):raise ValueError('Tampon CLI modifié pendant la lecture ; réessaie.')
  fresh=output[len(before):];position=fresh.rfind(command)
  if position>=0 and re.search(r'[\w.-]+#\s*$',fresh):
   result=fresh[position+len(command):]
   if re.search(r'% (Invalid|Ambiguous|Incomplete)',result):raise ValueError('Commande de lecture VLAN non prise en charge.')
   return result
  time.sleep(.15)
 raise ValueError('Lecture VLAN fraîche non confirmée ; aucune valeur par défaut présumée.')

def read(engine,port):
 valid_port(port)
 return parse_switchport(fresh_command(engine,'show interfaces '+port+' switchport'),port)

def vlan_ids(engine):
 code='''try {var d=ipc.network().getDevice("SW1"),m=d.getProcess("VlanManager"),ids=[];
 if(!m)throw new Error("VlanManager absent");var n=m.getVlanCount();if(n<1||n>4094)throw new Error("Inventaire invalide");
 for(var i=0;i<n;i++){var v=m.getVlanAt(i);if(v)ids.push(v.getVlanNumber());}reportResult(JSON.stringify(ids));
 }catch(e){reportResult(JSON.stringify({error:String(e)}));}'''
 values=json.loads(engine.call(code))
 if not isinstance(values,list) or not values or any(not isinstance(n,int) or isinstance(n,bool) or not 1<=n<=4094 for n in values):raise ValueError('Inventaire VLAN non confirmé.')
 return set(values)

def plan(engine,port):
 original=read(engine,port);used=vlan_ids(engine)
 isolated=next((n for n in range(999,899,-1) if n not in used),None)
 if isolated is None:raise ValueError('Aucun VLAN d’isolement libre dans la plage 900–999.')
 return dict(kind='vlan_wrong',port=port,before_vlan=original['vlan'],after_vlan=isolated,before_admin=original['admin'],before_operational=original['operational'])

def apply(engine,injection,restore):
 port=valid_port(injection['port']);vlan=injection['before_vlan' if restore else 'after_vlan']
 if not isinstance(vlan,int) or not 1<=vlan<=4094:raise ValueError('VLAN invalide.')
 current=read(engine,port)
 if current['admin']!=injection['before_admin']:raise ValueError('Le mode du port a changé ; restauration automatique bloquée.')
 commands=['enable','configure terminal']
 if not restore:
  if current['vlan']!=injection['before_vlan'] or vlan in vlan_ids(engine):raise ValueError('Configuration VLAN modifiée avant injection.')
  commands+=['vlan '+str(vlan),'name NETOPS_ISO_'+str(vlan),'exit']
 commands+=['interface '+port,'switchport access vlan '+str(vlan),'end']
 return engine.call('configureIosDevice("SW1", '+json.dumps('\n'.join(commands))+');reportResult("ok");')

def matches(engine,injection,restore):
 current=read(engine,injection['port'])
 return current['vlan']==injection['before_vlan' if restore else 'after_vlan'] and current['admin']==injection['before_admin']

def remove_unused(engine,injection):
 vlan=injection['after_vlan']
 if vlan not in vlan_ids(engine):return dict(removed=True,message='VLAN temporaire déjà absent.')
 text=fresh_command(engine,'show vlan brief')
 rows=text.splitlines()
 for index,line in enumerate(rows):
  match=re.match(r'^\s*'+str(vlan)+r'\s+(\S+)\s+(\S+)(.*)$',line)
  if not match:continue
  if match.group(1)!='NETOPS_ISO_'+str(vlan):return dict(removed=False,message='VLAN renommé : conservé pour éviter une suppression inattendue.')
  continuation=rows[index+1] if index+1<len(rows) else ''
  if match.group(3).strip() or re.search(r'(?:Fa|Gi|FastEthernet|GigabitEthernet)\d+/',continuation):return dict(removed=False,message='VLAN encore utilisé : conservé.')
  if match.group(2).lower()!='active':return dict(removed=False,message='État du VLAN non reconnu : conservé.')
  command='enable\nconfigure terminal\nno vlan '+str(vlan)+'\nend'
  ack=engine.call('configureIosDevice("SW1", '+json.dumps(command)+');reportResult("ok");')
  removed=ack=='ok' and vlan not in vlan_ids(engine)
  return dict(removed=removed,message='VLAN temporaire retiré.' if removed else 'Suppression du VLAN non confirmée.')
 return dict(removed=False,message='Lecture du VLAN temporaire incomplète : conservé.')
