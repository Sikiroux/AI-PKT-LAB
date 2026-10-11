"""État commun et prérequis du prototype ; aucune réponse réseau inventée."""
import hashlib
import json
import random
import time
from pathlib import Path
import directory_adapter as ad
import directory_incidents
import files_adapter
import file_incidents
import dns_incidents
import mixed_incidents
import technician_model
import desktop_services
import desktop_incidents
import client_workspaces as clients
import company_registry
import company_documents
import sim_inventory

VERSION = 1
from network_proofs import TTL, proof


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
    if state.get('mixed_incident') and action != 'remote':return mixed_incidents.access(state,action,at)
    if state.get('file_incident') and action != 'remote':
        return file_incidents.access(state, action, at)
    if 'file_service' in state and action != 'remote':
        return files_adapter.access(state, action, at)
    if 'directory' in state and action != 'remote':
        return ad.access(state, action, at)
    observation = state.get('observation') or {}
    observation = observation.get('probes', {}).get('remote' if action == 'remote' else 'share', observation)
    fresh = (type(observation.get('at',0)) in (int,float) and observation.get('status') in ('passed', 'failed') and
             0 <= at - observation.get('at', 0) <= TTL)
    net = observation['status'] if fresh else 'unknown'
    if state.get('devices'):
        source='technician' if action=='remote' else 'client'
        target_role='client' if action=='remote' else 'server'
        net=proof(state,'remote' if action=='remote' else 'share',source,state['devices'].get(target_role,{}).get('ip'),at)['status']
    policy = technician_model.policy(state, at) if action == 'remote' else None
    checks = [('service', 'Service de prise en main' if action == 'remote' else 'Service de partage',
               state['remote_service'] if action == 'remote' else state['share_service']),
              ('account', 'Compte actif', (state['directory']['users'][state['directory_user_id']]['enabled'] if 'directory' in state else state['account_enabled']))]
    if action == 'remote':
        # Le transport distant est indépendant du compte Windows du demandeur.
        checks = [check for check in checks if check[0] != 'account']
    if action != 'remote':
        checks.append(('permission', 'Autorisation de lecture' if action == 'read' else 'Autorisation d’écriture',
                       state['read_allowed'] if action == 'read' else state['write_allowed']))
    statuses = []
    parent_ok = net == 'passed'
    if policy is not None:
        status = policy['status'] if parent_ok else 'blocked'
        statuses.append(('technician', 'Accès du technicien : ' + policy['reason'], status))
        parent_ok = parent_ok and policy['allowed']
    for key, label, value in checks:
        status = ('passed' if value else 'failed') if parent_ok else 'blocked'
        statuses.append((key, label, status))
        parent_ok = parent_ok and status == 'passed'
    children = []
    for key, label, status in reversed(statuses):
        children = [result(key, label, status, children)]
    tree = result('network', 'Connectivité ICMP observée dans Packet Tracer (approximation du transport)', net, children)
    return dict(allowed=parent_ok, tree=tree,
                status='passed' if parent_ok else ('unknown' if net == 'unknown' or any(x[2] == 'unknown' for x in statuses) else 'failed'))


