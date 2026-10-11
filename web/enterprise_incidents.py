"""Incidents simultanés : mutation d'abord, signalement ensuite, contrôles par cible."""
import copy
import hashlib
import random
import time
import client_workspaces as clients
import enterprise_staff
import company_registry
import enterprise_dialogue
import desktop_services as ds
import files_adapter
import timers
import dns_adapter
import sim_peripherals as hardware
from peripheral_incidents import CAUSES as PERIPHERAL_CAUSES

CATALOGUE=(('printing','queue_paused'),('printing','spooler_stopped'),('printing','offline_mode'),
           ('endpoint','mapped_drive_wrong'),('endpoint','documents_missing'),('ad','account_disabled'),
           ('ftp','service_stopped'),('dns','resolver_wrong'))+tuple(('peripherals',kind+':'+cause) for kind,cause in PERIPHERAL_CAUSES)
def view(s,serial):
    return clients.project(s,serial)
def receive(tickets,target='random',minutes=30,client_serial='random',engine='varied',discovery_delay=0):
    c=tickets.controller;s=c.workspace.state
    if type(minutes) is not int or not 0<=minutes<=1440:raise ValueError('Durée invalide.')
    if type(discovery_delay) is not int or not 0<=discovery_delay<=300:raise ValueError('Délai de découverte invalide.')
    clients.sync_primary(s)
    opened=[t for t in tickets.state['tickets'] if t.get('live_incident') and t['status']!='clos']
    opened += [r['ticket'] for r in s.get('live_incidents',{}).values() if r.get('lifecycle')=='awaiting_activity']
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
    if engine=='apps':options=[p for p in options if p[0] in ('printing','endpoint','ftp','peripherals')]
    elif engine=='mixed':options=[p for p in options if p[0] in ('ad','endpoint','dns')]
    if any(t.get('live_family')=='ftp' for t in opened):options=[p for p in options if p[0]!='ftp']
    ftp_users,ftp_known=enterprise_staff.service_users(s,'ftp')
    if ftp_known and not any(candidate in ftp_users for candidate in candidates):
        if target=='ftp':raise ValueError('Aucun poste disponible ne dépend du dépôt FTP pour son activité métier.')
        options=[p for p in options if p[0]!='ftp']
    if previous and target=='random':options=[p for p in options if p[0]!=previous.get('live_family')] or options
    if not options:raise ValueError('Cette famille est indisponible ou un incident partagé est déjà ouvert.')
    family=rng.choice(sorted({pair[0] for pair in options}))
    family,cause=rng.choice([pair for pair in options if pair[0]==family]);ident='INC-LIVE-'+str(index).zfill(5);created=time.time()
    if family=='ftp' and ftp_known:
        eligible=[candidate for candidate in candidates if candidate in ftp_users]
        if client_serial=='random' and previous:eligible=[candidate for candidate in eligible if candidate!=previous['target_serial']] or eligible
        serial=rng.choice(eligible)
    affected=ftp_users if family=='ftp' and ftp_known else [serial]
    departments=sorted({person['department'] for person in s.get('staff',[]) if person.get('department') and any(s['client_workspaces'][item]['requester']==person.get('display_name') for item in affected)})
    profile=s['client_workspaces'][serial]
    wording={'printing':('Impression bloquée','Je ne peux plus imprimer les documents nécessaires à mon activité.'),
             'endpoint':('Dossiers de travail inaccessibles','Je ne peux plus ouvrir mes dossiers depuis ce poste.'),
             'ad':('Compte utilisateur indisponible','Mon compte est refusé et je ne peux plus accéder à mes outils.'),
             'dns':('Nom du service documentaire introuvable','Je ne retrouve plus mes dossiers avec leur adresse habituelle.'),
             'ftp':('Dépôt documentaire indisponible','Notre équipe ne peut plus se connecter au dépôt FTP.')}
    if family=='peripherals':
        kind=cause.split(':')[0]
        title=hardware.KINDS[kind]+' externe inutilisable'
        complaint={'monitor':'Mon écran externe n’affiche plus mon poste.','keyboard':'Mon clavier externe ne me permet plus de saisir du texte.','mouse':'Ma souris externe ne répond plus.'}[kind]
    else:title,complaint=wording[family]
    if family=='endpoint':
        if cause=='mapped_drive_wrong':
            title='Lecteur réseau Documents inaccessible'
            complaint='Le lecteur réseau Documents de mon poste ne donne plus accès au dossier partagé. Mes fichiers locaux restent accessibles.'
        else:
            title='Application Documents absente du poste'
            complaint='Je ne trouve plus l’application Documents sur mon poste pour ouvrir le partage. Mes fichiers locaux restent accessibles.'
    impact=dict(affected_serials=affected,affected_count=len(affected),work_status='blocked' if family in ('ad','endpoint','dns','peripherals') else 'degraded',
                activity=next((p['activity'] for p in s.get('staff',[]) if p['display_name']==profile['requester']),'Activité du poste'),
                scope='service_users' if family=='ftp' and ftp_known else 'workstation',departments=departments,
                evidence='business_dependencies' if family=='ftp' and ftp_known else 'reported_workstation')
    ticket=dict(id=ident,kind='workspace',name=profile['device']['name'],target_serial=serial,requester=profile['requester'],
        title=title,description=profile['requester']+' : « '+complaint+' » Poste : '+profile['device']['name']+'.',
        status='nouveau',stage='prepared',workspace_goal='live',live_incident=True,live_family=family,impact=impact,
        severity='critique' if len(affected)>1 else 'elevee' if impact['work_status']=='blocked' else 'moderee',
        created=time.strftime('%Y-%m-%d %H:%M:%S'),checks=[],complete=False,notes='',dialogue=[],timer=timers.configure(minutes,'training'))
    ticket['request_context']=dict(requester=profile['requester'],station=profile['device']['name'],serial=serial,company=s['company'],complaint=complaint,urgency_label='Activité bloquée' if impact['work_status']=='blocked' else 'Activité perturbée',priority_reason=impact['activity'])
    ticket['dialogue_questions']=enterprise_dialogue.questions(family)
    with c.client_scope(serial):
        current=c.workspace.state
        if family=='peripherals':
            hardware.ensure(current,[dict(serial=serial,remote_supported=True)])
            if not all(check['available'] for check in hardware.evaluate(current['peripherals'],serial).values()):
                raise ValueError('Rétablis les accessoires locaux du poste avant une nouvelle panne matérielle.')
            kind,fault=cause.split(':')
            item=next(i for i in current['peripherals']['items'].values() if i['station_serial']==serial and i['kind']==kind)
            if fault=='absent':item['station_serial']=None
            elif fault=='input':item['input']='DisplayPort'
            else:item['connected' if fault=='connection' else fault]=False
            current['peripherals']['revision']+=1
        elif family=='printing':
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
        applied=time.time()
        if not discovery_delay:timers.autostart(ticket['timer'])
        ticket['created']=time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(applied))
        ticket['incident_context']=dict(occurred_at=applied,applied_at=applied,reported_at=applied,
                                       resource_kind=family,resource=('Application Documents locale' if cause=='documents_missing' else 'Documents (partage réseau)') if family=='endpoint' else family)
        current.setdefault('live_incidents',{})[ident]=dict(id=ident,target_serial=serial,family=family,
            cause=cause,created=created,applied_at=applied,reported_at=applied,
            lifecycle='awaiting_activity' if discovery_delay else 'reported',
            discovery_due=applied+discovery_delay,activity=dict(label=impact['activity'],status='pending' if discovery_delay else 'failed'),ticket=copy.deepcopy(ticket))
        if discovery_delay:
            current['live_incidents'][ident]['reported_at']=None
            ticket['incident_context']['reported_at']=None
            current['live_incidents'][ident]['ticket']=copy.deepcopy(ticket)
        report=enterprise_dialogue.snapshot(current,ticket)
        if not discovery_delay:report['attempts'].append(enterprise_dialogue.attempt_description(report,applied,'failed'))
        current['live_incidents'][ident]['client_report']=report
        current['live_incident_count']=index
        c.workspace.save()
    s=c.workspace.state
    if discovery_delay:
        tickets.event(ident+' : événement appliqué ; prochaine activité programmée.')
        return tickets.public()
    tickets.state['tickets'].append(ticket)
    company_registry.ensure(s);company_registry.link_tickets(s,tickets.state['tickets'])
    s['live_incidents'][ident]['ticket']=copy.deepcopy(ticket);c.workspace.save()
    tickets.event(ident+' : panne appliquée, puis signalement reçu.');return tickets.public()

