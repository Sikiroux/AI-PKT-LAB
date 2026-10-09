"""Annuaire imbriqué dans la session ; observations et acteur fournis par le serveur."""
import hashlib
import time
import sim_ad

TTL = 45

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
    observation = state.get('observation') or {}
    key = 'directory' if source == 'technician' else 'share'
    probe = observation.get('probes',{}).get(key, {})
    # A legacy aggregate observation is insufficient for this source-target pair.
    expected = state['devices'][source]['name']
    target = state['devices']['server']['ip']
    valid = probe.get('source_device') == expected and probe.get('target') == target
    network = dict(status=probe.get('status','unknown') if valid else 'unknown', observed_at=probe.get('at',0), valid_until=probe.get('at',0)+TTL, evidence='icmp_proxy')
    if source=='technician':
        import technician_model
        policy=technician_model.policy(state,now)
        if not policy['allowed']:network['status']=policy['status']
    auth = state.get('directory_auth') or {}
    if auth.get('environment_id') != state.get('environment_id','legacy') or auth.get('source_device_id') != source or now > auth.get('expires_at',0):auth={}
    return dict(environment_id=state.get('environment_id','legacy'), source_device_id=source, target_device_id='server', network=network,
                directory_service='running' if state.get('directory_service',True) else 'stopped',
                resource_service='running' if state['share_service'] else 'stopped', authentication=auth)


def access(state, action, now):
    if 'file_service' in state:
        import files_adapter
        return files_adapter.access(state, action, now)
    return sim_ad.evaluate_access(state['directory'],state['directory_user_id'],state['directory_resource'],action,context(state,now=now),now)


def actor(state):
    # Console de formation : rôle technicien administrateur, imposé par le serveur.
    return dict(id='technician',environment_id=state.get('environment_id','legacy'),permissions=[sim_ad.CAPABILITY_USERS,sim_ad.CAPABILITY_PASSWORDS,sim_ad.CAPABILITY_GROUPS,sim_ad.CAPABILITY_OUS,sim_ad.CAPABILITY_COMPUTERS])


def invalidate(state):
    for profile in state.get('client_workspaces',{}).values():profile['local']['directory_auth']=None
    state['directory_auth'] = None
    state['validated'] = False
