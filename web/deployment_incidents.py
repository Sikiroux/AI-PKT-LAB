"""Demandes de déploiement sur disque d’atelier, sans modifier le client PT."""
import copy
import sim_deployment as sim
import desktop_services as ds
from client_dialogue import QUESTIONS

PRESERVED=('devices','directory','file_service')

def baseline(s):
    result={k:copy.deepcopy(s.get(k)) for k in PRESERVED}
    result['desktop_services']={k:copy.deepcopy(v) for k,v in s['desktop_services'].items() if k!='deployment'}
    return result

def prepare(state,now,minutes):
    s=copy.deepcopy(state);ds.ensure(s)
    for key in ('desktop_incident','mixed_incident','directory_incident','file_incident','dns_incident'):s.pop(key,None)
    index=s.get('desktop_incident_count',0)+1
    old=s['desktop_services'].get('deployment',{})
    d=sim.generate(str(s['seed'])+':ticket-deployment:'+str(index),s['environment_id'])
    d['revision']=old.get('revision',-1)+1
    s['desktop_services']['deployment']=d
    r=d['requirements'];image=next(i['name'] for i in d['images'] if i['id']==r['image_id'])
    text=(f"Prépare le poste d’atelier {d['station']} pour une arrivée chez {s['company']}. "
          f"Image demandée : {image}. Région : {r['locale']}, clavier : {r['keyboard']}, compte local : {r['account']}. "
          "Depuis le bureau du technicien, ouvre Déploiement. Sauvegarde le disque virtuel, prépare ses partitions et termine l’installation simulée. "
          "Cette demande concerne le disque d’atelier uniquement : aucun nouveau PC Packet Tracer ne sera installé. Préserve les postes, fichiers et comptes de l’entreprise.")
    s.update(desktop_incident=dict(id='INC-APP-'+str(index).zfill(4),title='Préparer un poste · Atelier de déploiement',description=text,station=d['station'],goal='deployment',family='deployment',created=now,dialogue=[],timer_minutes=minutes,baseline=baseline(s)),desktop_incident_count=index,ticket=text,validated=False)
    return s

def checks(s):
    d=s['desktop_services'].get('deployment');i=s['desktop_incident'];b=i['baseline']
    success=bool(d and d['station']==i['station'] and sim.evaluate(d)['passed'])
    preserved=baseline(s)==b
    return [dict(label='Déploiement du disque d’atelier terminé',status='valide' if success else 'non satisfait',detail='Image, sauvegarde, partitions et premier démarrage simulés ; aucune installation réelle.'),dict(label='Environnement client préservé',status='valide' if preserved else 'non satisfait',detail='Postes, annuaire, fichiers et services comparés au début de la demande.')]

def dialogue(s,question,now):
    i=s['desktop_incident']
    if question=='scope':answer=i['description']
    elif question=='when':answer='C’est une demande de préparation pour une arrivée, pas une panne du poste client.'
    elif question=='retest':answer='La préparation demandée est terminée.' if checks(s)[0]['status']=='valide' else 'La préparation du disque d’atelier n’est pas encore conforme.'
    else:answer='Cette demande concerne le poste d’atelier indiqué dans le ticket. Le réseau et les accès du client doivent être préservés.'
    row=dict(at=now,question={'scope':'Configuration demandée','when':'Contexte de la demande','retest':'Préparation terminée ?'}.get(question,QUESTIONS[question]),answer=answer,speaker=s['requester']);i['dialogue'].append(row);i['dialogue']=i['dialogue'][-60:];return row
