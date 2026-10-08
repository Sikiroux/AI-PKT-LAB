"""Demandes poste, impression et FTP, symptômes sans révéler la cause privée."""
import copy
import hashlib
import random
import desktop_services as ds
import directory_adapter as ad
import files_adapter as fa

FAMILIES={'printing':('spooler_stopped','queue_paused','offline_mode','wrong_default','driver_invalid','wrong_port','paper_empty'),'ftp':('service_stopped','control_blocked','data_blocked','account_disabled','password_wrong','read_denied','write_denied','disk_full'),'endpoint':('install_ftp','mapped_drive_wrong','documents_missing')}
KEYS=('desktop_incident','mixed_incident','directory_incident','file_incident','dns_incident')

def prepare(s,now,target='random',minutes=30,generation_seed=None):
    if target not in ('random','deployment','workstation_setup','peripherals',*FAMILIES):raise ValueError('Famille d’application inconnue.')
    if any(s.get(k) for k in KEYS) and not s['validated']:raise ValueError('Termine et vérifie l’intervention active.')
    if type(minutes) is not int or not 0<=minutes<=1440:raise ValueError('Durée de 0 à 1440 minutes.')
    if target=='peripherals':
        import peripheral_incidents
        return peripheral_incidents.prepare(s,now,minutes,generation_seed=generation_seed)
    if target=='workstation_setup':
        import workstation_requests
        return workstation_requests.prepare(s,now,minutes)
    if target=='deployment':
        import deployment_incidents
        return deployment_incidents.prepare(s,now,minutes)
    s=copy.deepcopy(s);ds.ensure(s)
    for k in KEYS:s.pop(k,None)
    index=s.get('desktop_incident_count',0)+1;rng=random.Random(hashlib.sha256((str(generation_seed or s['seed'])+':apps:v1:'+str(1 if generation_seed else index)).encode()).hexdigest());family=rng.choice(list(FAMILIES)) if target=='random' else target;cause=rng.choice(FAMILIES[family]);d=s['desktop_services'];e=d['endpoint'];p=d['printing'];f=d['ftp'];uid=s['directory_user_id']
    # Préparer seulement les dépendances nécessaires au scénario, en gardant les autres comptes.
    e['applications']=list(ds.APPS);e['mapped_drive']['path']='\\\\'+s['devices']['server']['name']+'\\Documents'
    p.update(spooler_running=True,default_queue='office');p['queues']['office'].update(port_ip=s['devices'][p['printer']['device_role']]['ip'],driver_valid=True,paused=False,use_offline=False);p['printer'].update(enabled=True,paper_pages=max(20,p['printer']['paper_pages']))
    f.update(service_running=True,control_allowed=True,data_allowed=True,capacity_bytes=max(1048576,sum(len(c.encode()) for c in f['files'].values())+65536));f['sessions']={};f['accounts']['depot'].update(enabled=True,password_hash=ds.password_hash('Formation!2026'),read=True,write=True)
    file='Bordereau-'+s['site']+'.txt';upload='Rapport-'+s['site']+'.txt';content='Rapport d’intervention — '+s['company']+' — '+s['requester'];e['local_files'][file]='Bordereau de formation — '+s['company'];e['local_files'][upload]=content
    if family=='endpoint' and cause!='install_ftp':
        fs=s['file_service'];share=fs['shares'][s['documents_share_id']];fs.update(service_status='running',firewall_tcp445_allowed=True);share['enabled']=True;s['directory']['users'][uid].update(enabled=True,locked_until=None,must_change_password=False,password_expires_at=now+3600)
        gid=s['directory_resource']['allowed_group_ids']['read'][0]
        if uid not in s['directory']['groups'][gid]['member_user_ids']:s['directory']['groups'][gid]['member_user_ids'].append(uid)
        for layer in ('share_acl','folder_acl'):
            for action in ('list','read'):share[layer][action]['group_ids']=list(dict.fromkeys(share[layer][action]['group_ids']+[gid]))
    goal='print' if family=='printing' else 'upload' if family=='ftp' and cause in ('write_denied','disk_full') else 'download' if family=='ftp' else 'install' if cause=='install_ftp' else 'documents'
    targetfile='Notice.txt';f['files'].setdefault(targetfile,'Notice de formation — '+s['company'])
    baseline=dict(ftp_files={n:c for n,c in f['files'].items() if not(goal=='upload' and n==upload)},local_files={n:c for n,c in e['local_files'].items() if not(goal=='download' and n==targetfile)},other_users={k:copy.deepcopy(v) for k,v in s['directory']['users'].items() if k!=uid},other_rights={})
    import file_incidents
    baseline['shared_files']=copy.deepcopy(s['file_service']['files'])
    baseline['other_rights']={k:file_incidents.rights(s,k) for k in baseline['other_users']}
    if family=='printing':
        if cause=='spooler_stopped':p['spooler_running']=False
        elif cause=='queue_paused':p['queues']['office']['paused']=True
        elif cause=='offline_mode':p['queues']['office']['use_offline']=True
        elif cause=='wrong_default':p['default_queue']='pdf'
        elif cause=='driver_invalid':p['queues']['office']['driver_valid']=False
        elif cause=='wrong_port':p['queues']['office']['port_ip']='192.0.2.254'
        else:p['printer']['paper_pages']=0
    elif family=='ftp':
        if cause in ('service_stopped','control_blocked','data_blocked'):f[{'service_stopped':'service_running','control_blocked':'control_allowed','data_blocked':'data_allowed'}[cause]]=False
        elif cause=='account_disabled':f['accounts']['depot']['enabled']=False
        elif cause=='password_wrong':f['accounts']['depot']['password_hash']=ds.password_hash('AncienMotDePasse!')
        elif cause in ('read_denied','write_denied'):f['accounts']['depot']['read' if cause=='read_denied' else 'write']=False
        else:f['capacity_bytes']=sum(len(c.encode()) for c in f['files'].values())
        if goal=='download':e['local_files'].pop(targetfile,None)
        else:f['files'].pop(upload,None)
        if cause=='disk_full':f['capacity_bytes']=sum(len(c.encode()) for c in f['files'].values())
    else:
        if cause=='mapped_drive_wrong':e['mapped_drive']['path']='\\\\'+s['devices']['server']['name']+'\\AncienDossier'
        else:e['applications'].remove('ftp' if cause=='install_ftp' else 'documents')
    text=(f"{s['requester']} ne retrouve pas son impression de {file}. Imprime ce bordereau sur {p['queues']['office']['name']} après réparation, avec cette file choisie par défaut." if goal=='print' else f"{s['requester']} ne peut plus déposer {upload} dans le dépôt FTP {s['devices']['server']['name']} ({s['devices']['server']['ip']}). Transfère le contenu du fichier local, compte depot / Formation!2026." if goal=='upload' else f"{s['requester']} ne peut plus récupérer {targetfile} depuis le dépôt FTP {s['devices']['server']['name']} ({s['devices']['server']['ip']}). Télécharge-le sur le poste, compte depot / Formation!2026." if goal=='download' else f"Installer le client FTP sur {s['devices']['client']['name']}, puis vérifier la connexion depot / Formation!2026 au dépôt ({s['devices']['server']['ip']})." if goal=='install' else f"{s['requester']} ne peut plus ouvrir Documents depuis le lecteur Z: de {s['devices']['client']['name']}. Rétablis le lecteur et vérifie l’ouverture du document partagé. Chemin attendu : "+'\\\\'+s['devices']['server']['name']+'\\Documents')+' Préserve les autres fichiers et accès.'
    s.update(desktop_incident=dict(id='INC-APP-'+str(index).zfill(4),title={'printing':'Impression introuvable','ftp':'Transfert documentaire impossible','endpoint':'Intervention sur le poste'}[family],description=text,goal=goal,family=family,cause=cause,created=now,document=file,upload=upload,content=content,download=targetfile,baseline=baseline,dialogue=[],timer_minutes=minutes),desktop_incident_count=index,ticket=text,remote_session=False,validated=False)
    ad.invalidate(s);return s

