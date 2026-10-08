"""Prototype autonome utilisant le même pont que NetOps Lab. Port web 8766."""
import copy
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
import files_adapter
import sim_files
import file_incidents
import dns_adapter
import sim_dns
import dns_incidents
import mixed_incidents
import technician_model
import workspace_links
import client_dialogue
import desktop_services
import desktop_incidents
import desktop_controller

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
        if state and 'directory' in state and 'file_service' not in state:
            backup = workspace.path.with_suffix('.before-files.json')
            if workspace.path.exists() and not backup.exists():backup.write_bytes(workspace.path.read_bytes())
            if files_adapter.ensure(state):workspace.save()

        if state and 'directory' in state and 'dns_service' not in state:
            backup=workspace.path.with_suffix('.before-dns.json')
            if workspace.path.exists() and not backup.exists():backup.write_bytes(workspace.path.read_bytes())
            if dns_adapter.ensure(state):workspace.save()

        if technician_model.ensure(state):workspace.save()
        if state and desktop_services.ensure(state):workspace.save()

    def new(self, seed):
        with self.lock:
            # Construire avant de changer : un échec ne remplace pas la session active.
            ident, path = self.environments.allocate()
            state = build(seed, path.parent / 'network')
            state['environment_id'] = ident
            ad.ensure(state)
            files_adapter.ensure(state)
            dns_adapter.ensure(state)
            technician_model.ensure(state)
            desktop_services.ensure(state)
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
            service_running = state['file_service']['service_status']=='running' if 'file_service' in state else state.get('share_service')
            if not service_running or not state.get('directory_service', True):
                raise ValueError('Rétablis les services avant le nouvel exercice d’annuaire.')
            self.workspace.state = directory_incidents.prepare(state, time.time())
            self.workspace.save()
            if self.on_change:
                self.on_change(self.workspace.state, self.workspace.path.parent)
            return self.workspace.public()

    def next_file_incident(self):
        with self.lock:
            s=self.workspace.state
            if not s:raise ValueError('Crée ou reprends un environnement.')
            now=time.time()
            for source in ('technician','client'):
                n=ad.context(s,source=source,now=now)['network']
                if n['status']!='passed' or not n['observed_at']<=now<=n['valid_until']:
                    raise ValueError('Rétablis et vérifie le réseau du client et du technicien vers le serveur.')
            if not s.get('directory_service',True):raise ValueError('Rétablis le service d’annuaire.')
            self.workspace.state=file_incidents.prepare(s,now)
            self.workspace.save()
            if self.on_change:self.on_change(self.workspace.state,self.workspace.path.parent)
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

    def public_snapshot(self):
        # GET must not wait behind a series of Packet Tracer pings. The cached
        # state is evaluated again at the current time, so expired proofs fail.
        acquired = self.lock.acquire(blocking=False)
        try:
            if acquired:
                self._read_state = copy.deepcopy(self.workspace.state)
            state = getattr(self, '_read_state', None)
            active = self.workspace.state
            if not state or not active or state.get('environment_id') != active.get('environment_id'):
                return None
            view = Workspace.__new__(Workspace)
            view.state = copy.deepcopy(state)
            return view.public()
        finally:
            if acquired: self.lock.release()

    def observe(self, blocking=False):
        # Ne jamais attendre le pont si une action utilisateur l'utilise déjà.
        if not self.lock.acquire(blocking=blocking):
            return
        try:
            s = self.workspace.state
            if not s:
                return
            self._read_state = copy.deepcopy(s)
            with self.engine.lock:
                snapshot=self.engine.snapshot();found = self.identities(snapshot)
                s['observed_workstations'] = [copy.deepcopy(d) for d in snapshot.get('devices', []) if d.get('model') in ('PC-PT','Laptop-PT')]
                client=found['client'];ports=[p for p in client.get('ports',[]) if p.get('name')=='FastEthernet0']
                s['network_observation']=dict(at=time.time(),devices=workspace_links.signature(snapshot,s),client_link=ports[0].get('linked') if ports else None,interfaces={role:[dict(p) for p in device.get('ports',[]) if p.get('name')=='FastEthernet0'] for role,device in found.items()})
                probes = {}
                for key, source, target_role in (('remote', 'technician', 'client'), ('share', 'client', 'server'), ('directory', 'technician', 'server')):
                    target = s['devices'][target_role]['ip']
                    ping = self.engine.ping(found[source]['name'], target)
                    probes[key] = dict(at=time.time(), source='Packet Tracer',
                        status={'valide': 'passed', 'non satisfait': 'failed'}.get(ping['status'], 'unknown'),
                        detail=ping.get('detail', ''), source_device=found[source]['name'], target=target)
                if 'desktop_services' in s:
                    printer=s['desktop_services']['printing']['printer'];target=s['devices'][printer['device_role']]['ip']
                    ping=self.engine.ping(found['client']['name'],target)
                    probes['printing']=dict(at=time.time(),source='Packet Tracer',status={'valide':'passed','non satisfait':'failed'}.get(ping['status'],'unknown'),detail=ping.get('detail',''),source_device=found['client']['name'],target=target)
                outside=s.get('technician_locations',{}).get('outside')
                if outside and (s.get('technician_session') or {}).get('location')=='outside':
                    ping=self.engine.ping(found['technician']['name'],outside['gateway'])
                    probes['vpn_gateway']=dict(at=time.time(),source='Packet Tracer',status={'valide':'passed','non satisfait':'failed'}.get(ping['status'],'unknown'),detail=ping.get('detail',''),source_device=found['technician']['name'],target=outside['gateway'])
            if s.get('technician_session',{}).get('location')=='outside' and probes.get('vpn_gateway',{}).get('status')!='passed':s['technician_session']['vpn'].update(connected=False,expires_at=0)
            statuses = [p['status'] for p in probes.values()]
            status = 'passed' if all(x == 'passed' for x in statuses) else 'unknown' if 'unknown' in statuses else 'failed'
            s['observation'] = dict(at=time.time(), status=status, source='Packet Tracer', probes=probes)
            desktop_services.process_jobs(s,time.time())
            for role, d in found.items():
                s['devices'][role]['name'] = d['name']
            s['bound_file'] = s['network_file']
        except Exception as e:
            s['network_observation']=None
            s['observation'] = dict(at=time.time(), status='unknown', source='Packet Tracer', detail=str(e))
        finally:
            if self.workspace.state:
                if not evaluate(self.workspace.state, 'remote')['allowed']:
                    self.workspace.state['remote_session'] = False
                    if 'directory' in self.workspace.state: ad.invalidate(self.workspace.state)
                if (not all(row['status']=='valide' for row in desktop_incidents.checks(self.workspace.state,time.time())) if self.workspace.state.get('desktop_incident') else not evaluate(self.workspace.state, 'read')['allowed']):
                    self.workspace.state['validated'] = False
                self.workspace.save()
            self._read_state = copy.deepcopy(self.workspace.state)
            self.lock.release()

    def ping(self, target, source='client'):
        if source not in ('client', 'technician'):
            raise ValueError('Poste source inconnu.')
        target = str(ipaddress.ip_address(target))
        with self.lock, self.engine.lock:
            if not self.workspace.state:
                raise ValueError('Génère un environnement.')
            if source=='technician' and self.workspace.state.get('technician_session',{}).get('location')=='outside' and not technician_model.policy(self.workspace.state)['allowed']:
                outside=self.workspace.state.get('technician_locations',{}).get('outside',{})
                if target!=outside.get('gateway'):raise ValueError('Connecte le VPN pour tester les ressources internes depuis l’extérieur.')
            found = self.identities(self.engine.snapshot())
            return self.engine.ping(found[source]['name'], target)

    def action(self, action, target_serial=None):
        with self.lock:
            if action == 'connect' and target_serial is not None:
                client = (self.workspace.state or {}).get('devices', {}).get('client', {})
                if not target_serial or target_serial != client.get('serial'):
                    raise ValueError('Ce poste ne dispose pas d’un bureau distant simulé dans cet environnement.')
            if action == 'reset':
                if not self.workspace.state:
                    raise ValueError('Choisis un environnement.')
                seed = self.workspace.state['seed']
                ident = self.environments.data['active']
                state = build(seed, self.workspace.path.parent / 'network')
                state['environment_id'] = ident
                state['reset_id'] = secrets.token_hex(8)
                ad.ensure(state)
                files_adapter.ensure(state)
                dns_adapter.ensure(state)
                technician_model.ensure(state)
                desktop_services.ensure(state)
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
                files_adapter.sync_catalog(s)
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

    def files(self, action, data):
        with self.lock:
            s=self.workspace.state
            if not s or 'file_service' not in s:raise ValueError('Partages non disponibles.')
            now=time.time()
            if action in ('admin','operation'):
                net=ad.context(s,source='technician',now=now)['network']
                if net['status']!='passed' or not net['observed_at']<=now<=net['valid_until']:
                    raise ValueError('Vérifie la liaison du technicien au serveur.')
                actor=dict(id='technician',environment_id=s.get('environment_id','legacy'),permissions=[sim_files.CAPABILITY_FILES])
                if action=='admin':
                    return dict(service=sim_files.public_file_service(s['file_service'],actor),
                        directory=sim_ad.public_directory(s['directory']),documents_share_id=s['documents_share_id'])
                outcome=sim_files.apply_operation(s['file_service'],data.get('operation'),data.get('payload',{}),actor,now)
                s['file_service']=outcome['service'];s['validated']=False
                self.workspace.event('Partages : '+str(data.get('operation')))
                return {'result':outcome['result']}
            if action!='action':raise ValueError('Action de fichiers inconnue.')
            if not s['remote_session'] or not evaluate(s,'remote')['allowed']:
                s['remote_session']=False;self.workspace.save();raise ValueError('Reconnecte le poste distant.')
            if s.get('desktop_services') and 'documents' not in s['desktop_services']['endpoint']['applications']:return dict(result={'allowed':False,'code':'APPLICATION_MISSING'},revision=s['file_service']['revision'])
            req=data.get('request',{})
            outcome=sim_files.perform_file_action(s['file_service'],req,files_adapter.context(s,now),now)
            if outcome['result']['allowed']:
                s['file_service']=outcome['service'];s['files']=files_adapter.names(s)
                if req.get('action')=='read':
                    import workstation_requests
                    workstation_requests.record(s,'read',req.get('file_id'),now)
                if req.get('action') in ('write','delete'):s['validated']=False
                self.workspace.save()
            return dict(result=files_adapter.presentation(outcome['result']),revision=s['file_service']['revision'])

    def dns(self, action, data):
        with self.lock:
            s=self.workspace.state
            if not s or not dns_adapter.ensure(s) and 'dns_service' not in s:raise ValueError('DNS non disponible.')
            now=time.time();source=data.get('source','client')
            if source not in ('client','technician'):raise ValueError('Poste source inconnu.')
            if action in ('admin','operation'):
                net=ad.context(s,source='technician',now=now)['network']
                if net['status']!='passed' or not net['observed_at']<=now<=net['valid_until']:raise ValueError('Vérifie la liaison du technicien au serveur.')
                actor=dns_adapter.actor(s,admin=True)
                if action=='admin':return dict(service=sim_dns.public_dns(s['dns_service'],actor),documents_dns_name=s['documents_dns_name'])
                outcome=sim_dns.apply_operation(s['dns_service'],data.get('operation'),data.get('payload',{}),actor,now)
                s['validated']=False
            elif action in ('resolve','flush'):
                if source=='client' and (not s['remote_session'] or not evaluate(s,'remote')['allowed']):raise ValueError('Reconnecte le poste distant.')
                if action=='resolve':outcome=sim_dns.resolve(s['dns_service'],source,data.get('query',{}),dns_adapter.context(s,source,now),now)
                else:outcome=sim_dns.flush_cache(s['dns_service'],dns_adapter.actor(s,source),source,now)
            else:raise ValueError('Action DNS inconnue.')
            s['dns_service']=outcome['service'];self.workspace.save()
            return dict(result=outcome['result'])

    def next_dns_incident(self):
        with self.lock:
            s=self.workspace.state
            if not s:raise ValueError('Crée un environnement.')
            now=time.time()
            for source in ('client','technician'):
                n=ad.context(s,source=source,now=now)['network']
                if n['status']!='passed' or not n['observed_at']<=now<=n['valid_until']:raise ValueError('Vérifie le réseau client et technicien vers le serveur.')
            self.workspace.state=dns_incidents.prepare(s,now);self.workspace.save()
            if self.on_change:self.on_change(self.workspace.state,self.workspace.path.parent)
            return self.workspace.public()

    def next_desktop_incident(self,target='random',minutes=30):
        with self.lock:
            s=self.workspace.state
            if not s or 'file_service' not in s:raise ValueError('Crée ou reprends une entreprise complète.')
            now=time.time();net=ad.context(s,'technician',now)['network']
            if net['status']!='passed' or not net['observed_at']<=now<=net['valid_until']:raise ValueError('Vérifie le réseau du technicien avant la préparation.')
            self.workspace.state=desktop_incidents.prepare(s,now,target,minutes);self.workspace.save()
            if self.on_change:self.on_change(self.workspace.state,self.workspace.path.parent)
            return self.workspace.public()

    def desktop(self,path,data):return desktop_controller.handle(self,path,data)

    def next_mixed_incident(self, level=1, target='random', minutes=30):
        with self.lock:
            s=self.workspace.state
            if not s or 'file_service' not in s:raise ValueError('Crée ou reprends un environnement complet.')
            if type(minutes) is not int or not 0<=minutes<=1440:raise ValueError('Durée : 0 à 1440 minutes.')
            now=time.time()
            for source in ('client','technician'):
                n=ad.context(s,source=source,now=now)['network']
                if n['status']!='passed' or not n['observed_at']<=now<=n['valid_until']:raise ValueError('Vérifie le réseau client et technicien avant la préparation.')
            prepared=mixed_incidents.prepare(s,now,level,target)
            incident=prepared['mixed_incident'];incident['timer_minutes']=minutes
            if any(layer=='network' for layer,cause in incident['causes']):
                with self.engine.lock:
                    snapshot=self.engine.snapshot();found=self.identities(snapshot)
                    port=next((p for p in found['client'].get('ports',[]) if p['name']=='FastEthernet0'),None)
                    if not port or not port.get('linked') or not port.get('peer'):raise ValueError('Liaison client lisible et connectée requise.')
                    incident['network_baseline']=workspace_links.signature(snapshot,prepared)
                    incident['cable_before']=dict(port='FastEthernet0',peer=port['peer'])
                    self.workspace.state=prepared;self.workspace.save()
                    try:
                        result=json.loads(self.engine.call(workspace_links.disconnect_js(found['client'],'FastEthernet0',port['peer'])))
                        if not result.get('ok'):raise RuntimeError(result.get('error','Retrait non confirmé.'))
                        current=self.engine.snapshot();after=self.identities(current)
                        p=next(p for p in after['client']['ports'] if p['name']=='FastEthernet0')
                        if p.get('linked') is not False:raise RuntimeError('État du câble non confirmé.')
                        incident['injection_state']='applied'
                    except Exception:
                        incident['injection_state']='uncertain';prepared['observation']=None;prepared['network_observation']=None
                        self.workspace.save()
                        if self.on_change:self.on_change(prepared,self.workspace.path.parent)
                        raise
                prepared['observation']=None;prepared['network_observation']=None
            self.workspace.state=prepared;self.workspace.save()
            if self.on_change:self.on_change(prepared,self.workspace.path.parent)
            return self.workspace.public()

    def confirm_mixed_injection(self):
        with self.lock,self.engine.lock:
            s=self.workspace.state;i=(s or {}).get('mixed_incident')
            if not i or 'cable_before' not in i:raise ValueError('Aucune injection réseau à contrôler.')
            found=self.identities(self.engine.snapshot());p=next((p for p in found['client']['ports'] if p['name']==i['cable_before']['port']),None)
            if not p or p.get('linked') not in (True,False) or p['linked'] and p.get('peer')!=i['cable_before']['peer']:raise ValueError('Liaison absente du diagnostic ou déplacée vers un autre appareil.')
            i['injection_state']='applied';self.workspace.save();return self.workspace.public()

    def technician(self, action, data):
        with self.lock:
            s=self.workspace.state
            if not s:raise ValueError('Crée ou reprends un environnement.')
            technician_model.ensure(s)
            if action=='state':return technician_model.public(s)
            if action in ('vpn-connect','vpn-disconnect'):
                result=technician_model.vpn(s,'connect' if action=='vpn-connect' else 'disconnect',data.get('password',''))
                self.workspace.event('VPN : '+result['code']);return dict(result=result,technician=technician_model.public(s))
            if action not in ('move','confirm'):raise ValueError('Action du portable inconnue.')
            t=s['technician_session']
            if action=='move':
                location=data.get('location');mode=data.get('connection','wired')
                if location not in s.get('technician_locations',{}) or mode not in ('wired','console','none'):raise ValueError('Destination ou raccordement inconnu. Les anciens réseaux doivent être déplacés manuellement dans Packet Tracer.')
                destination=dict(s['technician_locations'][location])
                if mode=='console':destination['port']='Console'
                t['pending']=dict(location=location,connection=mode,destination=destination,at=time.time())
                technician_model.invalidate(s);self.workspace.save()
                with self.engine.lock:
                    found=self.identities(self.engine.snapshot())
                    r=json.loads(self.engine.call(workspace_links.move_js(found['technician'],destination,mode)))
                    if not r.get('ok'):raise ValueError(r.get('error','Raccordement non confirmé.'))
            pending=t.get('pending')
            if not pending:raise ValueError('Aucun raccordement en attente.')
            with self.engine.lock:
                snapshot=self.engine.snapshot();found=self.identities(snapshot);device=found['technician'];dest=pending['destination']
                peer=next((d for d in snapshot['devices'] if d.get('serial')==dest['serial']),None)
                if not peer:raise ValueError('Appareil cible absent.')
                port=next((p for p in device['ports'] if p['name']==('RS232' if pending['connection']=='console' else 'FastEthernet0')),None)
                if pending['connection']=='none':valid=not any(p.get('linked') for p in device['ports'] if p['name'] in ('RS232','FastEthernet0'))
                else:valid=bool(port and port.get('linked') and port.get('peer')==dict(device=peer['name'],port=dest['port']))
                if pending['connection']=='wired':valid=valid and port.get('ip')==dest['ip'] and port.get('mask')==dest['mask']
                if not valid:raise ValueError('Configure le raccordement et l’adresse attendus dans Packet Tracer, puis confirme à nouveau.')
            t.update(location=pending['location'],connection=pending['connection'],pending=None)
            if t['connection']=='wired':s['devices']['technician']['ip']=dest['ip']
            t['history'].append(dict(at=time.time(),location=t['location'],connection=t['connection']));t['history']=t['history'][-30:]
            self.workspace.event('Portable : '+t['location']+' / '+t['connection'])
            return technician_model.public(s)

    def dialogue(self, data):
        with self.lock:
            if not self.workspace.state:raise ValueError('Aucun environnement.')
            row=(desktop_incidents.dialogue(self.workspace.state,data.get('ticket_id'),data.get('question')) if self.workspace.state.get('desktop_incident') else client_dialogue.ask(self.workspace.state,data.get('ticket_id'),data.get('question')))
            self.workspace.save()
            if self.on_change:self.on_change(self.workspace.state,self.workspace.path.parent)
            return dict(answer=row,incident=desktop_incidents.public(self.workspace.state) or mixed_incidents.public(self.workspace.state))


def run():
    # Compatibilité avec l'ancien lanceur : toujours utiliser le serveur unifié.
    from tickets_app import run as unified_run
    unified_run()


if __name__ == '__main__':
    run()
