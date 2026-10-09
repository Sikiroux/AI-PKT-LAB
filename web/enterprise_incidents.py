"""Incidents simultanés : mutation d'abord, signalement ensuite, contrôles par cible."""
import copy
import hashlib
import random
import time
import client_workspaces as clients
import company_registry
import desktop_services as ds
import files_adapter
import timers
import dns_adapter

CATALOGUE=(('printing','queue_paused'),('printing','spooler_stopped'),('printing','offline_mode'),
           ('endpoint','mapped_drive_wrong'),('endpoint','documents_missing'),('ad','account_disabled'),
           ('ftp','service_stopped'),('dns','resolver_wrong'))
def view(s,serial):
    return clients.project(s,serial)
def receive(tickets,target='random',minutes=30,client_serial='random',engine='varied'):
    c=tickets.controller;s=c.workspace.state
    if type(minutes) is not int or not 0<=minutes<=1440:raise ValueError('Durée invalide.')
    clients.sync_primary(s)
    opened=[t for t in tickets.state['tickets'] if t.get('live_incident') and t['status']!='clos']
    legacy=[t for t in tickets.state['tickets'] if t['kind']=='workspace' and not t.get('live_incident') and t['status']!='clos' and t.get('stage')!='queued']
    shared=next((t for t in opened if t.get('live_family')=='ftp'),None)
    if target=='ftp' and shared:
        shared.setdefault('followups',[]).append(dict(id=len(shared.get('followups',[]))+1,date=time.strftime('%Y-%m-%d %H:%M:%S'),author='Signalement entreprise',kind='followup',text='Nouveau signalement rattaché à la panne FTP déjà ouverte.'))
        s['live_incidents'][shared['id']]['ticket']=copy.deepcopy(shared)
        c.workspace.save();tickets.event(shared['id']+' : signalement regroupé.');return tickets.public()
    if legacy:raise ValueError('Termine le scénario historique avant les incidents simultanés.')
    index=s.get('live_incident_count',0)+1
    seed=hashlib.sha256((s['seed']+':enterprise-incidents:v1:'+str(index)).encode()).hexdigest()
    rng=random.Random(seed)
    previous=next((t for t in reversed(tickets.state['tickets']) if t.get('live_incident')),None)
    busy={t['target_serial'] for t in opened}
    candidates=[serial for serial in sorted(s['client_workspaces']) if serial not in busy]
    if client_serial!='random':candidates=[serial for serial in candidates if serial==client_serial]
    elif previous:
        candidates=[serial for serial in candidates if serial!=previous['target_serial']] or candidates
    if not candidates:raise ValueError('Tous les postes sélectionnables ont déjà une intervention ouverte.')
    serial=rng.choice(candidates)
    options=[pair for pair in CATALOGUE if target=='random' or pair[0]==target or target=='files' and pair[0]=='endpoint']
    if engine=='apps':options=[p for p in options if p[0] in ('printing','endpoint','ftp')]
    elif engine=='mixed':options=[p for p in options if p[0] in ('ad','endpoint','dns')]
    if any(t.get('live_family')=='ftp' for t in opened):options=[p for p in options if p[0]!='ftp']
    if previous and target=='random':options=[p for p in options if p[0]!=previous.get('live_family')] or options
    if not options:raise ValueError('Cette famille est indisponible ou un incident partagé est déjà ouvert.')
    family,cause=rng.choice(options);ident='INC-LIVE-'+str(index).zfill(5);created=time.time()
    affected=list(s['client_workspaces']) if family=='ftp' else [serial]
    with c.client_scope(serial):
        current=c.workspace.state
        if family=='printing':
            printing=current['desktop_services']['printing']
            if cause=='queue_paused':printing['queues']['office']['paused']=True
            elif cause=='offline_mode':printing['queues']['office']['use_offline']=True
            else:printing['spooler_running']=False
        elif family=='endpoint':
            endpoint=current['desktop_services']['endpoint']
            if cause=='mapped_drive_wrong':endpoint['mapped_drive']['path']='\\\\'+current['devices']['server']['name']+'\\AncienDossier'
            elif 'documents' in endpoint['applications']:endpoint['applications'].remove('documents')
        elif family=='ad':
            current['directory']['users'][current['directory_user_id']]['enabled']=False
            current['directory_auth']=None
        elif family=='dns':
            current['dns_service']['clients']['client']['dns_server_ip']='192.0.2.254'
            current['dns_service']['cache']['client']={}
        else:
            current['desktop_services']['ftp']['service_running']=False
            current['desktop_services']['ftp']['sessions']={}
        c.workspace.save()
    s=c.workspace.state
    profile=s['client_workspaces'][serial]
    wording={'printing':('Impression bloquée','Je ne peux plus imprimer les documents nécessaires à mon activité.'),
             'endpoint':('Dossiers de travail inaccessibles','Je ne peux plus ouvrir mes dossiers depuis ce poste.'),
             'ad':('Compte utilisateur indisponible','Mon compte est refusé et je ne peux plus accéder à mes outils.'),
             'dns':('Nom du service documentaire introuvable','Je ne retrouve plus mes dossiers avec leur adresse habituelle.'),
             'ftp':('Dépôt documentaire indisponible','Notre équipe ne peut plus se connecter au dépôt FTP.')}
    title,complaint=wording[family]
    impact=dict(affected_serials=affected,affected_count=len(affected),work_status='blocked' if family in ('ad','endpoint','dns') else 'degraded',
                activity=next((p['activity'] for p in s.get('staff',[]) if p['display_name']==profile['requester']),'Activité du poste'),
                scope='company' if family=='ftp' else 'workstation')
    ticket=dict(id=ident,kind='workspace',name=profile['device']['name'],target_serial=serial,requester=profile['requester'],
        title=title,description=profile['requester']+' : « '+complaint+' » Poste : '+profile['device']['name']+'.',
        status='nouveau',stage='prepared',workspace_goal='live',live_incident=True,live_family=family,impact=impact,
        severity='critique' if len(affected)>1 else 'elevee' if impact['work_status']=='blocked' else 'moderee',
        created=time.strftime('%Y-%m-%d %H:%M:%S'),checks=[],complete=False,notes='',dialogue=[],timer=timers.configure(minutes,'training'))
    ticket['request_context']=dict(requester=profile['requester'],station=profile['device']['name'],serial=serial,company=s['company'],complaint=complaint,urgency_label='Activité bloquée' if impact['work_status']=='blocked' else 'Activité perturbée',priority_reason=impact['activity'])
    timers.autostart(ticket['timer'])
    s.setdefault('live_incidents',{})[ident]=dict(id=ident,target_serial=serial,family=family,cause=cause,created=created,ticket=copy.deepcopy(ticket))
    s['live_incident_count']=index;c.workspace.save()
    tickets.state['tickets'].append(ticket)
    company_registry.ensure(s);company_registry.link_tickets(s,tickets.state['tickets'])
    s['live_incidents'][ident]['ticket']=copy.deepcopy(ticket);c.workspace.save()
    tickets.event(ident+' : panne appliquée, puis signalement reçu.');return tickets.public()