def public(s):
    i=s.get('desktop_incident');return {k:copy.deepcopy(i[k]) for k in ('id','title','description','goal','created','dialogue','target_serial','target_name') if k in i} if i else None

def checks(s,now):
    import client_workspaces
    target=s['desktop_incident'].get('target_serial')
    if target and target!=s['devices']['client']['serial']:
        return checks(client_workspaces.project(s,target),now)
    if s['desktop_incident'].get('family')=='workstation_setup':
        import workstation_requests
        return workstation_requests.checks(s,now)
    if s['desktop_incident'].get('family')=='deployment':
        import deployment_incidents
        return deployment_incidents.checks(s)
    if s['desktop_incident'].get('family')=='peripherals':
        import peripheral_incidents
        return peripheral_incidents.checks(s)
    i=s['desktop_incident'];d=s['desktop_services'];f=d['ftp'];e=d['endpoint'];p=d['printing'];goal=i['goal'];unknown=False
    if goal=='print':
        r=ds.evaluate_print(s,'office',now);unknown=r['status']=='unknown'
        success=r['allowed'] and p['default_queue']=='office' and any(j['name']==i['document'] and j['queue_id']=='office' and j['status']=='printed' and j['created_at']>=i['created'] and j['content']==e['local_files'].get(i['document']) for j in p['jobs'])
    elif goal in ('upload','download','install'):
        r=ds.ftp_check(s,'upload' if goal=='upload' else 'download','client',now);unknown=r['status']=='unknown'
        success=r['allowed'] and (f['files'].get(i['upload'])==i['content'] if goal=='upload' else e['local_files'].get(i['download'])==f['files'].get(i['download']) and i['download'] in e['local_files'] if goal=='download' else 'ftp' in e['applications'])
    else:
        r=fa.access(s,'read',now);unknown=r['status']=='unknown';success=r['allowed'] and 'documents' in e['applications'] and drive_ok(s)
    import file_incidents
    b=i['baseline'];preserved=all(f['files'].get(n)==v for n,v in b['ftp_files'].items()) and all(e['local_files'].get(n)==v for n,v in b['local_files'].items()) and all(s['directory']['users'].get(k)==v and file_incidents.rights(s,k)==b['other_rights'][k] for k,v in b['other_users'].items())
    preserved=preserved and s['file_service']['files']==b['shared_files']
    return [dict(label='Résultat demandé observé',status='valide' if success else 'inconnu' if unknown else 'non satisfait',detail='Impression/transfert pédagogique et contrôle ICMP PT récent.'),dict(label='Autres fichiers et utilisateurs préservés',status='valide' if preserved else 'non satisfait',detail='Comparaison avec le début de cette intervention.')]

