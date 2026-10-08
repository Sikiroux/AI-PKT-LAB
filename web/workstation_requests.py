"""Préparation applicative du client existant, résultats issus d’actions observées."""
import copy
import hashlib
import random
import desktop_services as ds
import directory_adapter as ad
import files_adapter as fa
import file_incidents
import sim_files

PROFILES={
 'documents':dict(label='Poste documentaire',apps=['documents'],tasks=['read']),
 'office':dict(label='Poste de bureautique',apps=['documents','printers'],tasks=['read','print']),
 'exchange':dict(label='Poste d’échange de fichiers',apps=['documents','printers','ftp'],tasks=['read','print','download','upload'])}

def prepare(state,now,minutes=30):
    s=copy.deepcopy(state);ds.ensure(s);index=s.get('desktop_incident_count',0)+1
    rng=random.Random(hashlib.sha256((str(s['seed'])+':workstation-requests:v1:'+str(index)).encode()).hexdigest())
    profile=rng.choice(list(PROFILES));plan=PROFILES[profile];d=s['desktop_services'];e=d['endpoint'];f=d['ftp'];p=d['printing']
    suffix=hashlib.sha256((str(s['seed'])+str(index)).encode()).hexdigest()[:6].upper()
    print_name='Accueil-'+suffix+'.txt';upload='Rapport-'+suffix+'.txt';download='Guide-'+suffix+'.txt'
    content='Préparation du poste — '+s['company']+' — '+s['requester']+' — '+suffix
    slots=(1 if 'print' in plan['tasks'] else 0)+(2 if 'download' in plan['tasks'] else 0)
    if len(e['local_files'])+slots>100:raise ValueError('Libère '+str(slots)+' emplacements de fichiers locaux avant cette demande.')
    added_ftp='Guide utilisateur — '+s['company']+' — '+suffix
    needed=sum(len(v.encode('utf-8')) for v in f['files'].values())+len(added_ftp.encode('utf-8'))+len(content.encode('utf-8'))
    if 'download' in plan['tasks'] and needed>f['capacity_bytes']:raise ValueError('Le dépôt FTP manque de capacité pour la demande ; ajuste sa capacité avant de générer.')
    if 'print' in plan['tasks']:e['local_files'][print_name]='Fiche d’accueil — '+s['company']
    if 'download' in plan['tasks']:
        e['local_files'][upload]=content;f['files'][download]=added_ftp
    candidates=[x for x in s['file_service']['files'].values() if x['share_id']==s['documents_share_id']]
    if not candidates:raise ValueError('Un document partagé est requis pour la préparation du poste.')
    target=rng.choice(candidates)
    # Le scénario fournit des services utilisables et retire les réglages du poste.
    # Grants directs au seul demandeur : ne pas élargir les groupes des collègues.
    uid=s['directory_user_id'];fs=s['file_service'];share=fs['shares'][s['documents_share_id']]
    fs.update(service_status='running',firewall_tcp445_allowed=True);share['enabled']=True
    s['directory']['users'][uid].update(enabled=True,locked_until=None,must_change_password=False,password_expires_at=now+3600)
    for layer in ('share_acl','folder_acl'):
        for action in ('list','read'):
            grants=share[layer][action]['user_ids']
            if uid not in grants:grants.append(uid)
    if 'print' in plan['tasks']:
        p['spooler_running']=True;p['queues']['office'].update(port_ip=s['devices'][p['printer']['device_role']]['ip'],driver_valid=True,paused=False,use_offline=False)
        p['printer'].update(enabled=True,paper_pages=max(20,p['printer']['paper_pages']))
    if 'download' in plan['tasks']:
        f.update(service_running=True,control_allowed=True,data_allowed=True)
        f['accounts']['depot'].update(enabled=True,read=True,write=True,password_hash=ds.password_hash('Formation!2026'))
    baseline=dict(devices=copy.deepcopy(s['devices']),shared_files=copy.deepcopy(s['file_service']['files']),local_files=copy.deepcopy(e['local_files']),ftp_files=copy.deepcopy(f['files']),ftp_accounts=copy.deepcopy(f['accounts']),other_users={k:copy.deepcopy(v) for k,v in s['directory']['users'].items() if k!=s['directory_user_id']},other_rights={k:file_incidents.rights(s,k) for k in s['directory']['users'] if k!=s['directory_user_id']},other_apps=[a for a in e['applications'] if a not in plan['apps']])
    e['applications']=[a for a in e['applications'] if a not in plan['apps']];e['mapped_drive']['path']='\\\\'+s['devices']['server']['name']+'\\AncienDossier'
    if 'print' in plan['tasks']:p['default_queue']='pdf'
    f['sessions']={}
    for key in ('desktop_incident','mixed_incident','directory_incident','file_incident','dns_incident'):s.pop(key,None)
    todo=['Installer '+', '.join(ds.APPS[a] for a in plan['apps']), 'Raccorder le lecteur Z: à '+'\\\\'+s['devices']['server']['name']+'\\Documents', 'Ouvrir le document partagé '+target['name']]
    if 'print' in plan['tasks']:todo.append('Choisir '+p['queues']['office']['name']+' par défaut et imprimer '+print_name)
    if 'download' in plan['tasks']:todo.append('Avec Client FTP, compte depot / Formation!2026, télécharger '+download+' et envoyer '+upload+' vers '+s['devices']['server']['ip'])
    description=s['requester']+' demande la préparation de '+s['devices']['client']['name']+' : '+plan['label']+'. '+'. '.join(todo)+'. Préserve les autres applications, fichiers et utilisateurs. Il s’agit du poste client simulé existant ; aucun nouveau PC Packet Tracer n’est créé.'
    incident=dict(id='INC-APP-'+str(index).zfill(4),title='Préparer un poste · '+plan['label'],description=description,goal='workstation_setup',family='workstation_setup',created=now,dialogue=[],timer_minutes=minutes,profile=profile,required_apps=plan['apps'],tasks=plan['tasks'],target_file_id=target['id'],print_name=print_name,upload=upload,download=download,content=content,evidence={},baseline=baseline)
    s.update(desktop_incident=incident,desktop_incident_count=index,ticket=description,validated=False,remote_session=False);ad.invalidate(s);return s

