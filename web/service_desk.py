"""Arrivées de tickets sur le site persistant ou des réseaux indépendants."""
import random,time,sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))
from addressing import private_networks
from lab_engine import organization
import timers
import procedural,live_faults
import site_services
CATALOGUE=[
 ('dns_service_off','Les employés ne retrouvent plus les services par leur nom','Les employés indiquent que les accès par adresse IP fonctionnent, mais plus les noms des services.','elevee'),
 ('dns_record_delete','Un intranet inaccessible par son nom','La comptabilité ne peut plus ouvrir intranet.entreprise.test ; le nom du dépôt FTP fonctionne toujours.','moderee'),
 ('http_service_off','La page intranet ne s’ouvre plus','Les postes peuvent joindre le serveur, mais le navigateur n’affiche plus l’intranet.','elevee'),
 ('ftp_service_off','Le dépôt documentaire ne répond plus','Les utilisateurs ne peuvent plus se connecter au dépôt FTP, alors que le serveur répond au ping.','moderee'),
 ('ftp_write_denied','Impossible de déposer les documents','Le compte depot se connecte et liste les fichiers, mais les transferts vers le dépôt sont refusés.','moderee'),
 ('ftp_password_wrong','Un compte ne peut plus accéder au dépôt','lecteur se connecte normalement ; depot/Depot123 est refusé.','moderee'),
 ('dhcp_server_off','Les postes ne reçoivent plus leur configuration réseau','Un poste employé configuré en DHCP ne reçoit plus d’adresse utilisable.','elevee'),
 ('tftp_service_off','La sauvegarde réseau échoue','L’équipe IT ne peut plus transférer la sauvegarde de R1 vers le serveur TFTP.','faible'),
]
CATALOGUE += [
 ('dns_record_wrong','Le nom de l’intranet ne mène plus à la bonne page','intranet.entreprise.test ne mène plus à la page attendue ; ftp.entreprise.test fonctionne toujours.','moderee'),
 ('dhcp_relay_missing','Un poste ne reçoit plus de bail DHCP','PC-ALICE ne reçoit pas de bail DHCP ; PC-BOB en statique reste fonctionnel.','elevee'),
 ('dhcp_relay_wrong','Un poste ne reçoit plus de bail DHCP','PC-ALICE ne reçoit pas de bail DHCP ; PC-BOB en statique reste fonctionnel.','elevee'),
]
CATALOGUE += [(fid,title,complaint,'moderee') for fid,title,complaint in [
 ('local_wrong_ip','Un poste ne communique plus','PC-ALICE ne joint plus les services ; PC-BOB fonctionne.'),
 ('local_wrong_mask','Un poste ne joint plus les services distants','PC-ALICE ne joint plus les services ; PC-BOB fonctionne.'),
 ('local_wrong_gateway','Un poste ne joint plus les serveurs','PC-ALICE communique avec les employés, mais pas avec les serveurs ; PC-BOB fonctionne.'),
 ('local_wrong_dns','Un poste ne retrouve plus l’intranet','PC-ALICE ouvre l’intranet par IP mais pas par son nom ; PC-BOB fonctionne.'),
 ('add_employee','Installer le poste d’un nouvel employé','Un nouvel employé arrive : installer PC-NEW suivant la feuille, sans modifier les postes existants.')]]
SITE_CATALOGUE=[dict(id='site:http',title='Incident HTTP du site — API requise'),dict(id='site:dns',title='Incident DNS du site — API requise'),dict(id='site:dhcp',title='Incident DHCP du site — API requise'),dict(id='pc',title='Installer un nouveau poste'),dict(id='wifi',title='Connecter un nouveau portable'),dict(id='incident',title='Dépanner un poste filaire du site')]
def site_choices(snapshot,opened):
 names={d['name']:d for d in snapshot['devices']}
 kinds={t['kind'] for t in opened if t['kind']!='service'}
 choices=[]
 switch=names.get('SW1',{})
 free=any(p.get('name','').startswith('FastEthernet0/') and not p.get('linked') for p in switch.get('ports',[]))
 if 'pc' not in kinds and free:choices.append(('pc',None))
 if 'wifi' not in kinds and 'AP1' in names:choices.append(('wifi',None))
 # An incident must not interfere with an unfinished intervention on this site.
 if not kinds:
  for d in snapshot['devices']:
   if d.get('model')=='PC-PT' and any(p.get('linked') and p.get('up') and p.get('protocol_up') and not p.get('wireless') for p in d.get('ports',[])):
    choices.append(('incident',d['name']))
 return choices
