"""NetOps Lab local — tickets persistants, Python standard uniquement."""
import ipaddress
import json, os, secrets, threading, time, webbrowser, shutil, ntpath
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from diagnostic import Engine, checks, ROOT
from vendor.live_bridge import PTCommandBridge
from console_tools import CLEAN_JS, cleaned
from generator_app import Generator
from workspace_app import Controller
from workspace_routes import WorkspaceRoutes
import timers
import re
import live_faults,vlan_faults
import site_services
from service_desk import ServiceDesk
from urllib.parse import urlparse,parse_qs

LINK_JS = r'''try {var d=ipc.network().getDevice("SW1"),p=d.getPort("FastEthernet0/1"),l=p.getLink();var a=l.getPort1(),b=l.getPort2();reportResult(JSON.stringify({ends:[{device:a.getOwnerDevice().getName(),port:a.getName()},{device:b.getOwnerDevice().getName(),port:b.getName()}]}));}catch(e){reportResult(JSON.stringify({error:String(e)}));}'''

def now(): return time.strftime('%Y-%m-%d %H:%M:%S')
def device(snapshot, name):
    matches=[d for d in snapshot['devices'] if d['name']==name]
    if len(matches)!=1: raise ValueError('Equipement absent ou nom ambigu : '+name)
    return matches[0]

