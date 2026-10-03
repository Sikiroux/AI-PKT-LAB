import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[2]))
"""Convention de noms et implantation physique, après les mutations pédagogiques."""
import copy,re,uuid,json,html
import xml.etree.ElementTree as ET
KNOWN={'R1':'RTR-01','ISP':'RTR-ISP-01','SW1':'SW-01','SW-EMP':'SW-USR-01','SW-SRV':'SW-SRV-01','SW-GUEST':'SW-ACC-01','SW-WAN':'SW-WAN-01','SW-LAN':'SW-LAN-01','PC-ADMIN':'PC-IT-01','PC-ALICE':'PC-CPT-01','PC-BOB':'PC-CPT-02','PC-GUEST':'PC-ACC-01','PC-CLIENT':'PC-USR-01','SRV-INFRA':'SRV-INF-01','SRV-WEB':'SRV-WEB-01','SRV-WEB2':'SRV-WEB-02','SRV-FTP':'SRV-FIC-01','SRV-MAIL':'SRV-MSG-01','AP1':'AP-01','MX1':'FW-01','MERAKI-CLOUD':'SRV-MRK-01','WEB-PUBLIC':'SRV-PUB-01'}
def prefix(value):
 value=str(value).upper()
 if not re.fullmatch(r'[A-Z][A-Z0-9]{1,5}',value):raise ValueError('Code de site : 2 à 6 lettres/chiffres, commençant par une lettre.')
 return value

def mapping(names,site='AG1'):
 site=prefix(site);out={};used=set()
 for index,name in enumerate(sorted(set(names)),1):
  suffix=KNOWN.get(name,re.sub(r'[^A-Z0-9-]','',name.upper())[:12] or 'DEV-'+str(index))
  candidate=site+'-'+suffix
  if candidate in used:candidate+='-'+str(index)
  out[name]=candidate;used.add(candidate)
 return out

def replace(text,names):
 if not names:return text
 pattern=r'(?<![A-Za-z0-9_-])('+ '|'.join(re.escape(x) for x in sorted(names,key=len,reverse=True))+r')(?![A-Za-z0-9_-])'
 return re.sub(pattern,lambda m:names[m.group(0)],text)

def rename_tree(root,names):
 for node in root.iter():
  if node.text:node.text=replace(node.text,names)
  for key,value in list(node.attrib.items()):node.set(key,replace(value,names))

def value(node,tag,text):
 child=node.find(tag)
 if child is None:child=ET.SubElement(node,tag)
 child.text=str(text)