def recover(tickets,s):
    known={t['id'] for t in tickets.state['tickets']}
    for record in s.get('live_incidents',{}).values():
        if record.get('lifecycle') in ('awaiting_activity','resolved_before_report'):continue
        record['ticket'].setdefault('dialogue_questions',enterprise_dialogue.questions(record['family']))
        if record['id'] not in known and record.get('ticket'):tickets.state['tickets'].append(copy.deepcopy(record['ticket']))
        ticket=next((t for t in tickets.state['tickets'] if t['id']==record['id']),None)
        if not ticket or record.get('family')!='ftp' or ticket.get('status')=='clos' or ticket.get('impact',{}).get('evidence'):continue
        affected,registered=enterprise_staff.service_users(s,'ftp')
        if not registered:affected=[ticket['target_serial']]
        departments=sorted({p['department'] for p in s.get('staff',[]) if p.get('department') and any(s['client_workspaces'][serial]['requester']==p.get('display_name') for serial in affected)})
        ticket.setdefault('impact',{}).update(affected_serials=affected,affected_count=len(affected),departments=departments,
            scope='service_users' if registered else 'workstation',evidence='business_dependencies' if registered else 'reported_workstation')
        record['ticket']['impact']=copy.deepcopy(ticket['impact'])

def checks(s,t,at):
    record=s.get('live_incidents',{}).get(t['id'])
    if not record or record['target_serial']!=t['target_serial']:raise ValueError('Incident absent ou cible remplacée.')
    if record['family']=='peripherals':
        model=s.get('peripherals')
        if not model or model['environment_id']!=s.get('environment_id','legacy'):
            return [dict(label='Équipement local du poste',status='inconnu',detail='Équipement non disponible pour cet environnement.')]
        return [dict(label=hardware.KINDS[kind]+' externe opérationnel',status='valide' if check['available'] else 'non satisfait',detail='État matériel simulé du poste identifié ; aucun contrôle réseau requis.') for kind,check in hardware.evaluate(model,t['target_serial']).items()]
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
    return [dict(id=r['id'],target_serial=r['target_serial'],created=r['created'],family=r['family']) for r in incidents.values() if r.get('lifecycle') not in ('awaiting_activity','resolved_before_report')]