class ServiceDesk:
 def __init__(self,tickets,generator):
  self.t=tickets;self.g=generator
  self.settings=self.t.state.setdefault('session',dict(active=False,interval='fixed',minimum=5,maximum=10,max_open=3,ticket_minutes=30,next_at=None,message='Session arrêtée.'))
  self.settings.setdefault('live_services',False);self.settings.setdefault('fault_mode','random');self.settings.setdefault('source','independent');self.settings.setdefault('trace_mode','hidden')
  if self.settings['active']:
   self.settings.update(active=False,next_at=None,message='Session mise en pause au redémarrage. Reprends-la explicitement.');self.t.save()
 def public(self):return dict(settings=self.settings,catalogue=[dict(id=x[0],title=x[1]) for x in procedural.FAMILIES],site_catalogue=SITE_CATALOGUE)
 def configure(self,d):
  minimum=int(d.get('minimum',5));maximum=int(d.get('maximum',10));cap=int(d.get('max_open',3));duration=int(d.get('ticket_minutes',30));mode=d.get('interval','fixed')
  if not(1<=minimum<=maximum<=120 and 1<=cap<=10 and 0<=duration<=1440 and mode in ('fixed','random')):raise ValueError('Intervalles de 1 à 120 min, plafond de 1 à 10 tickets, durée de 0 à 1440 min.')
  source=d.get('source',self.settings['source']);traces=d.get('trace_mode',self.settings['trace_mode'])
  if source not in ('independent','site') or traces not in ('hidden','technician'):raise ValueError('Source de tickets ou mode de traces invalide.')
  fault=d.get('fault_mode',self.settings['fault_mode'])
  if fault not in ('random','port_down','ip_wrong','mask_wrong','vlan_wrong'):raise ValueError('Famille de panne invalide.')
  if fault=='vlan_wrong' and traces!='technician':raise ValueError('Les incidents VLAN exigent explicitement les traces visibles.')
  live=d.get('live_services',self.settings['live_services'])
  if type(live) is not bool:raise ValueError('Option de services invalide.')
  self.settings.update(live_services=live,fault_mode=fault,source=source,trace_mode=traces,interval=mode,minimum=minimum,maximum=maximum,max_open=cap,ticket_minutes=duration)
  if self.settings['active']:self.schedule()
  self.t.save();return self.public()
 def schedule(self,at=None):
  at=time.time() if at is None else at
  minutes=self.settings['minimum'] if self.settings['interval']=='fixed' else random.uniform(self.settings['minimum'],self.settings['maximum'])
  self.settings['next_at']=at+minutes*60
 def control(self,active):
  if active and self.settings['source']=='site' and not self.t.state['site']:raise ValueError('Enregistre le site avant de démarrer ses arrivées.')
  self.settings.update(active=active,message='Session active.' if active else 'Arrivées en pause.')
  if active:self.schedule()
  else:self.settings['next_at']=None
  self.t.save();return self.public()
 def create(self,scenario=None):
  opened=[t for t in self.t.state['tickets'] if t['status']!='clos']
  if len(opened)>=self.settings['max_open']:raise ValueError('Plafond de tickets ouverts atteint.')
  if self.settings['source']=='site':return self.create_site(scenario,opened)
  seed=random.SystemRandom().randrange(10**9)
  plan=procedural.choose(seed,scenario,self.t.state['tickets'],opened)
  fid=plan['cause'];_,_,complaint,severity=next(x for x in CATALOGUE if x[0]==fid)
  title=plan['title']
  # La plainte doit correspondre à la portée réelle de chaque mutation.
  target=plan['target_employee'];target_name='PC-ALICE' if target==1 else 'PC-BOB' if target==2 else f'PC-CPT-{target:02d}'
  if plan['family']=='lease':complaint=target_name+' ne reçoit pas de bail DHCP ; '+('PC-BOB' if target==1 else 'PC-ALICE')+' en statique reste fonctionnel.'
  if plan['family']=='workstation':
   import re
   complaint=re.sub(r'PC-ALICE|PC-BOB',lambda m:target_name if m.group()=='PC-ALICE' else ('PC-BOB' if target==1 else 'PC-ALICE'),complaint)
  site=plan['site_code'];networks=private_networks(seed,plan['address_family'])
  names=organization.mapping(('R1','PC-ALICE','PC-BOB','SRV-INFRA','SRV-WEB','PC-NEW',target_name),site)
  complaint=organization.replace(complaint,names)
  job=self.g.start(dict(mode='atelier' if plan['family']=='new_employee' else 'depannage',scenario=fid,level=5,count=1,seed=seed,ticket_title=title,address_family=plan['address_family'],site_code=site,business_names=True,employee_count=plan['employee_count'],has_it=plan['has_it'],target_employee=target,employee_layout=plan['employee_layout']))
  ident='INC-'+str(1001+len(self.t.state['tickets']))
  t=dict(id=ident,kind='service',service_scenario=fid,procedural=plan,job_id=job['id'],title=title,description=f"Agence {site} — {plan['requester']} signale : "+complaint+f" Réseau employés : {networks['employees']} ; {plan['employee_count']} postes utilisateurs {'avec un poste IT dédié' if plan['has_it'] else 'sans poste IT dédié ; intervention par un prestataire externe'}. Réalise l’intervention demandée dans le réseau dédié à ce ticket. Conserve les autres services. Consulte la feuille du ticket pour les appareils, adresses et tests attendus.",severity=severity,status='nouveau',created=time.strftime('%Y-%m-%d %H:%M:%S'),checks=[],complete=False,notes='',manual_ssid=False,validation='manual',timer=timers.configure(self.settings['ticket_minutes'],'training'))
  self.t.state['tickets'].append(t);self.t.event(ident+' : incident reçu, réseau dédié en préparation.');return self.t.public()
 def create_site(self,scenario,opened):
  if scenario not in (None,'','pc','wifi','incident','site:http','site:dns','site:dhcp'):raise ValueError('Choisis une intervention du catalogue du site.')
  snapshot=self.t.engine.snapshot();self.t.guard(snapshot)
  choices=site_choices(snapshot,opened)
  names={d['name']:d for d in snapshot['devices']}
  if self.settings['live_services'] and not any(t['kind']!='service' for t in opened):
   for c in self.t.state['site'].get('service_capabilities',[]):
    if c.get('supported') and c.get('enabled') is True and c['device'] in names and names[c['device']].get('serial')==c['serial']:choices.append(('site:'+c['service'],c['device']))
  if self.settings['fault_mode'] not in ('random','vlan_wrong'):choices=[x for x in choices if x[0]!='incident' or self.settings['fault_mode'] in live_faults.choices(names[x[1]])]
  if scenario:choices=[x for x in choices if x[0]==scenario]
  if not choices:raise ValueError('Aucune intervention compatible : termine les tickets du site ou libère un port pour un nouveau poste.')
  seed=random.SystemRandom().randrange(10**9);rng=random.Random(seed)
  recent=[(t['kind'],t.get('name') if t['kind']=='incident' else None) for t in self.t.state['tickets'][-6:] if t['kind']!='service']
  fresh=[x for x in choices if x not in recent]
  kind,target=rng.choice(fresh or choices)
  before=len(self.t.state['tickets'])
  if kind.startswith('site:'):site_services.create(self.t,kind.split(':')[1],target)
  else:self.t.new(kind,self.settings['trace_mode'],target,self.settings['fault_mode'])
  ticket=self.t.state['tickets'][before]
  ticket['arrival']=dict(source='site',seed=seed,target=target,version=1)
  ticket['timer']=timers.configure(self.settings['ticket_minutes'],'training')
  self.t.event(ticket['id']+' : intervention reçue sur le site persistant.')
  return self.t.public()
 def tick(self,at=None):
  at=time.time() if at is None else at
  if not self.settings['active'] or at<self.settings['next_at']:return
  try:self.create();self.settings['message']='Dernier ticket reçu.';self.schedule(at)
  except Exception as e:self.settings.update(message='Arrivée différée : '+str(e),next_at=at+15)
  self.t.save()