class Tickets:
    def __init__(self, engine, path):
        self.engine=engine; self.path=Path(path)
        self.open_target=None
        self.desk=None
        self.readiness={'status':'non_verifie','message':'Réseau à vérifier'}
        self.state=json.loads(self.path.read_text(encoding='utf-8')) if self.path.exists() else {'site':None,'tickets':[],'events':[]}
        interrupted=False
        for t in self.state['tickets']:
            if t.get('injection',{}).get('state')=='pending':
                t['injection']['state']='uncertain';t['status']='a_controler';interrupted=True
        if interrupted:self.save()
    def bind_environment(self, state, folder, generator, controller):
        if self.desk:
            self.desk.settings.update(active=False, next_at=None)
            self.save()
        path = Path(folder) / 'tickets.json'
        fresh = Tickets(self.engine, path)
        if state.get('reset_id') and (fresh.state.get('site') or {}).get('reset_id')!=state['reset_id']:
            if path.exists():shutil.copy2(path,path.with_name('tickets-before-reset-'+state['reset_id']+'.json'))
            fresh.state={'site':None,'tickets':[],'events':[]}
        self.__dict__.update(fresh.__dict__)
        self.controller = controller
        client = state['devices']['client']
        self.state['site'] = self.state.get('site') or dict(devices=[dict(name=d['name'], serial=d['serial']) for d in state['devices'].values()], inventory=[])
        self.state['site'].update(name=state['company'], file=state['network_file'], environment_id=state.get('environment_id','legacy'),
            reset_id=state.get('reset_id'), profile=dict(switch=state['expected_cable']['peer'], server=state['devices']['server']['ip'],
                         network=str(ipaddress.ip_network(client['ip']+'/24',strict=False)), client=client['name'], site=state['site'], ap=None))
        if not any(t['kind']=='workspace' for t in self.state['tickets']):
            self.state['tickets'].append(dict(id='INC-1000', kind='workspace', name=client['name'], title='Documents partagés inaccessibles',
                description=state['ticket']+' Poste concerné : '+client['name']+'. Rétablis le réseau puis l’accès en lecture depuis le bureau distant.',
                status='nouveau', severity='moderee', created=now(), checks=[], complete=False, notes=''))
        incident = state.get('directory_incident')
        if incident and not any(t['id'] == incident['id'] for t in self.state['tickets']):
            self.state['tickets'].append(dict(id=incident['id'], kind='workspace', name=client['name'],
                title=incident['title'], description=incident['description'], workspace_goal=incident['goal'],
                status='nouveau', severity='moderee', created=now(), checks=[], complete=False, notes=''))
        self.desk = ServiceDesk(self, generator)
        self.desk.settings.update(source='site',active=False,next_at=None)
        self.save()

    def profile(self, key):
        defaults = dict(switch='SW1',server='192.168.50.10',network='192.168.50.0/24',client='PC-ADMIN',ap='AP1',site='AG1')
        return (self.state.get('site') or {}).get('profile',{}).get(key,defaults[key])

    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp=self.path.with_suffix('.tmp')
        temp.write_text(json.dumps(self.state,ensure_ascii=False,indent=2),encoding='utf-8');os.replace(temp,self.path)
    def event(self,text): self.state['events'].append({'date':now(),'text':text});self.save()
    def public(self):
        return {'site':{'name':self.state['site'].get('name','Agence de test'),'environment_id':self.state['site'].get('environment_id'),'profile':self.state['site'].get('profile',{}),'devices':len(self.state['site']['devices']),'file':self.state['site'].get('file'),'ready':self.readiness,'inventory':self.state['site'].get('inventory',[]),'inventory_at':self.state['site'].get('inventory_at'),'service_capabilities':self.state['site'].get('service_capabilities',[])} if self.state['site'] else None,
                'tickets':[{k:v for k,v in t.items() if k not in ('baseline','injection','service_scenario','procedural')} for t in self.state['tickets']],
                'session':self.desk.public() if self.desk else None,'service_jobs':self.desk.g.jobs() if self.desk else [],'console_diagnostic':self.state.get('console_diagnostic'),'events':self.state['events'][-40:]}
    def check_file(self,snapshot,expected):
        actual=snapshot.get('saved_filename')
        if not actual:raise ValueError('Le pont ne confirme pas le nom du fichier ouvert.')
        if ntpath.normcase(ntpath.normpath(actual))!=ntpath.normcase(ntpath.normpath(expected)):
            raise ValueError('Le fichier actuellement ouvert ne correspond pas au fichier de travail associé.')
    def guard(self,snapshot):
        if not self.state['site']:raise ValueError('Enregistre d’abord le site de test.')
        if self.open_target:self.check_file(snapshot,self.open_target)
        elif self.state['site'].get('file'):self.check_file(snapshot,self.state['site']['file'])
        for old in self.state['site']['devices']:
            if device(snapshot,old['name']).get('serial')!=old['serial']:raise ValueError('Le reseau ouvert ne correspond plus au site enregistre. Rouvre le bon fichier Packet Tracer.')
    def register(self):
        if self.state['site']:raise ValueError('Site deja enregistre. Il est conserve apres redemarrage.')
        s=self.engine.snapshot()
        names=['R1','SW1','AP1','PC-ADMIN','SRV-WEB'];anchors=[]
        for name in names:
            d=device(s,name)
            if not d.get('serial'):raise ValueError('Identite non disponible : '+name)
            anchors.append({'name':name,'serial':d['serial']})
        if device(s,self.profile('switch'))['model']!='2960-24TT':raise ValueError('Utilise le reseau-test.pkt fourni.')
        self.state['site']={'devices':anchors,'file':s.get('saved_filename') if s.get('saved_filename') and ntpath.isabs(s['saved_filename']) else None};self.remember_inventory(s);self.event('Site de test enregistre.')
    def remember_inventory(self,snapshot):
        site=self.state['site']
        previous={d['serial']:d for d in site.get('inventory',[]) if d.get('serial')}
        inventory=[];seen=set()
        for d in snapshot['devices']:
            serial=d.get('serial')
            if not serial:continue
            if serial in seen:raise ValueError('Inventaire ambigu : numéro de série dupliqué.')
            seen.add(serial);old=previous.get(serial,{})
            inventory.append(dict(name=d['name'],serial=serial,model=d.get('model'),
                ports=d.get('ports',[]),present=True,first_seen=old.get('first_seen',now()),last_seen=now()))
        inventory.extend(dict(d,present=False) for serial,d in previous.items() if serial not in seen)
        site['inventory']=inventory;site['inventory_at']=now();self.save()
    def sync_inventory(self):
        snapshot=self.engine.snapshot();self.guard(snapshot);self.remember_inventory(snapshot)
        self.event('Inventaire du site actualisé ; appareils absents conservés dans l’historique.')
        return self.public()
    def next_device_name(self,kind,snapshot):
        base=(self.profile('site')+'-PC-USR' if kind=='pc' else self.profile('site')+'-LT-USR') if self.state['site'].get('profile') else ('PC-NOUVEAU' if kind=='pc' else 'LAPTOP-WIFI')
        used={d['name'] for d in snapshot['devices']}
        used.update(d['name'] for d in self.state['site'].get('inventory',[]))
        used.update(t.get('name') for t in self.state['tickets'])
        if base not in used:return base
        index=2
        while base+'-'+str(index).zfill(2) in used:index+=1
        return base+'-'+str(index).zfill(2)
    def endpoint(self,name):
        # Discover the port attached to a known wired PC; never target a trunk/uplink.
        code=r'''try {var d=ipc.network().getDevice(NAME),p=d.getPort("FastEthernet0"),l=p.getLink();var a=l.getPort1(),b=l.getPort2();reportResult(JSON.stringify({ends:[{device:a.getOwnerDevice().getName(),port:a.getName()},{device:b.getOwnerDevice().getName(),port:b.getName()}]}));}catch(e){reportResult(JSON.stringify({error:String(e)}));}'''.replace('NAME',json.dumps(name))
        link=json.loads(self.engine.call(LINK_JS if name=='PC-ADMIN' and self.profile('switch')=='SW1' else code))
        ends=link.get('ends',[])
        if len(ends)!=2 or not any(e.get('device')==name and e.get('port')=='FastEthernet0' for e in ends):raise ValueError('Le poste doit être directement câblé à SW1.')
        matches=[e for e in ends if e.get('device')==self.profile('switch') and re.fullmatch(r'(FastEthernet|GigabitEthernet)0/[0-9]+',e.get('port',''))]
        if len(matches)!=1:raise ValueError('Liaison non prise en charge : poste directement relié à SW1 requis.')
        return matches[0]['port']
    def set_port(self,port,up):
        if not re.fullmatch(r'(FastEthernet|GigabitEthernet)0/[0-9]+',port):raise ValueError('Port invalide.')
        command='enable\nconfigure terminal\ninterface '+port+'\n'+('no shutdown' if up else 'shutdown')+'\nend'
        return self.engine.call('configureIosDevice('+json.dumps(self.profile('switch'))+', '+json.dumps(command)+');reportResult("ok");')
    def get(self,ident):
        return next(t for t in self.state['tickets'] if t['id']==ident)
    def attach(self,path):
        if not self.state['site']:raise ValueError('Enregistre le site avant de lui associer une sauvegarde.')
        p=Path(path).expanduser()
        if not p.is_absolute() or p.suffix.lower() not in ('.pkt','.pka') or not p.is_file():raise ValueError('Indique le chemin complet d’un fichier .pkt ou .pka existant.')
        snapshot=self.engine.snapshot()
        previous=self.state['site'].get('file');previous_target=self.open_target;self.state['site']['file']=None;self.open_target=None
        try:self.guard(snapshot)
        finally:self.state['site']['file']=previous;self.open_target=previous_target
        self.check_file(snapshot,str(p.resolve()))
        self.open_target=None;self.state['site']['file']=str(p.resolve())
        if self.state['site'].get('environment_id'):
            self.controller.workspace.state.update(network_file=str(p.resolve()),bound_file=None,observation=None,remote_session=False,validated=False)
            self.controller.workspace.save()
        self.event('Fichier de travail associé au site.')
        self.readiness={'status':'non_verifie','message':'Fichier associé ; son contenu sera contrôlé après ouverture.'}
    def open_network(self):
        if os.name!='nt':raise ValueError('L’ouverture automatique est prévue pour Windows dans cette version.')
        if self.state['site']:
            file=self.state['site'].get('file')
            if not file:raise ValueError('Associe ta sauvegarde Packet Tracer dans Site de test avant de l’ouvrir.')
            p=Path(file)
        else:
            folder=ROOT/'travail';folder.mkdir(exist_ok=True);p=folder/'agence.pkt'
            if not p.exists():shutil.copy2(ROOT/'reseau-test.pkt',p)
        if p.suffix.lower() not in ('.pkt','.pka') or not p.is_file():raise ValueError('Fichier de travail introuvable.')
        os.startfile(str(p))
        self.open_target=str(p)
        self.readiness={'status':'attente','message':'Ouverture demandée. Attente du pont et du contrôle du site.'}
        return {'file':str(p),'message':'Ouverture demandée ; attends le contrôle de connexion.'}
    def ready(self):
        if not self.engine.bridge.is_connected:
            self.readiness={'status':'attente','message':'En attente de MCP BUILDER…'}
        else:
            try:
                s=self.engine.snapshot()
                if self.open_target:self.check_file(s,self.open_target)
                if self.state['site']:self.guard(s)
                else:
                    for name in ('R1','SW1','AP1','PC-ADMIN','SRV-WEB'):device(s,name)
                self.open_target=None
                self.readiness={'status':'pret','message':'Pont connecté et équipements du site reconnus.'}
            except Exception:
                self.readiness={'status':'mauvais_reseau','message':'Réseau non reconnu ou lecture incomplète. Ouvre le fichier du site et réessaie.'}
        return self.readiness
    def new(self,kind,trace_mode='hidden',target=None,fault='port_down'):
        if fault not in (*live_faults.KINDS,'vlan_wrong','random'):raise ValueError('Panne inconnue.')
        if trace_mode not in ('hidden','technician'):raise ValueError('Mode de traces inconnu')
        if kind not in ('incident','pc','wifi'):raise ValueError('Type inconnu')
        if any(t['kind']==kind and t['status']!='clos' for t in self.state['tickets']):raise ValueError('Un ticket de ce type est deja ouvert.')
        if kind=='incident' and fault=='vlan_wrong' and trace_mode!='technician':raise ValueError('La panne VLAN exige le mode traces visibles : aucune lecture/modification VLAN sans historique CLI n’est confirmée par ce pont.')
        if self.state['site'].get('profile') and kind=='wifi':raise ValueError('Cet environnement ne comporte pas encore de point d’accès Wi-Fi configuré.')
        if self.state['site'].get('profile') and fault=='vlan_wrong':raise ValueError('Panne VLAN à adapter aux switches procéduraux avant activation.')
        s=self.engine.snapshot();self.guard(s)
        self.remember_inventory(s)
        name=(target or self.profile('client')) if kind=='incident' else self.next_device_name(kind,s)
        if kind=='incident':
            candidate=device(s,name)
            known=next((d for d in self.state['site']['inventory'] if d['name']==name and d.get('present')),None)
            if not known or candidate.get('model')!='PC-PT':raise ValueError('Choisis un PC filaire présent dans l’inventaire du site.')
        if kind=='incident':
            incident_port=self.endpoint(name)
            p=next(p for p in device(s,self.profile('switch'))['ports'] if p['name']==incident_port)
            if not p['up'] or not p['protocol_up']:raise ValueError('Le poste doit fonctionner avant de creer un incident.')
            mutation=vlan_faults.plan(self.engine,incident_port) if fault=='vlan_wrong' else live_faults.plan(candidate,fault,s,int(time.time_ns()%10**9),target=self.profile('server'))
            if self.engine.ping(name,self.profile('server'))['status']!='valide':raise ValueError('Le ping initial echoue ou reste incertain. Reessaie quand le reseau fonctionne.')
        if kind=='incident' and trace_mode=='hidden' and mutation['kind']=='port_down':
            report=self.clean_console()
            if not cleaned(report):raise ValueError('Injection bloquée : effacement de la console et de l’historique non confirmé. Ouvre Site de test pour consulter le diagnostic. Le mode traces visibles est réservé au scénario d’erreur humaine.')
        t={'id':('INC-' if kind=='incident' else 'DEM-')+str(1001+len(self.state['tickets'])), 'kind':kind,'name':name,
           'title':{'incident':name+' ne rejoint plus le serveur','pc':'Installer un poste pour un nouvel arrivant','wifi':'Connecter le portable au reseau de l’agence'}[kind],
           'description':{'incident':'Le service IT signale une perte d’accès au serveur 192.168.50.10 depuis PC-ADMIN. Diagnostique puis rétablis la communication.',
           'pc':'Ajoute un PC nommé PC-NOUVEAU, raccorde-le au réseau 192.168.50.0/24 et vérifie son accès au serveur 192.168.50.10. Une adresse obtenue par DHCP convient.',
           'wifi':'Ajoute un portable nommé LAPTOP-WIFI avec une carte compatible (WPC300N selon le modèle). Connecte-le au SSID ouvert Agence-Lab, sans câble réseau. Il doit obtenir une adresse 192.168.50.0/24 et joindre 192.168.50.10.'}[kind],
           'trace_mode':trace_mode,'severity':'moderee' if kind=='incident' else 'faible','impact':'Un poste concerné' if kind=='incident' else 'Demande planifiée','status':'nouveau','created':now(),'baseline':s,'checks':[],'complete':False,'notes':'','manual_ssid':False}
        if kind=='incident':t['description']=name+' signale une perte d’accès au serveur 192.168.50.10. Diagnostique puis rétablis la communication en préservant les autres postes.'
        if kind=='incident' and mutation.get('kind')=='vlan_wrong':t['description']+=' Le port doit rester dans le VLAN d’accès '+str(mutation['before_vlan'])+' prévu pour ce poste.'
        if kind=='incident' and mutation.get('before'):
            t['description']+=' Le plan d’adressage prévoit '+mutation['before']['ip']+' avec le masque '+mutation['before']['mask']+' pour ce poste.'
        elif kind=='pc':t['description']=t['description'].replace('PC-NOUVEAU',name)
        else:t['description']=t['description'].replace('LAPTOP-WIFI',name)
        t['description']=t['description'].replace('192.168.50.10',self.profile('server')).replace('192.168.50.0/24',self.profile('network'))
        self.state['tickets'].append(t);self.event(t['id']+' : ticket cree.')
        if kind=='incident':
            t['injection']={'device':self.profile('switch'),'switch_port':incident_port,'port':incident_port,'target_serial':candidate['serial'],'before_up':True,'state':'pending',**mutation};self.save()
            try:
                if self.apply_fault(t,False)!='ok':raise RuntimeError('Injection sans confirmation')
                time.sleep(.5)
                current=self.engine.snapshot();self.guard(current)
                p=next(p for p in device(current,self.profile('switch'))['ports'] if p['name']==incident_port)
                if not self.fault_matches(t,current,False):raise RuntimeError('Modification non confirmée')
                failure=self.engine.ping(name,self.profile('server'))
                if failure['status']!='non satisfait':
                    if self.apply_fault(t,True)!='ok':raise RuntimeError('Rétablissement non confirmé')
                    restored=self.engine.snapshot();self.guard(restored)
                    if not self.fault_matches(t,restored,True):raise RuntimeError('Rétablissement incomplet')
                    self.cleanup(t);t['injection']['state']='restored';t['status']='a_controler';self.save()
                    raise RuntimeError('La panne ne produit pas un échec de communication confirmé.')
                t['injection']['state']='applied'
                self.cleanup(t)
                if trace_mode=='hidden' and not cleaned(t['cleanup']):
                    ack=self.apply_fault(t,True)
                    if ack!='ok':raise RuntimeError('Rétablissement non confirmé')
                    restored=self.engine.snapshot();self.guard(restored)
                    if not self.fault_matches(t,restored,True):raise RuntimeError('Port encore désactivé')
                    t['injection']['state']='restored';t['status']='a_controler';self.save()
                    raise RuntimeError('Masquage incomplet, port réactivé')
                self.event(t['id']+' : incident initialise.')
            except Exception:
                if t['injection']['state']=='restored':
                    t['status']='a_controler';self.save();raise RuntimeError('Injection annulée et configuration rétablie : symptôme ou masquage non confirmé. Vérifie le ticket avant de continuer.')
                t['injection']['state']='uncertain';t['status']='a_controler';self.save()
                raise RuntimeError('Injection incertaine. Le ticket est conserve. Utilise « Retablir le test » puis verifie avant de continuer.')
        self.save();return self.public()
    def apply_fault(self,t,restore):
        injection=t['injection']
        snapshot=self.engine.snapshot();self.guard(snapshot)
        if injection.get('target_serial') and device(snapshot,t['name']).get('serial')!=injection['target_serial']:raise ValueError('Le poste concerné a été remplacé ; modification automatique bloquée.')
        if self.endpoint(t['name'])!=injection.get('switch_port',injection['port']):raise ValueError('Le câblage du poste a changé ; modification automatique bloquée.')
        if injection.get('kind')=='vlan_wrong':return vlan_faults.apply(self.engine,injection,restore)
        if injection.get('kind','port_down')=='port_down':return self.set_port(injection['port'],restore)
        return self.engine.call(live_faults.apply_js(injection,restore))
    def fault_matches(self,t,snapshot,restore):
        injection=t['injection']
        if injection.get('kind')=='vlan_wrong':return vlan_faults.matches(self.engine,injection,restore)
        if injection.get('kind','port_down')=='port_down':
            port=next((p for p in device(snapshot,self.profile('switch'))['ports'] if p['name']==injection['port']),None)
            return bool(port and port.get('up') is restore)
        return live_faults.matches(snapshot,injection,restore)
    def clean_console(self):
        try:report=json.loads(self.engine.call(CLEAN_JS.replace('SW1',self.profile('switch'))))
        except Exception:report={'display':False,'history':False,'reason':'Aucune confirmation du pont'}
        self.state['console_diagnostic']=report;self.save();return report
    def cleanup(self,t):
        if t.get('injection',{}).get('kind')=='vlan_wrong':t['cleanup']={'display':False,'history':False,'intentional':True,'method':'Scénario VLAN avec traces de technicien conservées.'}
        elif t.get('injection',{}).get('kind','port_down')!='port_down':t['cleanup']={'display':True,'history':True,'method':'Modification par API, sans commandes de configuration dans la CLI.'}
        elif t.get('trace_mode')=='technician':t['cleanup']={'display':False,'history':False,'intentional':True}
        else:t['cleanup']=self.clean_console()
    def verify(self,t):
        s=self.engine.snapshot();self.guard(s)
        if sum(d['name']==t['name'] for d in s['devices'])>1:raise ValueError('Nom du poste ambigu : utilise un nom unique.')
        result=checks(s,t['baseline'],t['name'],'wifi' if t['kind']=='wifi' else 'wired',self.profile('network'))
        found=next((d for d in s['devices'] if d['name']==t['name']),None)
        if found:
            allowed=('PC-PT','Laptop-PT') if t['kind']=='wifi' else ('PC-PT',)
            result.append({'label':'Type de poste attendu','status':'valide' if found.get('model') in allowed else 'non satisfait','detail':''})
        if t['kind']=='incident' and t.get('injection',{}).get('target_serial'):
            result.append(dict(label='Identité du poste conservée',status='valide' if found and found.get('serial')==t['injection']['target_serial'] else 'non satisfait',detail='Le poste concerné doit conserver son numéro de série.'))
        if t['kind']=='incident':
            old_switch=device(t['baseline'],self.profile('switch'));current_switch=device(s,self.profile('switch'))
            injected_port=next((p for p in current_switch['ports'] if p['name']==t['injection'].get('switch_port',t['injection']['port'])),None)
            result.append(dict(label='Port concerné actif',status='valide' if injected_port and injected_port.get('up') else 'non satisfait',detail='La liaison du poste doit être active.'))
            expected=[p['name'] for p in old_switch['ports'] if p.get('up') and p.get('linked') and p['name']!=t['injection'].get('switch_port',t['injection']['port'])]
            current={p['name']:p for p in current_switch['ports']}
            preserved=all(current.get(name,{}).get('up') for name in expected)
            result.append(dict(label='Autres ports actifs de SW1 préservés',status='valide' if preserved else 'non satisfait',detail='Contrôle de l’état des ports observés actifs avant la panne ; ne prouve pas tous les services.'))
        if t['kind']=='incident' and t['injection'].get('kind','port_down') in ('ip_wrong','mask_wrong'):
            result.append(dict(label='Adressage de départ rétabli',status='valide' if self.fault_matches(t,s,True) else 'non satisfait',detail='Conserver l’adresse et le masque attendus pour ce poste.'))
        if t['kind']=='incident' and t['injection'].get('kind')=='vlan_wrong':
            try:correct=self.fault_matches(t,s,True)
            except Exception:correct=None
            result.append(dict(label='VLAN d’accès attendu rétabli',status='inconnu' if correct is None else ('valide' if correct else 'non satisfait'),detail='Lecture IOS fraîche ; un ping réussi seul ne valide pas le VLAN.'))
        if t['kind']=='incident':result=[c for c in result if c['label']!='Nouvel equipement depuis le point de depart']
        if any(c['label']=='Equipement present' and c['status']=='valide' for c in result):result.append(self.engine.ping(t['name'],self.profile('server')))
        t['checks']=result;t['complete']=all(c['status']=='valide' for c in result);t['checked']=now();t['manual_ssid']=False
        self.event(t['id']+' : verification effectuee.');return self.public()
    def workspace_action(self, t, action, data):
        if t['status']=='clos':raise ValueError('Ce ticket est clos.')
        if action=='notes':t['notes']=str(data.get('notes',''))[:4000]
        elif action in ('take','wait'):
            t['status']='en_cours' if action=='take' else 'en_attente'
        elif action in ('verify','close'):
            if t['id'].startswith('INC-AD-') and t['id'] != (self.controller.workspace.state.get('directory_incident') or {}).get('id'):
                raise ValueError('Cet incident appartient à un exercice précédent.')
            self.controller.observe(blocking=True)
            public=self.controller.workspace.public()
            result=public['checks']['read']
            t['checks']=[dict(label='Réseau et accès en lecture du partage',status='valide' if result['allowed'] else 'non satisfait',detail='Contrôle actuel du réseau Packet Tracer et des droits simulés.')]
            t['complete']=result['allowed'];t['checked']=now()
            if t.get('workspace_goal') == 'write':
                write = public['checks']['write']
                t['checks'].append(dict(label='Accès en écriture du partage', status='valide' if write['allowed'] else 'non satisfait', detail='Droit distinct, authentification et réseau observés.'))
                t['complete'] = t['complete'] and write['allowed']
            if t['id'].startswith('INC-AD-'):
                self.controller.workspace.state['validated'] = t['complete']
                self.controller.workspace.save()
            if action=='close':
                if not t['complete']:self.save();raise ValueError('Accès au partage non rétabli.')
                if t.get('timer') and t['timer'].get('started'):timers.operate(t['timer'],'finish')
                t.update(status='clos',closed=now())
        else:raise ValueError('Action non prise en charge pour ce ticket.')
        self.save()
        return self.public()

    def action(self,ident,action,data):
        t=self.get(ident)
        if t['kind']=='workspace' and action in ('verify','close'):
            return self.workspace_action(t,action,data)
        if t['status']=='clos':raise ValueError('Ce ticket est deja clos.')
        if action=='timer':
            cmd=data.get('timer_action');timer=t.get('timer')
            if cmd=='configure':
                if timer and timer.get('started'):raise ValueError('Durée verrouillée après le démarrage.')
                t['timer']=timers.configure(data.get('minutes',0),data.get('mode','training'))
                if t['status']=='en_cours':timers.autostart(t['timer'])
            else:
                if cmd not in ('pause','resume') or not timer:raise ValueError('Action chronomètre invalide pour un ticket.')
                timers.operate(timer,cmd)
            self.save()
        elif action=='wait':t['status']='en_attente';self.event(t['id']+' : en attente.')
        elif action=='severity':
            value=data.get('severity')
            if value not in ('faible','moderee','elevee','critique'):raise ValueError('Sévérité inconnue')
            t['severity']=value;self.event(t['id']+' : sévérité mise à jour.')
        elif action=='take':
            timers.autostart(t.get('timer'));t['status']='en_cours';self.event(t['id']+' : pris en charge.')
        elif action=='retry_service':
            if t['kind']!='service' or not self.desk:raise ValueError('Action réservée aux réseaux de tickets.')
            old=next(j for j in self.desk.g.jobs() if j['id']==t['job_id'])
            if old['status'] not in ('failed','interrupted'):raise ValueError('Relance réservée à une génération échouée ou interrompue.')
            job=self.desk.g.start(dict(mode='atelier' if t.get('procedural',{}).get('family')=='new_employee' else 'depannage',scenario=t['service_scenario'],level=5,count=1,ticket_title=t['title'],**({k:t['procedural'][k] for k in ('seed','address_family','site_code','employee_count','has_it','target_employee','employee_layout') if k in t['procedural']} if t.get('procedural') else {}),business_names=bool(t.get('procedural',{}).get('site_code'))));t['job_id']=job['id'];self.event(t['id']+' : préparation du réseau relancée.')
        elif action=='notes':t['notes']=str(data.get('notes',''))[:4000];self.save()
        elif action=='verify':
            if t['kind']=='site_service':return site_services.verify(self,t)
            if t['kind']=='service':
                t['checks']=[dict(label='Tests de service dans Packet Tracer',status='inconnu',detail='Validation manuelle : réalise les tests de la feuille, documente leurs résultats et confirme-les à la clôture.')];t['checked']=now();self.save();return self.public()
            return self.verify(t)
        elif action=='restore':
            if t['kind']=='site_service':return site_services.restore(self,t)
            if t['kind']!='incident':raise ValueError('Action reservee au test incident')
            self.guard(self.engine.snapshot())
            if self.endpoint(t['name'])!=t['injection'].get('switch_port',t['injection']['port']):raise ValueError('Le câblage du poste a changé : restauration automatique bloquée.')
            if self.apply_fault(t,True)!='ok':raise RuntimeError('Rétablissement non confirmé.')
            self.cleanup(t);t['injection']['state']='restored';t['status']='en_cours';self.event(t['id']+' : retablissement du test demande.');return self.verify(t)
        elif action=='close':
            if t['kind']=='site_service':
                site_services.verify(self,t)
                if not t['configuration_complete'] or data.get('manual_tests') is not True or len(t['notes'].strip())<20:raise ValueError('Configuration rétablie, tests fonctionnels déclarés et compte rendu détaillé requis.')
                if t.get('timer') and t['timer'].get('started'):timers.operate(t['timer'],'finish')
                t.update(status='clos',closed=now(),manual_tests=True,complete=False);self.event(t['id']+' : clos avec configuration contrôlée et tests fonctionnels déclarés.');return self.public()
            if t['kind']=='service':
                if not self.desk:raise ValueError('Service de tickets indisponible.')
                job=next(j for j in self.desk.g.jobs() if j['id']==t['job_id'])
                if job['status']!='done':raise ValueError('Le réseau du ticket n’est pas prêt.')
                if data.get('manual_tests') is not True or len(t['notes'].strip())<20:raise ValueError('Confirme les tests et enregistre un compte rendu précis avant de clôturer.')
                if t.get('timer') and t['timer']['started']:timers.operate(t['timer'],'finish')
                t.update(status='clos',closed=now(),manual_tests=True,complete=False,checked=now(),checks=[dict(label='Résultats déclarés par le technicien',status='inconnu',detail='Clôture manuelle, aucune validation automatique du service.')]);self.event(t['id']+' : clos sur déclaration manuelle des tests.');return self.public()
            if t['kind']=='incident' and t['injection']['state'] not in ('applied','restored'):raise ValueError('Injection incertaine : retablis le test avant de cloturer.')
            # Re-read live state; a former successful check cannot close a broken network.
            self.verify(t)
            manual=t['kind']=='wifi' and data.get('manual_ssid') is True
            ok=t['complete'] or (manual and all(c['status']=='valide' or (c['label']=='SSID et point d acces attendus' and c['status']=='inconnu') for c in t['checks']))
            if not ok:raise ValueError('Cloture refusee : objectifs non satisfaits ou verification manuelle manquante.')
            if t.get('timer') and t['timer'].get('started'):timers.operate(t['timer'],'finish')
            if t.get('injection',{}).get('kind')=='vlan_wrong':
                try:t['vlan_cleanup']=vlan_faults.remove_unused(self.engine,t['injection'])
                except Exception:t['vlan_cleanup']={'removed':False,'message':'Nettoyage du VLAN temporaire non confirmé ; VLAN conservé.'}
            final=self.engine.snapshot();self.guard(final);self.remember_inventory(final)
            t['manual_ssid']=manual;t['status']='clos';t['closed']=now();self.event(t['id']+' : clos'+(' avec confirmation manuelle du SSID.' if manual else '.'))
        else:raise ValueError('Action inconnue')
        return self.public()

