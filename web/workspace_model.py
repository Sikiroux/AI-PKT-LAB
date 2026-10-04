"""État commun et prérequis du prototype ; aucune réponse réseau inventée."""
import hashlib
import json
import random
import time
from pathlib import Path

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
    observation = state.get('observation') or {}
    observation = observation.get('probes', {}).get('remote' if action == 'remote' else 'share', observation)
    fresh = (observation.get('status') in ('passed', 'failed') and
             0 <= at - observation.get('at', 0) <= TTL)
    net = observation['status'] if fresh else 'unknown'
    checks = [('service', 'Service de prise en main' if action == 'remote' else 'Service de partage',
               state['remote_service'] if action == 'remote' else state['share_service']),
              ('account', 'Compte actif', state['account_enabled'])]
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
            'checks': {a: evaluate(s, a) for a in ('remote', 'read', 'write')},
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
                s['files'].append('Test.txt')
        elif action == 'grant_read':
            # Action dans la console d'administration simulée, indépendante de RDP.
            s['read_allowed'] = True
        elif action == 'grant_write':
            s['write_allowed'] = True
        elif action == 'validate':
            if not evaluate(s, 'read')['allowed']:
                raise ValueError('Lecture du partage non rétablie ; ticket non validé.')
            s['validated'] = True
        else:
            raise ValueError('Action inconnue.')
        self.event('Action : ' + action)
        return self.public()
