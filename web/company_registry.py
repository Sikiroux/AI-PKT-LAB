"""Liens persistants du périmètre représenté ; jamais une preuve réseau ou un droit."""
import copy
import hashlib

VERSION = 1


def _id(state, kind, key):
    # Identité logique reproductible ; l'environnement reste la portée obligatoire.
    return kind + '-' + hashlib.sha256((str(state['seed']) + ':registry:v1:' + kind + ':' + key).encode()).hexdigest()[:20]


def ensure(state):
    if not state or not state.get('devices') or state.get('_client_view'):
        return False
    before = copy.deepcopy(state.get('company_registry'))
    env = state.get('environment_id', 'legacy')
    registry = state.setdefault('company_registry', dict(version=VERSION, environment_id=env, people={}, assets={}))
    if registry['version'] != VERSION or registry['environment_id'] != env:
        raise ValueError('Référentiel incompatible avec cet environnement.')
    profiles = dict(state.get('client_workspaces', {}))
    primary = state['devices'].get('client', {})
    if primary.get('serial'):
        profiles[primary['serial']] = dict(device=primary, user_id=state.get('directory_user_id'), requester=state.get('requester'))
    users = state.get('directory', {}).get('users', {})
    for person in registry['people'].values():
        person['represented'] = False
    for asset in registry['assets'].values():
        asset.update(represented=False, employee_id=None)
    for serial, profile in profiles.items():
        uid = profile.get('user_id')
        if not uid:
            continue
        ident = _id(state, 'employee', uid)
        user = users.get(uid, {})
        person = registry['people'].setdefault(ident, dict(id=ident, environment_id=env, account_id=uid))
        staff=next((r for r in state.get('staff',[]) if r['display_name']==profile.get('requester')),{})
        if staff:person.update(department=staff['department'],activity=staff['activity'])
        person.update(display_name=user.get('display_name', profile.get('requester') or uid),
                      username=user.get('username'), account_present=uid in users, represented=True)
    # Les rôles générés assurent un lien stable, même si l'appareil est renommé.
    for role, device in state['devices'].items():
        serial = device.get('serial')
        if not serial:
            continue
        ident = _id(state, 'asset', role)
        asset = registry['assets'].setdefault(ident, dict(id=ident, environment_id=env, source_role=role))
        profile = profiles.get(serial, {})
        uid = profile.get('user_id')
        employee = _id(state, 'employee', uid) if uid else None
        asset.update(serial=serial, name=device['name'], ip=device.get('ip'), represented=True,
                     employee_id=employee, owner_kind='technician' if role == 'technician' else 'employee' if employee else 'infrastructure')
    __import__('sim_corporate').sync_people(state)
    return before != registry


def links(state, serial):
    registry = state.get('company_registry') or {}
    if registry.get('environment_id') != state.get('environment_id', 'legacy'):
        return {}
    matches = [a for a in registry.get('assets', {}).values() if a.get('represented') and a.get('serial') == serial]
    if len(matches) != 1:
        return {}
    a = matches[0]
    return dict(environment_id=registry['environment_id'], asset_id=a['id'], employee_id=a['employee_id'])


def public(state):
    # Pas de mot de passe, permissions, panne cachée ou observation réseau.
    registry = state.get('company_registry')
    if not registry:
        return None
    return copy.deepcopy(registry) | dict(scope='represented_endpoints', complete_staff=len(state.get('staff',[]))==30 and sum(bool(p.get('represented')) for p in registry['people'].values())==30)


def link_tickets(state, tickets):
    """Ne rattache que les tickets de cet environnement et les postes non ambigus."""
    changed = False
    primary = state.get('devices', {}).get('client', {})
    for ticket in tickets:
        if ticket.get('kind') != 'workspace':
            continue
        if ticket.get('environment_id') not in (None, state.get('environment_id', 'legacy')):
            continue
        serial = ticket.get('target_serial')
        # Seul le premier ticket historique possède une cible implicite connue.
        if not serial and ticket.get('id') == 'INC-1000':
            serial = primary.get('serial')
        refs = links(state, serial)
        if refs and any(ticket.get(k) != v for k, v in refs.items()):
            ticket.update(refs, target_serial=serial)
            changed = True
    return changed
