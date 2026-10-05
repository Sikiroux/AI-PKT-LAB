"""Incidents d'annuaire déterministes ; le ticket expose les symptômes seulement."""
import copy
import hashlib
import random
import sim_ad
import directory_adapter as ad

FAMILIES = ('account_disabled', 'account_locked', 'password_expired', 'read_group_missing', 'write_group_missing')

def prepare(state, now):
    if 'directory' not in state:
        raise ValueError('Un annuaire intégré est requis.')
    previous = state.get('directory_incident') or state.get('file_incident') or state.get('dns_incident') or state.get('mixed_incident')
    if previous and not state.get('validated'):
        raise ValueError('Résous et vérifie l’incident actuel avant le suivant.')
    s = copy.deepcopy(state)
    s.pop('file_incident',None);s.pop('dns_incident',None);s.pop('mixed_incident',None)
    index = s.get('directory_incident_count', 0)
    # Un cycle mélange les familles, sans répétition avant épuisement.
    r = random.Random(hashlib.sha256((str(s['seed']) + ':ad-incidents:' + str(index // len(FAMILIES))).encode()).hexdigest())
    order = list(FAMILIES); r.shuffle(order)
    family = order[index % len(order)]
    d = s['directory']; uid = s['directory_user_id']; user = d['users'][uid]
    # L'action explicite démarre un nouvel exercice sur le même réseau.
    user.update(enabled=True, locked_until=None, failed_attempts=0,
                must_change_password=False, password_expires_at=now+d['policy']['password_max_age_seconds'])
    for action in ('read', 'write'):
        for gid in s['directory_resource']['allowed_group_ids'][action]:
            if uid not in d['groups'][gid]['member_user_ids']:
                d['groups'][gid]['member_user_ids'].append(uid)
    if 'file_service' in s:
        share=s['file_service']['shares'][s['documents_share_id']]
        for layer in ('share_acl','folder_acl'):
            for a,right in [('list','read'),('read','read'),('write','write'),('delete','write')]:
                grant=share[layer][a]
                grant['user_ids']=[x for x in grant['user_ids'] if x!=uid]
                grant['group_ids']=list(dict.fromkeys(grant['group_ids']+s['directory_resource']['allowed_group_ids'][right]))
        s['file_service']['revision']+=1
    if family == 'account_disabled': user['enabled'] = False
    elif family == 'account_locked':
        user['locked_until'] = now + d['policy']['lockout_seconds']
        user['failed_attempts'] = d['policy']['lockout_threshold']
    elif family == 'password_expired': user['password_expires_at'] = now-1
    else:
        action = 'read' if family == 'read_group_missing' else 'write'
        for gid in s['directory_resource']['allowed_group_ids'][action]:
            d['groups'][gid]['member_user_ids'] = [x for x in d['groups'][gid]['member_user_ids'] if x != uid]
        s['directory_resource']['allowed_user_ids'][action] = [x for x in s['directory_resource']['allowed_user_ids'][action] if x != uid]
        if 'file_service' in s:
            share=s['file_service']['shares'][s['documents_share_id']]
            for layer in ('share_acl','folder_acl'):
                for a in (('list','read') if action=='read' else ('write','delete')):
                    share[layer][a]['user_ids']=[x for x in share[layer][a]['user_ids'] if x!=uid]
    d['revision'] += 1
    d['audit'].append(dict(at=now, operation='training_incident', code='INJECTED'))
    sim_ad.validate_directory(d)
    user_name = s['requester']; pc = s['devices']['client']['name']
    descriptions = {
        'account_disabled': f'{user_name} signale que sa connexion habituelle est refusée sur {pc}.',
        'account_locked': f'{user_name} ne peut plus ouvrir sa session sur {pc}, après plusieurs essais.',
        'password_expired': f'{user_name} indique que son mot de passe habituel ne permet plus de terminer la connexion sur {pc}.',
        'read_group_missing': f'{user_name} peut se connecter sur {pc}, mais ne peut plus ouvrir les documents partagés.',
        'write_group_missing': f'{user_name} ouvre les documents sur {pc}, mais ne peut plus enregistrer ses modifications.',
    }
    goal = 'write' if family == 'write_group_missing' else 'read'
    title = 'Enregistrement des documents impossible' if goal == 'write' else ('Documents partagés inaccessibles' if family == 'read_group_missing' else 'Connexion utilisateur impossible')
    incident = dict(id='INC-AD-'+str(index+1).zfill(4), title=title,
                    description=descriptions[family]+' Rétablis la connexion utilisateur et la lecture'+(' ainsi que l’écriture' if goal == 'write' else '')+' de Documents.',
                    goal=goal, family=family, created=now)
    s.update(directory_incident=incident, directory_incident_count=index+1, ticket=incident['description'])
    ad.invalidate(s); s['remote_session'] = False
    return s

def public_incident(state):
    value = state.get('directory_incident')
    return {k: value[k] for k in ('id', 'title', 'description', 'goal', 'created')} if value else None