def drive_ok(s):
    drive=s['desktop_services']['endpoint']['mapped_drive'];return drive['path'].casefold()==('\\\\'+s['devices']['server']['name']+'\\Documents').casefold()


def dialogue(s, ident, question, now=None):
    """Réponses observables, sans révéler la mutation privée du scénario."""
    import time
    from client_dialogue import QUESTIONS
    now = time.time() if now is None else now
    incident = s.get('desktop_incident')
    if not incident or incident['id'] != ident:
        raise ValueError('Ce dialogue ne concerne pas l’incident actif.')
    if incident.get('target_serial') and incident['target_serial']!=s['devices']['client']['serial']:
        import client_workspaces
        view=client_workspaces.project(s,incident['target_serial'])
        result=dialogue(view,ident,question,now)
        incident['dialogue']=view['desktop_incident']['dialogue']
        return result
    if question not in QUESTIONS:
        raise ValueError('Question inconnue.')
    family = incident['family']
    if family=='peripherals':
        import peripheral_incidents
        row=dict(at=now,question=QUESTIONS[question],answer=peripheral_incidents.answer(s,question),speaker=s['requester'])
        incident['dialogue'].append(row);incident['dialogue']=incident['dialogue'][-60:];return row
    if family=='workstation_setup':
        import workstation_requests
        answer=incident['description'] if question=='scope' else 'Cette demande prépare le poste pour son utilisateur.' if question=='when' else 'La préparation est conforme.' if question=='retest' and all(r['status']=='valide' for r in workstation_requests.checks(s,now)) else 'Il faut réaliser les actions demandées sur le poste, puis vérifier leur résultat.'
        row=dict(at=now,question=QUESTIONS[question],answer=answer,speaker=s['requester']);incident['dialogue'].append(row);incident['dialogue']=incident['dialogue'][-60:];return row
    if family=='deployment':
        import deployment_incidents
        return deployment_incidents.dialogue(s,question,now)
    if question == 'scope':
        answer = incident['description']
    elif question == 'when':
        answer = 'Cela fonctionnait lors de ma précédente utilisation. Je ne sais pas ce qui a changé.'
    elif question == 'network':
        observation = s.get('network_observation') or {}
        fresh = 0 <= now - observation.get('at', 0) <= ad.TTL
        link = observation.get('client_link') if fresh else None
        answer = 'La liaison réseau est indiquée débranchée.' if link is False else 'La liaison réseau est présente ; cela ne confirme pas le service.' if link is True else 'Je n’ai pas de constat réseau récent.'
    elif question == 'ip':
        target = s['devices'].get('printer', s['devices']['server'])['ip'] if family == 'printing' else s['devices']['server']['ip']
        status = ds.network(s, 'printing' if family == 'printing' else 'share', 'client', target, now)
        answer = 'Le dernier ping a réussi ; cela ne prouve pas le fonctionnement de l’application.' if status == 'passed' else 'Le dernier ping a échoué.' if status == 'failed' else 'Il faut effectuer un test réseau récent.'
    elif question == 'name':
        answer = 'Pour FTP, le ticket indique l’adresse IP du dépôt. Pour Documents, il faut également vérifier le nom du serveur.'
    elif question == 'login':
        answer = 'La connexion FTP est distincte de la session utilisateur ; ouvre le client FTP pour voir le résultat.' if family == 'ftp' else 'Ouvre la session utilisateur pour vérifier le message de connexion.'
    else:
        rows = checks(s, now)
        answer = 'Le résultat demandé est maintenant constaté.' if rows[0]['status'] == 'valide' else 'Je ne peux pas encore confirmer le résultat demandé.'
    row = dict(at=now, question=QUESTIONS[question], answer=answer, speaker=s['requester'])
    incident['dialogue'].append(row)
    incident['dialogue'] = incident['dialogue'][-60:]
    return row
