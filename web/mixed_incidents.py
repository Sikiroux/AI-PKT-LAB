"""Tickets multi-couches reproductibles ; causes privées, symptômes communs."""
import copy
import hashlib
import random
import directory_adapter as ad
import dns_adapter as da
import files_adapter as fa
import file_incidents as fi
import sim_dns

CATALOGUE={
 'ad':('account_disabled','account_locked','password_expired','read_group_missing','write_group_missing'),
 'files':fi.FAMILIES,
 'dns':('wrong_resolver','missing_record','wrong_address','service_stopped','transport_blocked','negative_cache','stale_cache'),
 'network':('cable_disconnected',)}
WRITE={'write_group_missing','folder_write_missing','quota_full','disk_full','file_read_only'}

def catalogue():
    return [dict(id=layer+':'+cause,label={'ad':'Annuaire','files':'Fichiers','dns':'DNS','network':'Réseau'}[layer]+' · '+cause) for layer,causes in CATALOGUE.items() for cause in causes]

def choose(seed,index,level,target='random'):
    if type(level) is not int or level not in (1,2,3):raise ValueError('Difficulté : 1, 2 ou 3 couches.')
    if target not in ('random',*CATALOGUE):raise ValueError('Famille ciblée inconnue.')
    rng=random.Random(hashlib.sha256((str(seed)+':mixed:v1:'+str(index)).encode()).hexdigest())
    layers=list(CATALOGUE);rng.shuffle(layers)
    if target!='random':layers.remove(target);layers.insert(0,target)
    return [(layer,rng.choice(CATALOGUE[layer])) for layer in layers[:level]]

def prepare(state,now,level=1,target='random'):
    if any(state.get(k) for k in ('mixed_incident','dns_incident','file_incident','directory_incident')) and not state.get('validated'):raise ValueError('Termine et vérifie l’incident courant.')
    causes=choose(state['seed'],state.get('mixed_incident_count',0),level,target)
    s=copy.deepcopy(state);da.ensure(s)
    for k in ('mixed_incident','dns_incident','file_incident','directory_incident'):s.pop(k,None)
    d=s['directory'];uid=s['directory_user_id'];u=d['users'][uid]
    u.update(enabled=True,locked_until=None,failed_attempts=0,must_change_password=False,password_expires_at=now+d['policy']['password_max_age_seconds'])
    s.update(directory_service=True,remote_service=True)
    fs=s['file_service'];sid=s['documents_share_id'];share=fs['shares'][sid]
    fs.update(service_status='running',firewall_tcp445_allowed=True);share.update(enabled=True,quota=dict(mode='off',limit_bytes=None))
    for right in ('read','write'):
        gid=s['directory_resource']['allowed_group_ids'][right][0]
        if uid not in d['groups'][gid]['member_user_ids']:d['groups'][gid]['member_user_ids'].append(uid)
        for layer in ('share_acl','folder_acl'):
            for action in (('list','read') if right=='read' else ('write','delete')):
                grant=share[layer][action];grant['user_ids']=[x for x in grant['user_ids'] if x!=uid]
                grant['group_ids']=list(dict.fromkeys(grant['group_ids']+[gid]))
    file=next((f for f in fs['files'].values() if f['share_id']==sid),None)
    if not file:raise ValueError('Un document de départ est requis.')
    file['read_only']=False
    used=fs['volume']['background_used_bytes']+sum(len(f['content'].encode()) for f in fs['files'].values())
    fs['volume']['capacity_bytes']=max(fs['volume']['capacity_bytes'],used+4096)
    dns=s['dns_service'];name=s['documents_dns_name'];dns.update(service_status='running',transport_allowed=True)
    dns['clients']['client'].update(dns_server_ip=dns['server']['ip'],search_suffix=dns['server']['zone']);dns['cache']['client']={}
    rid=next((x for x,r in dns['records'].items() if r['name']==name and r['type']=='A'),None)
    if rid is None:
        rid='documents-primary';dns['records'][rid]=dict(id=rid,name=name,type='A',value=fs['server']['ip'],ttl=300,enabled=True)
    dns['records'][rid].update(value=fs['server']['ip'],enabled=True)
    goal='write' if any(c in WRITE for _,c in causes) else 'read'
    baseline=dict(files={x:copy.deepcopy(f) for x,f in fs['files'].items() if x!=file['id']},original_name=file['name'],other_users={x:copy.deepcopy(user) for x,user in d['users'].items() if x!=uid},other_rights={x:fi.rights(s,x) for x in d['users'] if x!=uid},records={x:copy.deepcopy(r) for x,r in dns['records'].items() if x!=rid},technician_dns=copy.deepcopy(dns['clients']['technician']))
    requester_groups={g for g,obj in d['groups'].items() if uid in obj['member_user_ids']}
    wrong='192.0.2.254' if dns['server']['ip']!='192.0.2.254' else '192.0.2.253'
    for layer,cause in causes:
        if layer=='ad':
            if cause=='account_disabled':u['enabled']=False
            elif cause=='account_locked':u.update(locked_until=now+d['policy']['lockout_seconds'],failed_attempts=d['policy']['lockout_threshold'])
            elif cause=='password_expired':u['password_expires_at']=now-1
            else:
                right='read' if cause=='read_group_missing' else 'write'
                for gid in share['share_acl'][right]['group_ids']+share['folder_acl'][right]['group_ids']:
                    if uid in d['groups'][gid]['member_user_ids']:d['groups'][gid]['member_user_ids'].remove(uid)
        elif layer=='files':
            if cause=='service_stopped':fs['service_status']='stopped'
            elif cause=='share_disabled':share['enabled']=False
            elif cause=='firewall_blocked':fs['firewall_tcp445_allowed']=False
            elif cause in ('share_read_missing','folder_write_missing'):
                acl='share_acl' if cause=='share_read_missing' else 'folder_acl';action='read' if cause=='share_read_missing' else 'write'
                share[acl][action]=dict(user_ids=[x for x in share[acl][action]['user_ids'] if x!=uid],group_ids=[g for g in share[acl][action]['group_ids'] if g not in requester_groups])
            elif cause=='quota_full':share['quota']=dict(mode='hard',limit_bytes=max(1,sum(len(f['content'].encode()) for f in fs['files'].values() if f['share_id']==sid)))
            elif cause=='disk_full':fs['volume']['capacity_bytes']=max(1,used)
            else:file['read_only']=True
        elif layer=='dns':
            rec=dns['records'][rid]
            if cause=='wrong_resolver':dns['clients']['client']['dns_server_ip']=wrong
            elif cause=='missing_record':rec['enabled']=False
            elif cause=='wrong_address':rec['value']=wrong
            elif cause=='service_stopped':dns['service_status']='stopped'
            elif cause=='transport_blocked':dns['transport_allowed']=False
            else:
                rec.update(enabled=cause!='negative_cache',value=wrong if cause=='stale_cache' else dns['server']['ip'])
                out=sim_dns.resolve(dns,'client',dict(name=name,type='A'),da.context(s,'client',now),now)
                dns=out['service'];s['dns_service']=dns;dns['records'][rid].update(enabled=True,value=fs['server']['ip'])
    fs['revision']+=1;d['revision']+=1;dns['revision']+=1
    index=s.get('mixed_incident_count',0)+1
    text=f"{s['requester']} ({s['devices']['client']['name']}) signale : « "+('Je ne peux plus enregistrer mes modifications dans Documents.' if goal=='write' else 'Je n’arrive plus à ouvrir mon document dans Documents.')+f" » Document concerné : {file['name']}, serveur {name}. Rétablis la lecture"+(' et la sauvegarde avec du texte supplémentaire' if goal=='write' else '')+'. Préserve les autres accès et fichiers. Tu peux contacter le demandeur pour préciser les symptômes.'
    s.update(mixed_incident=dict(id='INC-MIX-'+str(index).zfill(4),title='Accès aux documents perturbé',description=text,goal=goal,level=level,causes=causes,target_file_id=file['id'],created=now,baseline=baseline,injection_state='pending' if any(l=='network' for l,_ in causes) else 'applied',dialogue=[]),mixed_incident_count=index,ticket=text,remote_session=False)
    ad.invalidate(s);return s

