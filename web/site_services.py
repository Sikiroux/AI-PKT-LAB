"""Tickets de services : contrôles de configuration et preuve fonctionnelle manuelle."""
import time
import service_api

def scan(tickets):
 snapshot=tickets.engine.snapshot();tickets.guard(snapshot);items=[]
 for device in snapshot['devices']:
  if device.get('model')!='Server-PT' or not device.get('serial'):continue
  for kind in service_api.SERVICES:
   adapter=service_api.probe(tickets.engine,device['name'],device['serial'],kind)
   items.append(dict(device=device['name'],serial=device['serial'],service=kind,supported=adapter['supported'],enabled=adapter.get('enabled')))
 tickets.state['site']['service_capabilities']=items;tickets.event('Capacités des services observées ; API absente conservée comme non prise en charge.')
 return tickets.public()

def create(tickets,kind,name):
 if kind not in service_api.SERVICES:raise ValueError('Service inconnu.')
 if any(t['status']!='clos' and t['kind']!='service' for t in tickets.state['tickets']):raise ValueError('Termine les interventions du site avant une panne de service partagée.')
 snapshot=tickets.engine.snapshot();tickets.guard(snapshot)
 matches=[d for d in snapshot['devices'] if d['name']==name and d.get('model')=='Server-PT']
 if len(matches)!=1:raise ValueError('Serveur absent ou ambigu.')
 server=matches[0];adapter=service_api.probe(tickets.engine,name,server['serial'],kind)
 if not adapter['supported'] or adapter['enabled'] is not True:raise ValueError('API de ce service non confirmée ou service déjà arrêté ; aucune injection effectuée.')
 spec=service_api.SERVICES[kind]
 ticket=dict(id='INC-'+str(1001+len(tickets.state['tickets'])),kind='site_service',name=name,service=kind,title=spec['title'],description='Les utilisateurs signalent un problème de '+kind.upper()+' sur '+name+'. Diagnostique et rétablis le service en préservant les autres services. Test attendu : '+spec['test'],severity='elevee',status='nouveau',created=time.strftime('%Y-%m-%d %H:%M:%S'),baseline=snapshot,checks=[],complete=False,configuration_complete=False,notes='',manual_ssid=False,validation='partielle : configuration automatique, fonctionnement déclaré manuellement',injection=dict(state='pending',adapter=adapter,before_enabled=True))
 others=[]
 for other in service_api.SERVICES:
  if other==kind:continue
  observed=service_api.probe(tickets.engine,name,server['serial'],other)
  if observed['supported']:others.append(observed)
 ticket['injection']['others']=others
 tickets.state['tickets'].append(ticket);tickets.save()
 try:
  tickets.guard(tickets.engine.snapshot());service_api.write(tickets.engine,adapter,False)
  ticket['injection']['state']='applied';tickets.event(ticket['id']+' : état du service modifié via API ; symptôme client à observer dans Packet Tracer.')
 except Exception:
  ticket['injection']['state']='uncertain';ticket['status']='a_controler';tickets.save();raise RuntimeError('Modification incertaine : le ticket est conservé pour restauration et contrôle.')
 return tickets.public()

def verify(tickets,ticket):
 snapshot=tickets.engine.snapshot();tickets.guard(snapshot);adapter=ticket['injection']['adapter'];checks=[]
 server=next((d for d in snapshot['devices'] if d['name']==adapter['device'] and d.get('serial')==adapter['serial']),None)
 checks.append(dict(label='Identité du serveur conservée',status='valide' if server else 'non satisfait',detail='Comparaison du nom et du numéro de série.'))
 try:
  current=service_api.probe(tickets.engine,adapter['device'],adapter['serial'],ticket['service']) if server else dict(supported=False)
  valid=current.get('supported') and current.get('enabled') is ticket['injection']['before_enabled']
  checks.append(dict(label='État du service rétabli',status='valide' if valid else ('inconnu' if not current.get('supported') else 'non satisfait'),detail='Contrôle de configuration : ne prouve pas une requête HTTP, DNS ou un bail DHCP.'))
 except Exception:checks.append(dict(label='État du service rétabli',status='inconnu',detail='Lecture de configuration non confirmée.'))
 for other in ticket['injection'].get('others',[]):
  try:
   state=service_api.probe(tickets.engine,other['device'],other['serial'],other['service']);status='valide' if state.get('supported') and state.get('enabled') is other['enabled'] else ('inconnu' if not state.get('supported') else 'non satisfait')
  except Exception:status='inconnu'
  checks.append(dict(label='Autre service préservé : '+other['service'].upper(),status=status,detail='Comparaison de l’état lu avant et après, sans requête fonctionnelle.'))
 ticket['configuration_complete']=all(c['status']=='valide' for c in checks)
 checks.append(dict(label='Test fonctionnel du service depuis les clients',status='inconnu',detail=service_api.SERVICES[ticket['service']]['test']))
 ticket.update(checks=checks,complete=False,checked=time.strftime('%Y-%m-%d %H:%M:%S'));tickets.event(ticket['id']+' : contrôles de configuration effectués, test fonctionnel manuel requis.')
 return tickets.public()

def restore(tickets,ticket):
 tickets.guard(tickets.engine.snapshot());service_api.write(tickets.engine,ticket['injection']['adapter'],ticket['injection']['before_enabled']);ticket['injection']['state']='restored';ticket['status']='en_cours';return verify(tickets,ticket)