def recover(tickets,s):
    known={t['id'] for t in tickets.state['tickets']}
    for record in s.get('live_incidents',{}).values():
        if record['id'] not in known and record.get('ticket'):tickets.state['tickets'].append(copy.deepcopy(record['ticket']))

def checks(s,t,at):
    record=s.get('live_incidents',{}).get(t['id'])
    if not record or record['target_serial']!=t['target_serial']:raise ValueError('Incident absent ou cible remplacée.')
    v=view(s,t['target_serial']);family=record['family']
    if family=='printing':
        result=ds.evaluate_print(v,'office',at);ok=result['allowed'];unknown=result['status']=='unknown'
    elif family=='endpoint':
        expected='\\\\'+v['devices']['server']['name']+'\\Documents'
        result=files_adapter.access(v,'read',at)
        ok=result['allowed'] and 'documents' in v['desktop_services']['endpoint']['applications'] and v['desktop_services']['endpoint']['mapped_drive']['path'].casefold()==expected.casefold()
        unknown=result['status']=='unknown'
    elif family=='ad':
        from workspace_model import evaluate
        result=evaluate(v,'remote',at);ok=result['allowed'] and v['directory']['users'][v['directory_user_id']]['enabled'];unknown=result['status']=='unknown'
    elif family=='dns':
        observation,result=dns_adapter.resolution(v,at)
        ok=observation['status']=='resolved' and observation['resolved_ip']==v['devices']['server']['ip'];unknown=observation['status']=='unknown'
    else:
        result=ds.ftp_check(v,'login','client',at);ok=result['allowed'];unknown=result['status']=='unknown'
    return [dict(label='Fonction concernée disponible sur le poste identifié',status='valide' if ok else 'inconnu' if unknown else 'non satisfait',
                 detail='Contrôle de la fonction simulée et preuve réseau Packet Tracer récente ; aucune réponse réseau inventée.')]