def physical(root,names,site='AG1'):
 """Réutilise les modèles de pièces/racks et recalcule leurs références UUID."""
 pw=root.find('PHYSICALWORKSPACE');devices=root.findall('NETWORK/DEVICES/DEVICE')
 if pw is None or not devices:return []
 nodes=list(pw.iter('NODE'));building=next((n for n in nodes if n.findtext('TYPE')=='2'),None)
 closet=next((n for n in nodes if n.findtext('TYPE')=='3'),None)
 rack=next((n for n in nodes if n.findtext('TYPE')=='4'),None)
 if any(n is None for n in (building,closet,rack)):return []
 ids={n.findtext('TYPE'):n.findtext('UUID_STR') for n in nodes if n.findtext('TYPE') in ('0','1','2')}
 if not all(ids.get(x) for x in ('0','1','2')):return []
 templates={n.findtext('UUID_STR'):copy.deepcopy(n) for n in nodes if n.findtext('TYPE')=='6'}
 # Reject an incomplete physical model before removing any original device node.
 for device in devices:
  dev_uuid=device.findtext('WORKSPACE/PHYSICAL','').split(',')[-1].strip()
  if not dev_uuid or dev_uuid not in templates:raise ValueError('Modèle physique incomplet : appareil sans emplacement de référence.')
 value(building,'NAME','Agence '+site);value(closet,'NAME','Local technique');value(rack,'NAME','Baie '+site+'-01')
 children=building.find('CHILDREN')
 if children is None:children=ET.SubElement(building,'CHILDREN')
 rooms={}
 room_labels=('Bureau IT','Bureaux utilisateurs','Accueil') if any('ADMIN' in {v:k for k,v in names.items()}.get(d.findtext('ENGINE/NAME'),d.findtext('ENGINE/NAME','')) for d in devices) else ('Bureaux utilisateurs','Accueil')
 for index,label in enumerate(room_labels,1):
  room=copy.deepcopy(closet);value(room,'NAME',label);value(room,'UUID_STR','{'+str(uuid.uuid5(uuid.NAMESPACE_URL,site+label+ids['2']))+'}');value(room,'X',index*180);value(room,'Y',220)
  old=room.find('CHILDREN')
  if old is not None:room.remove(old)
  ET.SubElement(room,'CHILDREN');children.append(room);rooms[label]=room
 templates={n.findtext('UUID_STR'):copy.deepcopy(n) for n in nodes if n.findtext('TYPE')=='6'}
 # Remove existing device nodes before placing each device exactly once.
 for parent in pw.iter():
  for child in list(parent):
   if child.tag=='NODE' and child.findtext('TYPE')=='6':parent.remove(child)
 reverse={v:k for k,v in names.items()};rows=[];rack_index=0;room_indexes={k:0 for k in rooms}
 for d in devices:
  engine=d.find('ENGINE');workspace=d.find('WORKSPACE')
  if engine is None or workspace is None:continue
  name=engine.findtext('NAME');model=engine.find('TYPE').get('model','');original=reverse.get(name,name)
  old_path=workspace.findtext('PHYSICAL','');dev_uuid=old_path.split(',')[-1].strip()
  if not dev_uuid or dev_uuid not in templates:continue
  in_rack=model.startswith(('Server','2960','2911','3560')) or original.startswith(('SW','R1','SRV','MX'))
  if in_rack:
   target=rack;parents=[ids['0'],ids['1'],ids['2'],closet.findtext('UUID_STR')];path=parents+[rack.findtext('UUID_STR'),dev_uuid]
   slot=rack_index;x=4+(slot%10)*4;y=(slot//10)*4;rack_index+=1;location='Local technique / '+rack.findtext('NAME');container=rack.findtext('UUID_STR')
  else:
   label='Bureau IT' if 'ADMIN' in original else ('Accueil' if 'GUEST' in original else 'Bureaux utilisateurs')
   target=rooms[label];parents=[ids['0'],ids['1'],ids['2'],target.findtext('UUID_STR')];path=parents+[dev_uuid]
   slot=room_indexes[label];room_indexes[label]+=1;x=80+slot*100;y=180;location=label;container=target.findtext('UUID_STR')
  value(workspace,'PHYSICAL',','.join(path));cpur=workspace.find('PHYSICAL_CPUR')
  if cpur is None:cpur=ET.SubElement(workspace,'PHYSICAL_CPUR')
  for tag,val in [('X',x),('Y',y),('X_PN',x),('Y_PN',y),('SLOT',slot),('SUBSLOT',0),('PARENT_PATH',','.join(parents)),('CONTAINER_ID',container)]:value(cpur,tag,val)
  node=templates[dev_uuid];target.find('CHILDREN').append(node)
  for tag,val in [('TYPE',6),('NAME',name),('UUID_STR',dev_uuid),('X',x),('Y',y),('SLOT',slot),('SUB_SLOT',0),('SX',1),('SY',1)]:value(node,tag,val)
  rows.append(dict(device=name,model=model,location=location,slot=slot if in_rack else None))
 return rows

def finalize(folder,site='AG1',business=True):
 folder=__import__('pathlib').Path(folder);site=prefix(site)
 initial=folder/'initial.xml';baseline=folder/'baseline.xml'
 if not initial.exists() or not baseline.exists():return dict(applied=False,reason='Organisation avancée réservée aux topologies d’ateliers et services.')
 root=ET.parse(initial).getroot()
 device_names=[d.findtext('ENGINE/NAME') for d in root.findall('NETWORK/DEVICES/DEVICE')]
 if (folder/'reference.xml').exists():
  reference_root=ET.parse(folder/'reference.xml').getroot()
  device_names.extend(d.findtext('ENGINE/NAME') for d in reference_root.findall('NETWORK/DEVICES/DEVICE'))
 names=mapping(device_names,site) if business else {}
 rows=[]
 for filename in ('initial.xml','baseline.xml','reproduction.xml','reference.xml','activity.xml'):
  path=folder/filename
  if not path.exists():continue
  tree=ET.parse(path);rename_tree(tree.getroot(),names)
  # An activity embeds both initial and answer network snapshots.
  for candidate in list(tree.getroot().iter()):
   if candidate.find('PHYSICALWORKSPACE') is not None:
    layout=physical(candidate,names,site)
    if filename=='initial.xml':rows=layout
  if filename=='activity.xml' and rows:
   appendix=layout_html(rows)
   for element in tree.getroot().iter():
    if element.text and '<html' in element.text and '</body>' in element.text:element.text=element.text.replace('</body>',appendix+'</body>')
  ET.indent(tree,space=' ');tree.write(path,encoding='utf-8',short_empty_elements=False)
 for filename in ('consignes.html','solution.json'):
  path=folder/filename
  if path.exists():
   content=replace(path.read_text(encoding='utf-8'),names)
   if filename=='consignes.html' and rows:content=content.replace('<h2>Indices progressifs</h2>',layout_html(rows)+'<h2>Indices progressifs</h2>')
   path.write_text(content,encoding='utf-8')
 plan=dict(applied=True,site=site,names=names,placements=rows,note='Slots du modèle Packet Tracer ; implantation et encombrement à vérifier visuellement.')
 (folder/'implantation.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2),encoding='utf-8')
 return plan

def layout_html(rows):
 result='<section><h2>Implantation physique</h2><p>Ouvre la vue physique : local technique et baie, bureaux utilisateurs et accueil ; bureau IT lorsqu’un poste dédié est présent. Les positions dans la baie restent à contrôler visuellement dans Packet Tracer.</p><table><tr><th>Appareil</th><th>Emplacement</th></tr>'
 for row in rows:result+='<tr><td>'+html.escape(row['device'])+'</td><td>'+html.escape(row['location'])+'</td></tr>'
 return result+'</table></section>'