def record(s,kind,name,now):
    i=s.get('desktop_incident') or {}
    targets={'read':i.get('target_file_id'),'download':i.get('download'),'upload':i.get('upload')}
    if i.get('target_serial',s['devices']['client']['serial'])!=s['devices']['client']['serial']:return False
    if i.get('family')!='workstation_setup' or kind not in i['tasks'] or kind not in targets or targets[kind]!=name:return False
    i['evidence'][kind]=dict(at=now,environment_id=s['environment_id'],source=s['devices']['client']['serial'],target=name);return True

def checks(s,now):
    i=s['desktop_incident'];d=s['desktop_services'];e=d['endpoint'];f=d['ftp'];p=d['printing'];rows=[]
    def row(label,ok,detail,unknown=False):rows.append(dict(label=label,status='valide' if ok else 'inconnu' if unknown else 'non satisfait',detail=detail))
    def evidence(kind):
        v=i['evidence'].get(kind,{})
        target={'read':i['target_file_id'],'download':i['download'],'upload':i['upload']}.get(kind)
        return v.get('target')==target and v.get('environment_id')==s['environment_id'] and v.get('source')==s['devices']['client']['serial'] and i['created']<=v.get('at',0)<=now
    row('Applications demandées installées',all(a in e['applications'] for a in i['required_apps']),'Vérification du poste simulé.')
    import desktop_incidents as di
    access=sim_files.evaluate_access(s['file_service'],dict(action='read',share_id=s['documents_share_id'],file_id=i['target_file_id']),fa.context(s,now),now);read_ok='documents' in e['applications'] and access['allowed'] and di.drive_ok(s) and evidence('read')
    row('Lecteur partagé et document ouverts',read_ok,'Lecture réussie du document ciblé depuis le client et accès actuel.',access['status']=='unknown')
    if 'print' in i['tasks']:
        r=ds.evaluate_print(s,'office',now)
        printed=any(j['name']==i['print_name'] and j['queue_id']=='office' and j['status']=='printed' and j['created_at']>=i['created'] and j['content']==i['baseline']['local_files'][i['print_name']] for j in p['jobs'])
        row('Impression sur la bonne file par défaut',r['allowed'] and p['default_queue']=='office' and printed,'Travail réellement traité par le moteur d’impression simulé.',r['status']=='unknown')
    if 'download' in i['tasks']:
        for task in ('download','upload'):
            r=ds.ftp_check(s,task,'client',now)
            copied=e['local_files'].get(i['download'])==i['baseline']['ftp_files'][i['download']] if task=='download' else f['files'].get(i['upload'])==i['content']
            row('Guide téléchargé' if task=='download' else 'Rapport envoyé',r['allowed'] and evidence(task) and copied,'Transfert réussi depuis le Client FTP, contenu conservé.',r['status']=='unknown')
    b=i['baseline'];preserved=s['devices']==b['devices'] and s['file_service']['files']==b['shared_files'] and all(e['local_files'].get(k)==v for k,v in b['local_files'].items()) and all(f['files'].get(k)==v for k,v in b['ftp_files'].items()) and f['accounts']==b['ftp_accounts'] and all(s['directory']['users'].get(k)==v and file_incidents.rights(s,k)==b['other_rights'][k] for k,v in b['other_users'].items()) and all(a in e['applications'] for a in b['other_apps'])
    row('Autres appareils, fichiers et utilisateurs préservés',preserved,'Comparaison avec le début de la demande.');return rows