def public(s):
    incidents=s.get('live_incidents',{})
    return [dict(id=r['id'],target_serial=r['target_serial'],created=r['created'],family=r['family']) for r in incidents.values()]

def dialogue(s,ident,question):
    from client_dialogue import QUESTIONS
    if question not in QUESTIONS:raise ValueError('Question inconnue.')
    record=s.get('live_incidents',{}).get(ident)
    if not record:raise ValueError('Incident inconnu.')
    v=view(s,record['target_serial']);ticket=record['ticket'];at=time.time()
    if question=='scope':answer='Je travaille sur '+v['devices']['client']['name']+'. '+ticket['impact']['activity']+'.'
    elif question=='when':answer='Le problème a commencé avant mon signalement.'
    elif question=='login':answer='Le compte est refusé.' if not v['directory']['users'][v['directory_user_id']]['enabled'] else 'Mon compte est actif ; cela ne confirme pas mon accès aux fichiers.'
    elif question=='network':
        observation=v.get('observation') or {}
        status=observation.get('status','unknown') if observation.get('valid_until',0)>at else 'unknown'
        answer={'passed':'Le dernier contrôle réseau est positif.','failed':'Le dernier contrôle réseau a échoué.'}.get(status,'Je ne dispose pas encore d’un contrôle réseau récent.')
    elif question=='retest':answer='La fonction demandée est disponible au dernier contrôle.' if all(r['status']=='valide' for r in checks(s,ticket,at)) else 'Le contrôle ne confirme pas encore que je peux reprendre cette activité.'
    else:answer='Je ne peux pas confirmer cela sans effectuer le test sur mon poste.'
    row=dict(at=at,question=QUESTIONS[question],answer=answer,speaker=v['requester'])
    ticket.setdefault('dialogue',[]).append(row);return row

def work_status(s):
    result=[]
    for serial,p in s.get('client_workspaces',{}).items():
        incidents=[]
        for r in s.get('live_incidents',{}).values():
            t=r['ticket']
            if t['status']=='clos' or serial not in t['impact']['affected_serials']:continue
            family=r['family'];primary=serial==clients.primary_serial(s)
            endpoint=s['desktop_services']['endpoint'] if primary else p['endpoint']
            printing=s['desktop_services']['printing'] if primary else p['printing']
            dns=s['dns_service']['clients']['client'] if primary else p['dns_client']
            user=s['directory_user_id'] if primary else p['user_id']
            if family=='ad':still=not s['directory']['users'][user]['enabled']
            elif family=='ftp':still=not s['desktop_services']['ftp']['service_running']
            elif family=='dns':still=dns['dns_server_ip']!=s['devices']['server']['ip']
            elif family=='printing':still=not printing['spooler_running'] or printing['queues']['office']['paused'] or printing['queues']['office']['use_offline']
            else:still='documents' not in endpoint['applications'] or endpoint['mapped_drive']['path'].casefold()!=('\\\\'+s['devices']['server']['name']+'\\Documents').casefold()
            if still:incidents.append(t)
        person=next((x for x in s.get('staff',[]) if x['display_name']==p['requester']),{})
        status='blocked' if any(t['impact']['work_status']=='blocked' for t in incidents) else 'degraded' if incidents else 'available'
        result.append(dict(serial=serial,name=p['requester'],department=person.get('department'),activity=person.get('activity'),status=status,tickets=[t['id'] for t in incidents]))
    return result
