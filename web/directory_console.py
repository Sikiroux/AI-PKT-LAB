"""Projection de navigation AD : relations de l'entreprise, sans nouveau droit."""

def public_context(state):
    environment = state.get('environment_id', 'legacy')
    registry = state.get('company_registry') or {}
    if registry.get('environment_id') != environment:
        registry = {}
    assets = registry.get('assets', {})
    account_links = {}
    for person in registry.get('people', {}).values():
        if not person.get('represented') or not person.get('account_present'):
            continue
        uid = person['account_id']
        # Les associations multiples sont montrées, jamais remplacées par un prénom.
        entry = account_links.setdefault(uid, {'employees': [], 'assets': []})
        entry['employees'].append({'id': person['id'], 'name': person['display_name']})
        for asset in assets.values():
            if asset.get('represented') and asset.get('employee_id') == person['id']:
                entry['assets'].append({k: asset.get(k) for k in ('id', 'name', 'serial', 'ip')})
    computer_links = {}
    for cid, computer in state['directory'].get('computers', {}).items():
        matches = [a for a in assets.values() if a.get('represented') and a.get('source_role') == computer.get('device_id')]
        if len(matches) == 1:
            asset = matches[0]
            computer_links[cid] = {k: asset.get(k) for k in ('id', 'name', 'serial', 'ip', 'employee_id')}
    return dict(environment_id=environment, company=state['company'],
                account_links=account_links, computer_links=computer_links,
                represented_staff_only=True)


def check_revision(directory, request):
    """Anciennes interfaces compatibles ; la nouvelle console fournit une révision."""
    if 'expected_revision' not in request:
        return
    revision = request['expected_revision']
    if type(revision) is not int or revision != directory['revision']:
        raise ValueError('L’annuaire a changé depuis son affichage. Actualise-le avant cette modification.')
