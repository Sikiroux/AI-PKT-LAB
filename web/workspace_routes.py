"""Routes du bureau avec le pont et le jeton du serveur principal."""
import mimetypes
import os
from urllib.parse import urlsplit
from pathlib import Path

ROOT = Path(__file__).resolve().parent

class WorkspaceRoutes:
    def __init__(self, controller, token):
        self.controller, self.token = controller, token

    def get(self, handler):
        path = urlsplit(handler.path).path
        if path in ('/workspace', '/workspace/desktop', '/workspace/technician'):
            name = 'workspace.html' if path == '/workspace' else 'desktop.html'
            html = (ROOT / name).read_text(encoding='utf-8')
            html = html.replace('__TECHNICIAN__', 'true' if path == '/workspace/technician' else 'false')
            html = html.replace('__TOKEN__', self.token).replace('__API_BASE__', '/workspace')
            handler.send(200, html, 'text/html')
        elif path == '/workspace/environments':
            with self.controller.lock:
                handler.send(200, self.controller.environments.public())
        elif path == '/workspace/state':
            handler.send(200, self.controller.public_snapshot())
        elif path.startswith('/osjs/'):
            name = path.removeprefix('/osjs/')
            allowed = {'main.js', 'main.css', 'LICENSE',
                       '881c86876af63b732063d7bdd51bb226.png', 'f4cfc6708cf6bfc17d4b1e775f594ae2.png'}
            if name not in allowed:
                handler.send(404, {'error': 'Ressource inconnue'})
            else:
                body = (ROOT / 'vendor' / 'osjs' / name).read_bytes()
                handler.send_response(200)
                handler.send_header('Content-Type', mimetypes.guess_type(name)[0] or 'application/octet-stream')
                handler.send_header('Content-Length', str(len(body)))
                handler.end_headers()
                handler.wfile.write(body)
        else:
            return False
        return True

    def post(self, handler, data):
        if not handler.path.startswith('/workspace/'):
            return False
        with self.controller.lock:
            return self._post_locked(handler, data)

    def _post_locked(self, handler, data):
        if not handler.path.startswith('/workspace/'):
            return False
        c = self.controller
        action = handler.path.removeprefix('/workspace/')
        # Creating/selecting an environment deliberately changes the active context.
        if 'environment_id' in data and action not in ('new', 'select') and c.workspace.state:
            with c.lock:
                active = (c.workspace.state or {}).get('environment_id', 'legacy')
                if data['environment_id'] != active:
                    raise ValueError('Cet accès distant appartient à un autre environnement. Reconnecte-toi.')
        if action == 'new': result = c.new(data.get('seed', ''))
        elif action=='desktop-incident' or action.startswith('desktop/'):
            if data.get('environment_id') != (c.workspace.state or {}).get('environment_id','legacy'):raise ValueError('Environnement actif requis.')
            result=c.next_desktop_incident(data.get('target','random'),data.get('minutes',30)) if action=='desktop-incident' else c.desktop(action.removeprefix('desktop/'),data)
        elif action == 'directory-incident':
            if data.get('environment_id') != (c.workspace.state or {}).get('environment_id', 'legacy'):
                raise ValueError('Environnement actif requis.')
            result = c.next_directory_incident()
        elif action == 'file-incident':
            if data.get('environment_id') != (c.workspace.state or {}).get('environment_id','legacy'):
                raise ValueError('Environnement actif requis.')
            result = c.next_file_incident()
        elif action in ('mixed-incident','mixed-confirm','dialogue') or action.startswith('technician/'):
            if data.get('environment_id') != (c.workspace.state or {}).get('environment_id','legacy'):raise ValueError('Environnement actif requis.')
            if action=='mixed-incident':result=c.next_mixed_incident(data.get('level',1),data.get('target','random'),data.get('minutes',30))
            elif action=='mixed-confirm':result=c.confirm_mixed_injection()
            elif action=='dialogue':result=c.dialogue(data)
            else:result=c.technician(action.removeprefix('technician/'),data)
        elif action == 'dns-incident':
            if data.get('environment_id') != (c.workspace.state or {}).get('environment_id','legacy'):raise ValueError('Environnement actif requis.')
            result=c.next_dns_incident()
        elif action.startswith('dns/'):
            if data.get('environment_id') != (c.workspace.state or {}).get('environment_id','legacy'):raise ValueError('Environnement actif requis.')
            result=c.dns(action.removeprefix('dns/'),data)
        elif action == 'select': result = c.select(data.get('id'))
        elif action == 'refresh':
            c.observe(blocking=True)
            with c.lock: result = c.workspace.public()
        elif action.startswith('directory/'):
            if data.get('environment_id') != (c.workspace.state or {}).get('environment_id','legacy'):
                raise ValueError('Environnement actif requis.')
            result = c.directory(action.removeprefix('directory/'), data)
        elif action.startswith('files/'):
            if data.get('environment_id') != (c.workspace.state or {}).get('environment_id','legacy'):
                raise ValueError('Environnement actif requis.')
            result = c.files(action.removeprefix('files/'),data)
        elif action == 'action': result = c.action(data['action'], target_serial=data.get('target_serial'))
        elif action == 'ping':
            if data.get('source', 'client') not in ('client', 'technician'):
                raise ValueError('Poste source inconnu.')
            result = c.ping(data['target'], source='technician') if data.get('source') == 'technician' else c.ping(data['target'])
        elif action == 'open':
            with c.lock:
                if not c.workspace.state: raise ValueError('Génère un environnement.')
                path = c.workspace.state['network_file']
            if os.name != 'nt': raise ValueError('Ouvre manuellement le fichier affiché dans Packet Tracer.')
            os.startfile(path)
            result = {'message': 'Ouverture demandée à Windows.'}
        else:
            handler.send(404, {'error': 'Action inconnue'})
            return True
        handler.send(200, result)
        return True
