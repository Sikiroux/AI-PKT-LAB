"""État commun et prérequis du prototype ; aucune réponse réseau inventée."""
import hashlib
import json
import random
import time
from pathlib import Path
import directory_adapter as ad
import directory_incidents
import files_adapter

VERSION = 1
TTL = 45


def generate(seed):
    seed = str(seed).strip()
    if not seed or len(seed) > 128:
        raise ValueError('Seed requise, 128 caractères maximum.')
    def rng(part):
        return random.Random(hashlib.sha256((seed + ':' + part).encode()).hexdigest())
    r = rng('company')
    site = r.choice(('ALB', 'TLS', 'MPL', 'BOR')) + str(r.randint(10, 99))
    user = r.choice(('Camille', 'Nora', 'Samir', 'Hugo', 'Mina'))
    return dict(version=VERSION, seed=seed, site=site, company='Agence ' + site,
                requester=user, address_family=rng('network').choice(('10', '172', '192')),
                network_seed=int(hashlib.sha256((seed + ':network').encode()).hexdigest()[:8], 16),
                devices={}, bound_file=None, anchors={}, observation=None,
                remote_service=True, share_service=True, account_enabled=True,
                read_allowed=False, write_allowed=False, files=['Procedure.txt'],
                remote_session=False, validated=False,
                ticket=f'{user} ne peut plus ouvrir le dossier partagé Documents.', events=[])


def result(key, label, state, children=()):
    return dict(id=key, label=label, status=state, children=list(children))


def evaluate(state, action, at=None):
    if action not in ('remote', 'read', 'write'):
        raise ValueError('Action inconnue.')
    at = time.time() if at is None else at
    if 'file_service' in state and action != 'remote':
        return files_adapter.access(state, action, at)
    if 'directory' in state and action != 'remote':
        return ad.access(state, action, at)
    observation = state.get('observation') or {}
    observation = observation.get('probes', {}).get('remote' if action == 'remote' else 'share', observation)
    fresh = (observation.get('status') in ('passed', 'failed') and
             0 <= at - observation.get('at', 0) <= TTL)
    net = observation['status'] if fresh else 'unknown'
    checks = [('service', 'Service de prise en main' if action == 'remote' else 'Service de partage',
               state['remote_service'] if action == 'remote' else state['share_service']),
              ('account', 'Compte actif', (state['directory']['users'][state['directory_user_id']]['enabled'] if 'directory' in state else state['account_enabled']))]
    if action != 'remote':
        checks.append(('permission', 'Autorisation de lecture' if action == 'read' else 'Autorisation d’écriture',
                       state['read_allowed'] if action == 'read' else state['write_allowed']))
    statuses = []
    parent_ok = net == 'passed'
    for key, label, value in checks:
        status = ('passed' if value else 'failed') if parent_ok else 'blocked'
        statuses.append((key, label, status))
        parent_ok = parent_ok and status == 'passed'
    children = []
    for key, label, status in reversed(statuses):
        children = [result(key, label, status, children)]
    tree = result('network', 'Connectivité ICMP observée dans Packet Tracer (approximation du transport)', net, children)
    return dict(allowed=parent_ok, tree=tree,
                status='passed' if parent_ok else ('unknown' if net == 'unknown' else 'failed'))


class Workspace:
    def __init__(self, path):
        self.path = Path(path)
        self.state = json.loads(self.path.read_text(encoding='utf-8')) if self.path.exists() else None
        if self.state:
            # Une ancienne observation ne prouve rien sur la nouvelle instance PT.
            self.state['observation'] = None
            self.state['remote_session'] = False
            self.state['directory_auth'] = None
            self.state['validated'] = False

    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp = self.path.with_suffix('.tmp')
        temp.write_text(json.dumps(self.state, ensure_ascii=False, indent=2), encoding='utf-8')
        temp.replace(self.path)

    def public(self):
        if not self.state:
            return None
        s = self.state
        # Les causes et droits internes ne sont pas dévoilés dans le ticket.
        return {k: s[k] for k in ('seed', 'version', 'company', 'requester', 'ticket', 'devices', 'files',
                                 'bound_file', 'remote_session', 'validated')} | {
            'environment_id': s.get('environment_id', 'legacy'),
            'directory_incident': directory_incidents.public_incident(s),
            'files': (files_adapter.names(s) if files_adapter.access(s,'list',time.time())['allowed'] else []) if 'file_service' in s else s['files'],
            'documents_share_id': s.get('documents_share_id'),
            'checks': {a: evaluate(s, a) for a in ('remote', 'read', 'write')},
            'directory_login': ({'username': s['directory']['users'][s['directory_user_id']]['username'], 'authenticated': bool(ad.context(s)['authentication'])} if 'directory' in s else None),
            'observation': s['observation'], 'events': s['events'][-30:]}

    def event(self, text):
        self.state['events'].append(dict(at=time.time(), text=text))
        self.save()

    def action(self, action):
        s = self.state
        if not s:
            raise ValueError('Génère un environnement.')
        if action == 'disconnect':
            s['remote_session'] = False
            if 'directory' in s: ad.invalidate(s)
        elif action == 'connect':
            if not evaluate(s, 'remote')['allowed']:
                raise ValueError('Connexion impossible ou réseau non vérifié. Consulte les prérequis.')
            s['remote_session'] = True
        elif action in ('read', 'write'):
            if not s['remote_session'] or not evaluate(s, 'remote')['allowed']:
                s['remote_session'] = False
                raise ValueError('Reconnecte la session distante après vérification réseau.')
            if not evaluate(s, action)['allowed']:
                raise ValueError('Accès au partage refusé ou connectivité inconnue.')
            if action == 'write' and 'Test.txt' not in s['files']:
                if 'file_service' not in s:s['files'].append('Test.txt')
            if 'file_service' in s:
                import sim_files
                outcome=sim_files.perform_file_action(s['file_service'],files_adapter.request(s,action),files_adapter.context(s,time.time()),time.time())
                if not outcome['result']['allowed']:raise ValueError(outcome['result']['code'])
                s['file_service']=outcome['service'];s['files']=files_adapter.names(s)
        elif action == 'grant_read':
            if 'directory' in s: raise ValueError('Utilise la console Annuaire pour modifier les groupes.')
            # Action dans la console d'administration simulée, indépendante de RDP.
            s['read_allowed'] = True
        elif action == 'grant_write':
            if 'directory' in s: raise ValueError('Utilise la console Annuaire pour modifier les groupes.')
            s['write_allowed'] = True
        elif action == 'validate':
            if not evaluate(s, 'read')['allowed']:
                raise ValueError('Lecture du partage non rétablie ; ticket non validé.')
            if s.get('directory_incident', {}).get('goal') == 'write' and not evaluate(s, 'write')['allowed']:
                raise ValueError('Écriture du partage non rétablie ; ticket non validé.')
            s['validated'] = True
        else:
            raise ValueError('Action inconnue.')
        self.event('Action : ' + action)
        return self.public()