class Workspace:
    def __init__(self, path):
        self.path = Path(path)
        self.state = json.loads(self.path.read_text(encoding='utf-8')) if self.path.exists() else None
        if self.state:
            # Une ancienne observation ne prouve rien sur la nouvelle instance PT.
            self.state['observation'] = None
            if self.state.get('local_access'):self.state['local_access']['sessions']={}
            self.state['remote_session'] = False
            self.state['directory_auth'] = None
            self.state['network_observation'] = None
            if 'desktop_services' in self.state:self.state['desktop_services']['ftp']['sessions']={}
            self.state['validated'] = False
            clients.reset_sessions(self.state)
            if 'technician_session' in self.state:self.state['technician_session']['vpn'].update(connected=False,expires_at=0)

    def save(self):
        clients.sync_primary(self.state)
        company_registry.ensure(self.state)
        sim_inventory.ensure(self.state)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp = self.path.with_suffix('.tmp')
        temp.write_text(json.dumps(self.state, ensure_ascii=False, indent=2), encoding='utf-8')
        temp.replace(self.path)

    def workstations(self):
        """Targets are identified by serial, never by an ambiguous display name."""
        s = self.state or {}
        devices = s.get('devices', {})
        client = devices.get('client', {})
        tech = devices.get('technician', {})
        observed = {d.get('serial'): d for d in s.get('observed_workstations', []) if d.get('serial')}
        rows = []
        for role, d in (('client', client), ('technician', tech)):
            if not d: continue
            seen = observed.pop(d.get('serial'), None)
            rows.append(dict(serial=d.get('serial'), name=d['name'], ip=d.get('ip'),
                             user=s.get('requester') if role=='client' else 'Technicien',
                             role=role, simulated=True, ticket_target=role=='client',
                             remote_supported=role=='client',remote_connected=bool(s.get('remote_session')) if role=='client' else False,
                             status=evaluate(s,'remote')['status'] if role=='client' else 'unknown'))
        ticket_serial=(s.get('desktop_incident') or {}).get('target_serial',client.get('serial'))
        for row in rows:row['ticket_target']=row['serial']==ticket_serial and row['role']=='client'
        for serial,profile in ({} if s.get('_client_view') else s.get('client_workspaces',{})).items():
            if serial==client.get('serial'):continue
            seen=observed.pop(serial,None);d=profile['device'];view=clients.project(s,serial)
            rows.append(dict(serial=serial,name=d['name'],ip=d.get('ip'),user=profile['requester'],role='client',
                simulated=True,ticket_target=serial==ticket_serial,remote_supported=True,status=evaluate(view,'remote')['status'],remote_connected=bool(view['remote_session'])))
        for d in observed.values():
            addresses=[p.get('ip') for p in d.get('ports',[]) if p.get('ip') not in (None,'','0.0.0.0')]
            rows.append(dict(serial=d['serial'], name=d['name'], ip=addresses[0] if addresses else None,
                             user=None, role='observed', simulated=False, ticket_target=False,
                             remote_supported=False, status='unknown'))
        for row in rows:
            row.update(company_registry.links(s, row.get('serial')))
            person=(s.get('company_registry') or {}).get('people',{}).get(row.get('employee_id'))
            if person:
                row['user']=person['display_name']
                row['username']=person.get('username')
        return rows

    def public(self):
        if not self.state:
            return None
        s = self.state
        # Les causes et droits internes ne sont pas dévoilés dans le ticket.
        return {k: s[k] for k in ('seed', 'version', 'company', 'requester', 'ticket', 'devices', 'files',
                                 'bound_file', 'remote_session', 'validated')} | {
            'environment_id': s.get('environment_id', 'legacy'),
            'client_serial':s['devices'].get('client',{}).get('serial'),
            'workstations': self.workstations(),
            'workforce': __import__('enterprise_incidents').work_status(s),
            'company_registry': company_registry.public(s),
            'company_documents': company_documents.public(s),
            'directory_incident': directory_incidents.public_incident(s),
            'file_incident': file_incidents.public_incident(s),
            'dns_incident': dns_incidents.public_incident(s),
            'mixed_incident':mixed_incidents.public(s),
            'desktop_incident':desktop_incidents.public(s),
            'desktop_services':desktop_services.public(s),
            'technician':technician_model.public(s),
            'network_file':s.get('network_file'),
            'organization_has_it':s.get('organization_has_it'),
            'documents_dns_name': s.get('documents_dns_name'),
            'files': (files_adapter.names(s) if files_adapter.access(s,'list',time.time())['allowed'] else []) if 'file_service' in s else s['files'],
            'documents_share_id': s.get('documents_share_id'),
            'checks': {a: evaluate(s, a) for a in ('remote', 'read', 'write')},
            'directory_login': ({'username': s['directory']['users'][s['directory_user_id']]['username'], 'authenticated': bool(ad.context(s)['authentication'])} if 'directory' in s else None),
            'monitoring': s.get('monitoring'),
            'network_health': __import__('network_monitor').public_status(s, time.time()),
            'last_known_observation': s.get('last_known_observation'),
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
            # Déconnexion du transport, pas déconnexion Windows.
        elif action == 'connect':
            access = evaluate(s, 'remote')
            if not access['allowed']:
                node = access['tree']
                while node['status'] == 'passed' and node['children']:
                    node = node['children'][0]
                message = node['label'] + (' : non vérifié récemment.' if node['status'] == 'unknown' else ' : accès refusé.')
                if node['id'] == 'network':
                    observation = s.get('observation') or {}
                    probe = observation.get('probes', {}).get('remote', observation)
                    if probe.get('detail'): message += ' ' + probe['detail']
                raise ValueError('Connexion impossible. ' + message)
            s['remote_session'] = True
        elif action in ('read', 'write'):
            if not s['remote_session'] or not evaluate(s, 'remote')['allowed']:
                raise ValueError('Accès distant non disponible pour cette action. Vérifie le réseau ; le bureau et la session utilisateur sont conservés.')
            if not evaluate(s, action)['allowed']:
                raise ValueError('Accès au partage refusé ou connectivité inconnue.')
            if action == 'write' and 'Test.txt' not in s['files']:
                if 'file_service' not in s:s['files'].append('Test.txt')
            if 'file_service' in s:
                import sim_files
                outcome=sim_files.perform_file_action(s['file_service'],(mixed_incidents.request(s,action) if s.get('mixed_incident') else file_incidents.request(s,action) if s.get('file_incident') else files_adapter.request(s,action)),files_adapter.context(s,time.time()),time.time())
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
            if s.get('desktop_incident'):
                if not all(c['status']=='valide' for c in desktop_incidents.checks(s,time.time())):raise ValueError('Résultat de l’application non rétabli.')
                s['validated']=True;self.event('Intervention application vérifiée.');return self.public()
            if s.get('mixed_incident') and not all(c['status']=='valide' for c in mixed_incidents.checks(s,time.time())):raise ValueError('Intervention mixte non rétablie ou contrôle incomplet.')
            if s.get('dns_incident') and not all(c['status']=='valide' for c in dns_incidents.checks(s,time.time())):raise ValueError('DNS, accès fichier ou état préservé non rétabli.')
            if s.get('file_incident') and not all(c['status']=='valide' for c in file_incidents.checks(s,time.time())):
                raise ValueError('Document ciblé ou autres accès non rétablis.')
            if not evaluate(s, 'read')['allowed']:
                raise ValueError('Lecture du partage non rétablie ; ticket non validé.')
            if s.get('directory_incident', {}).get('goal') == 'write' and not evaluate(s, 'write')['allowed']:
                raise ValueError('Écriture du partage non rétablie ; ticket non validé.')
            s['validated'] = True
        else:
            raise ValueError('Action inconnue.')
        self.event('Action : ' + action)
        return self.public()
