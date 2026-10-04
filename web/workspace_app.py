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

ROOT = Path(__file__).resolve().parent


class Controller:
    def __init__(self, engine, folder):
        self.engine = engine
        self.folder = Path(folder)
        self.workspace = Workspace(self.folder / 'session.json')
        self.lock = threading.RLock()

    def new(self, seed):
        with self.lock:
            if self.workspace.state:
                raise ValueError('Un environnement existe déjà. Réinitialise-le explicitement.')
            self.workspace.state = build(seed, self.folder / 'network')
            self.workspace.save()
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
                for key, source, target_role in (('remote', 'technician', 'client'), ('share', 'client', 'server')):
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
                if not evaluate(self.workspace.state, 'read')['allowed']:
                    self.workspace.state['validated'] = False
                self.workspace.save()
            self.lock.release()

    def ping(self, target):
        target = str(ipaddress.ip_address(target))
        with self.lock, self.engine.lock:
            if not self.workspace.state:
                raise ValueError('Génère un environnement.')
            found = self.identities(self.engine.snapshot())
            return self.engine.ping(found['client']['name'], target)

    def action(self, action):
        with self.lock:
            if action == 'reset':
                seed = self.workspace.state['seed'] if self.workspace.state else None
                self.workspace.state = None
                self.workspace.path.unlink(missing_ok=True)
                return self.new(seed) if seed else None
            return self.workspace.action(action)


def run():
    # Compatibilité avec l'ancien lanceur : toujours utiliser le serveur unifié.
    from tickets_app import run as unified_run
    unified_run()


if __name__ == '__main__':
    run()