def run():
    generator=Generator()
    bridge=PTCommandBridge();bridge.start();engine=Engine(bridge);tickets=Tickets(engine,ROOT/'donnees-netops.json');tickets.desk=ServiceDesk(tickets,generator);stop_arrivals=threading.Event()
    workspace=Controller(engine,ROOT/'workspace-session')
    def bind(state, folder):tickets.bind_environment(state,folder,generator,workspace)
    workspace.on_change=bind
    if workspace.workspace.state:bind(workspace.workspace.state,workspace.workspace.path.parent)
    def arrival_loop():
        while not stop_arrivals.wait(1):
            with workspace.lock, engine.lock:
                try:tickets.desk.tick()
                except Exception:pass
    threading.Thread(target=arrival_loop,daemon=True).start();token=secrets.token_urlsafe(32)
    workspace_routes=WorkspaceRoutes(workspace,token)
    def workspace_loop():
        while not stop_arrivals.is_set():
            workspace.observe()
            stop_arrivals.wait(10)
    threading.Thread(target=workspace_loop,daemon=True).start()
    class Handler(BaseHTTPRequestHandler):
        def send(self,code,data,ctype='application/json'):
            body=data.encode() if isinstance(data,str) else json.dumps(data,ensure_ascii=False).encode();self.send_response(code);self.send_header('Content-Type',ctype+'; charset=utf-8');self.send_header('Content-Length',str(len(body)));self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(body)
        def allowed(self):return self.headers.get('Host') in ('127.0.0.1:8765','localhost:8765')
        def do_GET(self):
            if not self.allowed():return self.send(403,{'error':'Acces refuse'})
            if workspace_routes.get(self):return
            if self.path=='/':return self.send(200,(ROOT/'tickets.html').read_text(encoding='utf-8').replace('__UI_TOKEN__',token),'text/html')
            if self.path=='/generator':return self.send(200,{'catalogue':generator.catalogue,'jobs':generator.jobs()})
            if self.path.startswith('/lab-file?'):
                try:
                    q=parse_qs(urlparse(self.path).query);p=generator.file(q['id'][0],q['name'][0]);body=p.read_bytes()
                    self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8' if p.suffix=='.html' else 'application/octet-stream');self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body);return
                except Exception:return self.send(404,{'error':'Fichier introuvable'})
            if self.path=='/state':
                with workspace.lock, engine.lock:return self.send(200,dict(tickets.public(),connected=bridge.is_connected))
            self.send(404,{'error':'Page inconnue'})
        def check_environment(self,data):
            site=tickets.state.get('site') or {}
            if site.get('environment_id') and data.get('environment_id')!=site['environment_id']:
                raise ValueError('L’environnement a changé. Actualise la page avant cette intervention.')
        def do_POST(self):
            if not self.allowed() or not secrets.compare_digest(self.headers.get('X-Diagnostic-Token',''),token):return self.send(403,{'error':'Acces refuse'})
            try:
                n=int(self.headers.get('Content-Length','0'))
                if not 0<=n<=8192:raise ValueError('Requete trop grande')
                data=json.loads(self.rfile.read(n) or b'{}')
                if workspace_routes.post(self,data):return
                if self.path in ('/new','/action','/inventory','/open','/ready','/attach','/service-ticket','/session-config','/session-control','/service-scan','/site-service','/console-test'):
                    with workspace.lock:
                        if tickets.state.get('site',{} ) and tickets.state['site'].get('environment_id') and data.get('environment_id')!=tickets.state['site']['environment_id']:
                            raise ValueError('L’environnement a changé. Actualise la page avant cette intervention.')
                if self.path in ('/session-config','/session-control','/service-ticket'):
                    with workspace.lock, engine.lock:
                        self.check_environment(data)
                        if self.path=='/session-config':result=tickets.desk.configure(data)
                        elif self.path=='/session-control':result=tickets.desk.control(data.get('active') is True)
                        else:result=tickets.desk.create(data.get('scenario'))
                    return self.send(200,result)
                if self.path=='/generate':return self.send(200,generator.start(data))
                if self.path=='/lab-timer':return self.send(200,generator.timer(data))
                if self.path=='/open-lab':return self.send(200,generator.open(data['id'],data['name']))
                if self.path=='/action':
                    with workspace.lock:
                        self.check_environment(data)
                        if tickets.get(data['id'])['kind']=='workspace':
                            return self.send(200,tickets.action(data['id'],data['action'],data))
                with workspace.lock, engine.lock:
                    if self.path!='/register':self.check_environment(data)
                    if self.path=='/register':tickets.register();result=tickets.public()
                    elif self.path=='/service-scan':result=site_services.scan(tickets)
                    elif self.path=='/site-service':result=site_services.create(tickets,data['service'],data['device'])
                    elif self.path=='/inventory':result=tickets.sync_inventory()
                    elif self.path=='/new':result=tickets.new(data['kind'],data.get('trace_mode','hidden'),data.get('target'),data.get('fault','port_down'))
                    elif self.path=='/open':result=tickets.open_network()
                    elif self.path=='/attach':tickets.attach(data['file']);result=tickets.public()
                    elif self.path=='/ready':result=tickets.ready()
                    elif self.path=='/console-test':
                        tickets.guard(engine.snapshot());result=tickets.clean_console()
                    elif self.path=='/action':result=tickets.action(data['id'],data['action'],data)
                    else:return self.send(404,{'error':'Action inconnue'})
                self.send(200,result)
            except Exception as e:self.send(400,{'error':str(e)})
        def log_message(self,*args):pass
    server=ThreadingHTTPServer(('127.0.0.1',8765),Handler)
    print('NetOps Lab : http://127.0.0.1:8765\nOuvrir le reseau-test.pkt puis Extensions > MCP BUILDER.\nGarder cette console ouverte. Ctrl+C pour arreter.')
    webbrowser.open('http://127.0.0.1:8765')
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:stop_arrivals.set();server.server_close();bridge.stop()
if __name__=='__main__':
    try:run()
    except Exception as e:print('Demarrage impossible :',e);raise SystemExit(1)