def dialogue(s,ident,question):
    record=s.get('live_incidents',{}).get(ident)
    if not record:raise ValueError('Incident inconnu.')
    return enterprise_dialogue.answer(s,record,question,time.time(),checks)


def work_status(s, include_pending=False):
    result=[]
    for serial,p in s.get('client_workspaces',{}).items():
        incidents=[]
        for r in s.get('live_incidents',{}).values():
            t=r['ticket']
            if not include_pending and r.get('lifecycle')=='awaiting_activity':continue
            if t['status']=='clos' or serial not in t['impact']['affected_serials']:continue
            family=r['family'];primary=serial==clients.primary_serial(s)
            endpoint=s['desktop_services']['endpoint'] if primary else p['endpoint']
            printing=s['desktop_services']['printing'] if primary else p['printing']
            dns=s['dns_service']['clients']['client'] if primary else p['dns_client']
            user=s['directory_user_id'] if primary else p['user_id']
            if family=='peripherals':still=not all(check['available'] for check in hardware.evaluate(s['peripherals'],serial).values())
            elif family=='ad':still=not s['directory']['users'][user]['enabled']
            elif family=='ftp':still=not s['desktop_services']['ftp']['service_running']
            elif family=='dns':still=dns['dns_server_ip']!=s['devices']['server']['ip']
            elif family=='printing':still=not printing['spooler_running'] or printing['queues']['office']['paused'] or printing['queues']['office']['use_offline']
            else:still='documents' not in endpoint['applications'] or endpoint['mapped_drive']['path'].casefold()!=('\\\\'+s['devices']['server']['name']+'\\Documents').casefold()
            if still:incidents.append(t)
        person=next((x for x in s.get('staff',[]) if x['display_name']==p['requester']),{})
        status='blocked' if any(t['impact']['work_status']=='blocked' for t in incidents) else 'degraded' if incidents else 'available'
        result.append(dict(serial=serial,name=p['requester'],department=person.get('department'),activity=person.get('activity'),status=status,tickets=[t['id'] for t in incidents]))
    return result


def discover(tickets, at=None):
    """Tentatives d'activité locales : aucun ping, aucune nouvelle mutation."""
    at=time.time() if at is None else at
    c=getattr(tickets,'controller',None)
    if not c:return 0
    s=c.workspace.state
    if not s or s.get('environment_id')!=(tickets.state.get('site') or {}).get('environment_id'):return 0
    due=[r for r in s.get('live_incidents',{}).values() if r.get('lifecycle')=='awaiting_activity' and at>=r['discovery_due']]
    if not due:return 0
    statuses={row['serial']:row for row in work_status(s,include_pending=True)}
    count=0
    for record in due:
        ident=record['id'];ticket=record['ticket'];record['activity']['attempted_at']=at
        affected=statuses.get(record['target_serial'],{}).get('tickets',[])
        if ident not in affected:
            record['lifecycle']='resolved_before_report';record['activity']['status']='passed';ticket['status']='clos'
            continue
        record['lifecycle']='reported';record['reported_at']=at;record['activity']['status']='failed'
        knowledge=record.setdefault('client_report',enterprise_dialogue.snapshot(view(s,record['target_serial']),ticket))
        knowledge['attempts'].append(enterprise_dialogue.attempt_description(knowledge,at,'failed'))
        ticket['created']=time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(at))
        ticket['incident_context']['reported_at']=at
        if ticket['timer'].get('limit') and not ticket['timer']['started']:timers.operate(ticket['timer'],'start',at)
        count+=1
    # Save the revealed report before exposing it to the independent ticket store.
    c.workspace.save()
    recover(tickets,s)
    company_registry.ensure(s);company_registry.link_tickets(s,tickets.state['tickets'])
    tickets.event('Activités des employés : '+str(count)+' nouveau(x) signalement(s).')
    return count
