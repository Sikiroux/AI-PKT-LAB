"""Prototype autonome utilisant le même pont que NetOps Lab. Port web 8766."""
import ipaddress
import json
import ntpath
import os
import secrets
import threading
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from diagnostic import Engine
from vendor.live_bridge import PTCommandBridge
from workspace_model import Workspace, evaluate
from workspace_network import build
from environment_store import EnvironmentStore
import directory_adapter as ad
import sim_ad
import directory_incidents

ROOT = Path(__file__).resolve().parent


class Controller:
    def __init__(self, engine, folder):
        self.engine = engine
        self.folder = Path(folder)
        self.environments = EnvironmentStore(self.folder)
        active = self.environments.data['active']
        self.workspace = Workspace(self.environments.path(active) if active else self.folder / 'session.json')
        self.lock = threading.RLock()
        self.on_change = None
        self._migrate_directory(self.workspace)

    def _migrate_directory(self, workspace):
        state = workspace.state
        if state and 'directory' not in state and all(k in state.get('devices',{}) for k in ('client','server','technician')):
            backup = workspace.path.with_suffix('.before-directory.json')
            if workspace.path.exists() and not backup.exists():
                backup.write_bytes(workspace.path.read_bytes())
            if ad.ensure(state): workspace.save()

    def new(self, seed):
        with self.lock:
            # Construire avant de changer : un échec ne remplace pas la session active.
            ident, path = self.environments.allocate()
            state = build(seed, path.parent / 'network')
            state['environment_id'] = ident
            ad.ensure(state)
            candidate = Workspace(path)
            candidate.state = state
            candidate.save()
            self._close_current()
            self.environments.register(ident, path)
            self.workspace = candidate
            if self.on_change:self.on_change(self.workspace.state,self.workspace.path.parent)
            return self.workspace.public()

    def _close_current(self):
        if self.workspace.state:
            self.workspace.state['remote_session'] = False
            self.workspace.state['observation'] = None
            self.workspace.state['validated'] = False
            if 'directory' in self.workspace.state: ad.invalidate(self.workspace.state)
            self.workspace.save()

    def next_directory_incident(self):
        with self.lock:
            state = self.workspace.state
            if not state:
                raise ValueError('Crée ou reprends un environnement.')
            for source in ('technician', 'client'):
                network = ad.context(state, source=source)['network']
                if network['status'] != 'passed' or not network['observed_at'] <= time.time() <= network['valid_until']:
                    raise ValueError('Rétablis et vérifie le réseau du client et du technicien vers le serveur avant le nouvel incident.')
            if not state.get('share_service') or not state.get('directory_service', True):
                raise ValueError('Rétablis les services avant le nouvel exercice d’annuaire.')
            self.workspace.state = directory_incidents.prepare(state, time.time())
            self.workspace.save()
            if self.on_change:
                self.on_change(self.workspace.state, self.workspace.path.parent)
            return self.workspace.public()

    def select(self, ident):
        with self.lock:
            candidate = Workspace(self.environments.path(ident))
            if not candidate.state:
                raise ValueError('Sauvegarde vide.')
            self._close_current()
            candidate.state['environment_id'] = ident
            self._migrate_directory(candidate)
            candidate.save()
            self.environments.activate(ident)
            self.workspace = candidate
            if self.on_change:self.on_change(self.workspace.state,self.workspace.path.parent)
            return self.workspace.public()

    def identities(self, snapshot):
        s = self.workspace.state
        actual = snapshot.get('saved_filename')
        if not actual or ntpath.normcase(ntpath.normpath(actual)) != ntpath.normcase(ntpath.normpath(s['network_file'])):
            raise ValueError('Ouvre entreprise.pkt de cette session et enregistre-le au même emplacement.')
        found = {}
        for role, expected in s['devices'].items():
            matches = [d for d in snapshot['devices'] if d.get('serial') == expected['serial']]
            if len(matches) != 1:
                raise ValueError('Identité absente ou ambiguë : ' + role)
            found[role] = matches[0]
        return found

    def observe(self, blocking=False):
        # Ne jamais attendre le pont si une action utilisateur l'utilise déjà.
        if not self.lock.acquire(blocking=blocking):
            return
        try:
            s = self.workspace.state
            if not s:
                return
            with self.engine.lock:
                found = self.identities(self.engine.snapshot())
                probes = {}
                for key, source, target_role in (('remote', 'technician', 'client'), ('share', 'client', 'server'), ('directory', 'technician', 'server')):
                    target = s['devices'][target_role]['ip']
                    ping = self.engine.ping(found[source]['name'], target)
                    probes[key] = dict(at=time.time(), source='Packet Tracer',
                        status={'valide': 'passed', 'non satisfait': 'failed'}.get(ping['status'], 'unknown'),
                        detail=ping.get('detail', ''), source_device=found[source]['name'], target=target)
            statuses = [p['status'] for p in probes.values()]
            status = 'passed' if all(x == 'passed' for x in statuses) else 'unknown' if 'unknown' in statuses else 'failed'
            s['observation'] = dict(at=time.time(), status=status, source='Packet Tracer', probes=probes)
            for role, d in found.items():
                s['devices'][role]['name'] = d['name']
            s['bound_file'] = s['network_file']
        except Exception as e:
            s['observation'] = dict(at=time.time(), status='unknown', source='Packet Tracer', detail=str(e))
        finally:
            if self.workspace.state:
                if not evaluate(self.workspace.state, 'remote')['allowed']:
                    self.workspace.state['remote_session'] = False
                    if 'directory' in self.workspace.state: ad.invalidate(self.workspace.state)
                if not evaluate(self.workspace.state, 'read')['allowed']:
                    self.workspace.state['validated'] = False
                self.workspace.save()
            self.lock.release()

    def ping(self, target, source='client'):
        if source not in ('client', 'technician'):
            raise ValueError('Poste source inconnu.')
        target = str(ipaddress.ip_address(target))
        with self.lock, self.engine.lock:
            if not self.workspace.state:
                raise ValueError('Génère un environnement.')
            found = self.identities(self.engine.snapshot())
            return self.engine.ping(found[source]['name'], target)

    def action(self, action):
        with self.lock:
            if action == 'reset':
                if not self.workspace.state:
                    raise ValueError('Choisis un environnement.')
                seed = self.workspace.state['seed']
                ident = self.environments.data['active']
                state = build(seed, self.workspace.path.parent / 'network')
                state['environment_id'] = ident
                state['reset_id'] = secrets.token_hex(8)
                ad.ensure(state)
                self.workspace.state = state
                self.workspace.save()
                if self.on_change:self.on_change(self.workspace.state,self.workspace.path.parent)
                return self.workspace.public()
            if action in ('grant_read','grant_write') and 'directory' in (self.workspace.state or {}):
                s = self.workspace.state
                right = 'read' if action == 'grant_read' else 'write'
                return self.directory('operation', {'operation':'add_group_member','payload':{'group_id':s['directory_resource']['allowed_group_ids'][right][0], 'user_id':s['directory_user_id']}})
            return self.workspace.action(action)

    def directory(self, action, data):
        with self.lock:
            s = self.workspace.state
            if not s or 'directory' not in s: raise ValueError('Annuaire non disponible pour cet environnement.')
            now = time.time()
            if action in ('state','operation'):
                ctx = ad.context(s, 'technician', now)
                n = ctx['network']
                if n['status'] != 'passed' or not n['observed_at'] <= now <= n['valid_until'] or ctx['directory_service'] != 'running':
                    raise ValueError('Annuaire inaccessible depuis le technicien. Vérifie le réseau maintenant.')
                if action == 'state':
                    return {'directory':sim_ad.public_directory(s['directory']), 'requester_id':s['directory_user_id'], 'resource':s['directory_resource']}
                outcome = sim_ad.apply_operation(s['directory'], data.get('operation'), data.get('payload',{}), ad.actor(s), now)
                s['directory'] = outcome['directory']
                ad.invalidate(s)
                self.workspace.event('Annuaire : '+str(data.get('operation')))
                return {'result':outcome['result']}
            if action not in ('login','change-password','logout'):raise ValueError('Action annuaire inconnue.')
            if action == 'logout':
                ad.invalidate(s);self.workspace.save();return {'result':{'code':'LOGGED_OUT','allowed':False}}
            if not s['remote_session'] or not evaluate(s,'remote')['allowed']:
                ad.invalidate(s);self.workspace.save();raise ValueError('Ouvre une session distante connectée avant l’authentification utilisateur.')
            # Ce bureau représente le demandeur du ticket ; le navigateur ne choisit pas son identité.
            username = s['directory']['users'][s['directory_user_id']]['username']
            if action == 'login':
                outcome = sim_ad.authenticate(s['directory'], username, data.get('password',''), ad.context(s,now=now), now)
            else:
                outcome = sim_ad.change_password(s['directory'], username, data.get('old_password',''), data.get('new_password',''), ad.context(s,now=now), now)
            s['directory'] = outcome['directory'];ad.invalidate(s)
            if outcome['result']['allowed']:
                s['directory_auth'] = dict(user_id=s['directory_user_id'],status='authenticated',environment_id=s.get('environment_id','legacy'),source_device_id='client',expires_at=now+1800)
            self.workspace.event('Connexion utilisateur : '+outcome['result']['code'])
            return {'result':outcome['result']}


def run():
    # Compatibilité avec l'ancien lanceur : toujours utiliser le serveur unifié.
    from tickets_app import run as unified_run
    unified_run()


if __name__ == '__main__':
    run()
