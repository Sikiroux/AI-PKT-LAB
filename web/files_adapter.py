"""Raccordement des fichiers simulés aux preuves PT et identités AD du serveur."""
import copy
import hashlib
import time
import directory_adapter as ad
import sim_ad
import sim_files

def catalog(state):
    d = state['directory']
    return dict(user_ids=list(d['users']), group_ids=list(d['groups']))

def ensure(state):
    if not state or 'directory' not in state or 'file_service' in state:
        return False
    now = time.time(); server = state['devices']['server']
    service = sim_files.generate_file_service(state['seed'], state.get('environment_id','legacy'),
        dict(id='server', name=server['name'], ip=server['ip'], dns_name=server['name']), catalog(state), now)
    # Migrer le seul partage existant, sans donner les grants du générateur sain.
    sid = next(iter(service['shares'])); share = service['shares'][sid]
    share.update(name='Documents', enabled=True, hidden=False)
    acl = {a:dict(user_ids=copy.deepcopy(state['directory_resource']['allowed_user_ids'][right]),
                  group_ids=copy.deepcopy(state['directory_resource']['allowed_group_ids'][right]))
           for a,right in [('list','read'),('read','read'),('write','write'),('delete','write')]}
    share['share_acl'] = copy.deepcopy(acl); share['folder_acl'] = copy.deepcopy(acl)
    service['shares'] = {sid:share}; service['files'] = {}
    for name in state.get('files', ['Procedure.txt']):
        fid = 'file-'+hashlib.sha256((state['seed']+':legacy-file:'+name).encode()).hexdigest()[:16]
        service['files'][fid] = dict(id=fid,share_id=sid,name=name,content='Document de formation : '+name+'\n',read_only=False,updated_at=now)
    service['service_status'] = 'running' if state.get('share_service',True) else 'stopped'
    sim_files.validate_file_service(service)
    state.update(file_service=service, documents_share_id=sid)
    return True

def sync_catalog(state):
    if 'file_service' in state:
        state['file_service']['principal_catalog'] = catalog(state)
        sim_files.validate_file_service(state['file_service'])

def context(state, now):
    ctx = ad.context(state, now=now); net = ctx['network']
    uid = state['directory_user_id']; d = state['directory']
    account = sim_ad.evaluate_user(d, uid, ctx, now)
    result = dict(environment_id=state.get('environment_id','legacy'),source_device_id='client',target_device_id='server',
        address_mode='ip',network=dict(status={'passed':'up','failed':'down'}.get(net['status'],'unknown'),
            observed_at=net['observed_at'],valid_until=net['valid_until'],source_device_id='client',target_device_id='server',evidence='icmp_proxy'),
        identity=dict(user_id=uid,group_ids=[gid for gid,g in d['groups'].items() if uid in g['member_user_ids']],
            account_allowed=account['allowed'] and account['code']==sim_ad.OK,
            authentication_valid=ctx['authentication'].get('user_id')==uid and ctx['authentication'].get('status')=='authenticated'))
    if state.get('dns_incident') or state.get('mixed_incident'):
        import dns_adapter
        result['address_mode']='name'
        result['name_resolution']=dns_adapter.resolution(state,now)[0]
    return result

def presentation(outcome):
    result = copy.deepcopy(outcome)
    def node(value):
        value['label'] = {'name_resolution':'Résolution du nom du serveur', 'scope':'Environnement et poste', 'network':'Connectivité ICMP observée (approximation)',
            'share_permission':'Droit sur le partage', 'filesystem_permission':'Droit sur les fichiers',
            'authentication':'Utilisateur connecté', 'capacity':'Capacité du disque', 'quota':'Quota du partage',
            'account':'Compte utilisable', 'firewall':'Pare-feu du service', 'service':'Service de fichiers',
            'share_enabled':'Partage activé','share_found':'Partage présent','file_lookup':'Fichier demandé',
            'read_only':'Fichier modifiable'}.get(value['stage'],value['stage'])
        for child in value['children']:node(child)
    node(result['tree']);return result

def request(state, action):
    sid=state['documents_share_id']; files=state['file_service']['files']
    req=dict(action=action,share_id=sid)
    if action=='read':
        found=next((f for f in files.values() if f['share_id']==sid),None)
        if not found:return dict(action='list',share_id=sid)
        req['file_id']=found['id']
    elif action=='write':
        found=next((f for f in files.values() if f['share_id']==sid and f['name']=='Test.txt'),None)
        req.update(expected_revision=state['file_service']['revision'],content='Test de sauvegarde de formation.\n')
        if found:req['file_id']=found['id']
        else:req['name']='Test.txt'
    return req

def access(state, action, now):
    return presentation(sim_files.evaluate_access(state['file_service'],request(state,action),context(state,now),now))

def names(state):
    return [f['name'] for f in state['file_service']['files'].values() if f['share_id']==state['documents_share_id']]
