"""Incidents de fichiers reproductibles, objectifs et contrôle des collatéraux."""
import copy
import hashlib
import random
import directory_adapter as ad
import files_adapter as fa
import sim_ad
import sim_files

FAMILIES=('service_stopped','share_disabled','firewall_blocked','share_read_missing',
          'folder_write_missing','quota_full','disk_full','file_read_only')

def rights(state, uid):
    share=state['file_service']['shares'][state['documents_share_id']]
    groups={gid for gid,g in state['directory']['groups'].items() if uid in g['member_user_ids']}
    return {a:all(uid in share[layer][a]['user_ids'] or bool(groups & set(share[layer][a]['group_ids']))
                  for layer in ('share_acl','folder_acl')) for a in sim_files.ACTIONS}

def prepare(state, now):
    if 'file_service' not in state:raise ValueError('Partages intégrés requis.')
    if (state.get('directory_incident') or state.get('file_incident') or state.get('dns_incident')) and not state.get('validated'):
        raise ValueError('Résous et vérifie l’incident actuel avant le suivant.')
    s=copy.deepcopy(state);s.pop('directory_incident',None);s.pop('dns_incident',None)
    index=s.get('file_incident_count',0)
    rng=random.Random(hashlib.sha256((str(s['seed'])+':file-incidents:'+str(index//len(FAMILIES))).encode()).hexdigest())
    order=list(FAMILIES);rng.shuffle(order);family=order[index%len(order)]
    d=s['directory'];uid=s['directory_user_id'];user=d['users'][uid]
    user.update(enabled=True,locked_until=None,failed_attempts=0,must_change_password=False,
                password_expires_at=now+d['policy']['password_max_age_seconds'])
    service=s['file_service'];sid=s['documents_share_id'];share=service['shares'][sid]
    for right in ('read','write'):
        for gid in s['directory_resource']['allowed_group_ids'][right]:
            if uid not in d['groups'][gid]['member_user_ids']:d['groups'][gid]['member_user_ids'].append(uid)
    for layer in ('share_acl','folder_acl'):
        for a in sim_files.ACTIONS:
            if uid not in share[layer][a]['user_ids']:share[layer][a]['user_ids'].append(uid)
    target=next((f for f in service['files'].values() if f['share_id']==sid),None)
    if not target:raise ValueError('Crée un fichier dans Documents avant cet exercice.')
    target['read_only']=False
    service.update(service_status='running',firewall_tcp445_allowed=True)
    share.update(enabled=True,quota=dict(mode='off',limit_bytes=None))
    used=service['volume']['background_used_bytes']+sum(len(f['content'].encode()) for f in service['files'].values())
    service['volume']['capacity_bytes']=max(service['volume']['capacity_bytes'],used+4096)
    baseline=dict(files={fid:copy.deepcopy(f) for fid,f in service['files'].items() if fid!=target['id']},
                  other_users={x:copy.deepcopy(u) for x,u in d['users'].items() if x!=uid},
                  other_rights={x:rights(s,x) for x in d['users'] if x!=uid},
                  original_name=target['name'])
    goal='write' if family in ('folder_write_missing','quota_full','disk_full','file_read_only') else 'read'
    if family=='service_stopped':service['service_status']='stopped'
    elif family=='share_disabled':share['enabled']=False
    elif family=='firewall_blocked':service['firewall_tcp445_allowed']=False
    elif family in ('share_read_missing','folder_write_missing'):
        layer='share_acl' if family=='share_read_missing' else 'folder_acl'
        action='read' if family=='share_read_missing' else 'write'
        grant=share[layer][action];grant['user_ids']=[x for x in grant['user_ids'] if x!=uid]
        mine={gid for gid,g in d['groups'].items() if uid in g['member_user_ids']}
        grant['group_ids']=[x for x in grant['group_ids'] if x not in mine]
    elif family=='quota_full':
        total=sum(len(f['content'].encode()) for f in service['files'].values() if f['share_id']==sid)
        share['quota']=dict(mode='hard',limit_bytes=max(1,total))
    elif family=='disk_full':service['volume']['capacity_bytes']=max(1,used)
    else:target['read_only']=True
    service['revision']+=1;d['revision']+=1
    d['audit'].append(dict(at=now,operation='training_file_incident',code='INJECTED'))
    sim_ad.validate_directory(d);sim_files.validate_file_service(service)
    name=target['name'];user_name=s['requester'];pc=s['devices']['client']['name']
    description=(f'{user_name}, sur {pc}, signale que le document {name} dans Documents '
                 +('s’ouvre mais ne peut plus être enregistré.' if goal=='write' else 'ne peut plus être ouvert.'))
    description+=f' Rétablis la lecture'+(' et une sauvegarde de ce document avec du texte supplémentaire' if goal=='write' else '')+'. Préserve les autres fichiers et les accès des autres utilisateurs.'
    incident=dict(id='INC-FIC-'+str(index+1).zfill(4),family=family,goal=goal,
                  title='Sauvegarde de document impossible' if goal=='write' else 'Document partagé inaccessible',
                  description=description,target_file_id=target['id'],created=now,baseline=baseline)
    s.update(file_incident=incident,file_incident_count=index+1,ticket=description)
    ad.invalidate(s);s['remote_session']=False
    return s

def public_incident(state):
    i=state.get('file_incident')
    return {k:i[k] for k in ('id','goal','title','description','target_file_id','created')} if i else None

def request(state, action):
    i=state['file_incident'];sid=state['documents_share_id'];fid=i['target_file_id']
    req=dict(action=action,share_id=sid,file_id=fid)
    if action=='write':
        f=state['file_service']['files'].get(fid)
        req.update(content=(f['content'] if f else '')+'\nTest de sauvegarde.\n',expected_revision=state['file_service']['revision'])
    return req

def access(state, action, now):
    return fa.presentation(sim_files.evaluate_access(state['file_service'],request(state,action),fa.context(state,now),now))

def checks(state, now):
    i=state['file_incident'];base=i['baseline'];service=state['file_service'];target=service['files'].get(i['target_file_id'])
    rows=[]
    for action in (('read','write') if i['goal']=='write' else ('read',)):
        result=access(state,action,now)
        rows.append(dict(label='Lecture du document ciblé' if action=='read' else 'Sauvegarde avec du texte supplémentaire',
                         status='valide' if result['allowed'] else ('inconnu' if result['status']=='unknown' else 'non satisfait'),
                         detail='Évaluation du moteur de fichiers avec observation réseau récente, sans écrire pendant le contrôle.'))
    unchanged=all(service['files'].get(fid)==f for fid,f in base['files'].items())
    unchanged=unchanged and bool(target and target['name']==base['original_name'])
    unchanged=unchanged and all(state['directory']['users'].get(uid)==u and rights(state,uid)==base['other_rights'][uid]
                                for uid,u in base['other_users'].items())
    rows.append(dict(label='Autres fichiers et accès préservés',status='valide' if unchanged else 'non satisfait',
                     detail='Comparaison avec l’état de départ de cet incident, hors fichier ciblé.'))
    return rows
