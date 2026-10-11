"""Annuaire imbriqué dans la session ; observations et acteur fournis par le serveur."""
import hashlib
import json
import time
import sim_ad

from network_proofs import TTL, proof

def ensure(state):
    if not state or 'directory' in state or not all(k in state.get('devices', {}) for k in ('client','server','technician')):
        return False
    env = state.get('environment_id', 'legacy')
    devices = [dict(id=k, name=d['name'], role=k) for k,d in state['devices'].items()]
    uid = 'usr-' + hashlib.sha256((state['seed']+':requester').encode()).hexdigest()[:16]
    requester = dict(id=uid, username=(state['staff'][0]['username'] if state.get('staff') else state['requester'].lower()), display_name=state['requester'], device_id='client')
    d = sim_ad.generate_directory(state['seed'], env, devices, requester, time.time())
    d['users'][uid]['enabled'] = state.get('account_enabled', True)
    group_ids = {}
    for action, label in [('read','Documents-Lecture'),('write','Documents-Ecriture')]:
        gid = 'grp-' + hashlib.sha256((state['seed']+':'+label).encode()).hexdigest()[:16]
        group_ids[action] = gid
        d['groups'][gid] = dict(id=gid, name=label, ou_id=next(iter(d['ous'])), member_user_ids=[uid] if state.get(action+'_allowed',False) else [])
    sim_ad.validate_directory(d)
    state.update(directory=d, directory_user_id=uid, directory_service=True,
                 directory_resource=dict(id='documents',server_device_id='server',allowed_user_ids={'read':[],'write':[]},allowed_group_ids={a:[gid] for a,gid in group_ids.items()}),
                 directory_auth=None)
    for k in ('account_enabled','read_allowed','write_allowed'):state.pop(k,None)
    return True


def context(state, source='client', now=None):
    now = time.time() if now is None else now
    key = 'directory' if source == 'technician' else 'share'
    network = proof(state,key,source,state['devices']['server']['ip'],now)
    if source=='technician':
        import technician_model
        policy=technician_model.policy(state,now)
        if not policy['allowed']:network['status']=policy['status']
    auth = authentication(state,source,now)
    return dict(environment_id=state.get('environment_id','legacy'), source_device_id=source, target_device_id='server', network=network,
                directory_service='running' if state.get('directory_service',True) else 'stopped',
                resource_service=state['file_service']['service_status'] if 'file_service' in state else 'running' if state['share_service'] else 'stopped', authentication=auth)


def access(state, action, now):
    if 'file_service' in state:
        import files_adapter
        return files_adapter.access(state, action, now)
    return sim_ad.evaluate_access(state['directory'],state['directory_user_id'],state['directory_resource'],action,context(state,now=now),now)


def actor(state):
    # Console de formation : rôle technicien administrateur, imposé par le serveur.
    return dict(id='technician',environment_id=state.get('environment_id','legacy'),permissions=[sim_ad.CAPABILITY_USERS,sim_ad.CAPABILITY_PASSWORDS,sim_ad.CAPABILITY_GROUPS,sim_ad.CAPABILITY_OUS,sim_ad.CAPABILITY_COMPUTERS])


def invalidate(state, all_clients=False):
    # Logout / échec de connexion : uniquement le poste actuellement sélectionné.
    if all_clients:
        for profile in state.get('client_workspaces',{}).values():profile['local']['directory_auth']=None
    state['directory_auth'] = None
    state['validated'] = False


def account_stamp(user):
    # Révision d'identité privée : groupes et expiration des observations exclus.
    fields={key:user.get(key) for key in ('id','username','enabled','credential','must_change_password')}
    return hashlib.sha256(json.dumps(fields,sort_keys=True).encode()).hexdigest()

def authentication(state,source,now):
    auth=state.get('directory_auth') or {};uid=state.get('directory_user_id')
    user=state.get('directory',{}).get('users',{}).get(uid)
    if not user or not user['enabled'] or auth.get('user_id')!=uid or auth.get('status')!='authenticated':return {}
    if auth.get('environment_id')!=state.get('environment_id','legacy') or auth.get('source_device_id')!=source:return {}
    if auth.get('kind')=='windows_logon':
        device=state['devices'][source]
        if auth.get('station_serial')!=device.get('serial') or auth.get('account_stamp')!=account_stamp(user):return {}
    elif now>=auth.get('expires_at',0):return {}
    return auth

def open_session(state,now):
    user=state['directory']['users'][state['directory_user_id']]
    return dict(kind='windows_logon',user_id=user['id'],status='authenticated',
                environment_id=state.get('environment_id','legacy'),source_device_id='client',
                station_serial=state['devices']['client'].get('serial'),issued_at=now,account_stamp=account_stamp(user))


def revoke_changed_sessions(state,before,after):
    old=before.get('users',{});new=after.get('users',{})
    changed={uid for uid in set(old)|set(new) if uid not in old or uid not in new or account_stamp(old[uid])!=account_stamp(new[uid])}
    if state.get('directory_user_id') in changed:state['directory_auth']=None
    for profile in state.get('client_workspaces',{}).values():
        if profile.get('user_id') in changed:profile['local']['directory_auth']=None