def public(s):
    i=s.get('mixed_incident')
    if not i:return None
    out={k:copy.deepcopy(i[k]) for k in ('id','title','description','goal','level','target_file_id','created','dialogue')}
    out['requires_confirmation']=i['injection_state']!='applied'
    return out

def request(s,action):
    i=s['mixed_incident'];fid=i['target_file_id'];r=dict(action=action,share_id=s['documents_share_id'],file_id=fid)
    if action=='write':r.update(content=s['file_service']['files'].get(fid,{}).get('content','')+'\nTest de sauvegarde.\n',expected_revision=s['file_service']['revision'])
    return r

def access(s,action,now):
    import sim_files
    return fa.presentation(sim_files.evaluate_access(s['file_service'],request(s,action),fa.context(s,now),now))

def checks(s,now):
    i=s['mixed_incident'];b=i['baseline'];fs=s['file_service'];file=fs['files'].get(i['target_file_id'])
    out=[]
    for action in ('read','write') if i['goal']=='write' else ('read',):
        r=access(s,action,now);out.append(dict(label='Lecture du document' if action=='read' else 'Sauvegarde avec croissance',status='valide' if r['allowed'] else ('inconnu' if r['status']=='unknown' else 'non satisfait'),detail='Contrôle actuel du réseau et des services simulés.'))
    ok=bool(file and file['name']==b['original_name']) and all(fs['files'].get(x)==f for x,f in b['files'].items())
    ok=ok and all(s['directory']['users'].get(x)==u and fi.rights(s,x)==b['other_rights'][x] for x,u in b['other_users'].items())
    ok=ok and all(s['dns_service']['records'].get(x)==r for x,r in b['records'].items()) and s['dns_service']['clients']['technician']==b['technician_dns']
    if i.get('network_baseline'):
        observed=s.get('network_observation') or {};fresh=0<=now-observed.get('at',0)<=ad.TTL
        ok=ok and fresh and all(observed.get('devices',{}).get(x)==v for x,v in i['network_baseline'].items())
    out.append(dict(label='Autres fichiers, droits et réseau préservés',status='valide' if ok else 'non satisfait',detail='État de référence de cette intervention.'))
    out.append(dict(label='Injection confirmée',status='valide' if i['injection_state']=='applied' else 'inconnu',detail='Une opération incertaine doit être contrôlée avant clôture.'))
    return out
