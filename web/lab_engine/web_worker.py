import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[2]))
"""Génération isolée : aucun accès au réseau de travail du pont."""
import contextlib,io,json,random,sys
from pathlib import Path
import builder,faults,workshops,ptexplorer
import reproduction,worksheet_answers,hashlib,organization
import xml.etree.ElementTree as ET
PAIRS=[('configure_mail','dns_service_off'),('configure_ftp','http_service_off'),('configure_dns','tftp_service_off'),('configure_dhcp_relay','http_service_off'),('configure_mail','http_service_off'),('configure_ftp','dns_service_off'),('add_web_server','http_service_off')]
def catalogue():
 out=[dict(id=k,title=v['title'],mode='depannage' if v['kind']=='fault' else 'atelier',topology=v['topology'],level=v['level']) for k,v in workshops.CATALOGUE.items()]
 out += [dict(id='classic:'+k,title=k.replace('_',' '),mode='depannage',topology=', '.join(v['topos']),level=v['level']) for k,v in faults.CATALOGUE.items()]
 out += [dict(id='mixed:'+str(i),title=workshops.CATALOGUE[a]['title']+' + '+workshops.CATALOGUE[b]['title'],mode='mixte',topology=workshops.CATALOGUE[a]['topology'],level=max(workshops.CATALOGUE[a]['level'],workshops.CATALOGUE[b]['level'])) for i,(a,b) in enumerate(PAIRS)]
 out += [dict(id=k,title=v["title"],mode="reproduction",topology=workshops.CATALOGUE[v["source"]]["topology"],level=workshops.CATALOGUE[v["source"]]["level"]) for k,v in reproduction.SCENARIOS.items()]
 return out

def generate(req):
 folder=Path(req['folder']);folder.mkdir(parents=True,exist_ok=True);seed=req['seed'];scenario=req['scenario'];level=req['level'];count=req['count']
 if req.get('ticket_title') and scenario in workshops.CATALOGUE:workshops.CATALOGUE[scenario]=dict(workshops.CATALOGUE[scenario],title=req['ticket_title'])
 if scenario.startswith('classic:'):
  fid=scenario.split(':',1)[1];spec=faults.CATALOGUE[fid];topology=random.Random(seed).choice(spec['topos'])
  _,topo=builder.build(topology,seed=seed,output_dir=str(folder))
  faults.inject(topo,level=level,fault_ids=[fid],count=count,seed=seed,output_path=str(folder/'lab.pka'),lang='fr')
  (folder/'consignes.html').write_text((folder/'lab.html').read_text(encoding='utf-8'),encoding='utf-8')
  # Socle sain séparé pour consultation de la correction.
  import shutil
  shutil.copy2(topo['pkt_path'],folder/'correction.pkt')
 else:
  reproduce_mutation=reproduction.install(scenario) if scenario in reproduction.SCENARIOS else None
  if scenario.startswith('mixed:'):
   a,b=PAIRS[int(scenario.split(':')[1])];first=workshops.CATALOGUE[a];second=workshops.CATALOGUE[b]
   def mutate(root,topo):first['mutate'](root,topo);second['mutate'](root,topo)
   workshops.CATALOGUE[scenario]=dict(first,title=first['title']+' + '+second['title'],kind='evolution',mutate=mutate,statement='Partie atelier : '+first['statement']+'\nPartie dépannage : '+second['statement'],hints=first['hints']+second['hints'],solution=first['solution']+'\n'+second['solution'],tests=first['tests']+second['tests'])
  meta=workshops.generate(scenario,seed=seed,output_dir=str(folder),address_family=req.get('address_family'))
  if reproduce_mutation:
   tree=ET.parse(folder/'baseline.xml');reproduce_mutation(tree.getroot(),meta['topology']);ET.indent(tree,space=' ');tree.write(folder/'reproduction.xml',encoding='utf-8',short_empty_elements=False)
   ptexplorer.ptfile_encode(str(folder/'reproduction.xml'),str(folder/'correction.pkt'))
  else:ptexplorer.ptfile_encode(str(folder/'baseline.xml'),str(folder/'correction.pkt'))
  layout=organization.finalize(folder,req.get('site_code','AG1'),business=not bool(req.get('ticket_title')))
  if layout['applied']:
   for source,target in [('initial.xml','lab.pkt'),('activity.xml','lab.pka'),('reproduction.xml' if reproduce_mutation else 'baseline.xml','correction.pkt')]:
    ptexplorer.ptfile_encode(str(folder/source),str(folder/target))
 # Compte rendu saisissable dans le HTML compagnon.
 html=(folder/'consignes.html').read_text(encoding='utf-8')
 form='<section><h2>Ton compte rendu</h2><table><tr><th>Observation / test</th><th>Réponse</th></tr>'
 for prompt in ['Symptômes observés','Diagnostic et justification','Actions réalisées','Adresses finales retenues','Tests de réussite et de refus']:
  form+='<tr><td>'+prompt+'</td><td><textarea aria-label="'+prompt+'" style="width:100%;min-height:70px"></textarea></td></tr>'
 form+='</table><p>Utilise l’impression du navigateur pour conserver tes réponses. La sauvegarde locale et l’export JSON sont disponibles ci-dessous.</p><button onclick="window.print()">Imprimer mes réponses</button></section>'
 key=hashlib.sha256((str(folder.resolve())+str(seed)+scenario).encode()).hexdigest()[:24]
 html=html.replace('</body>',form+worksheet_answers.script(key)+'</body>');(folder/'consignes.html').write_text(html,encoding='utf-8')
 return {'correction_label':'Exemple de panne reproduite' if scenario in reproduction.SCENARIOS else 'Réseau de référence (socle sain)', 'scenario':None if req.get('ticket_title') else scenario,'seed':seed,'validation':'Correction et tests manuels dans Packet Tracer','files':[p.name for p in folder.iterdir() if p.name in ('lab.pka','lab.pkt','consignes.html','correction.pkt','implantation.json')]}
if __name__=='__main__':
 if sys.argv[1]=='catalogue':print(json.dumps(catalogue(),ensure_ascii=False))
 else:
  req=json.loads(sys.stdin.read())
  with contextlib.redirect_stdout(io.StringIO()):result=generate(req)
  print(json.dumps(result,ensure_ascii=False))
