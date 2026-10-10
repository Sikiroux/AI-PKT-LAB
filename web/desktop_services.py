"""Poste, impression et FTP pédagogiques. Aucun accès au réseau ou disque réel."""
import copy
import hashlib
import hmac
import ipaddress
import time
import directory_adapter as ad
import sim_ad

APPS={'documents':'Documents','terminal':'Terminal réseau','dns':'DNS','login':'Session utilisateur','settings':'Paramètres du poste','printers':'Imprimantes','ftp':'Client FTP'}

def password_hash(password):return hashlib.sha256(('training-ftp:'+password).encode()).hexdigest()

def ensure(s):
    if not s or 'dns_service' not in s or 'desktop_services' in s:return False
    printer=s['devices'].get('printer',s['devices']['server']);name=printer['name'] if 'printer' in s['devices'] else 'PRN-'+s['site']+'-01'
    endpoint=dict(applications=list(APPS),mapped_drive=dict(letter='Z:',server_id='server',share_id=s['documents_share_id'],path='\\\\'+s['devices']['server']['name']+'\\Documents'),local_files={'Bienvenue.txt':'Poste de formation — '+s['company']},network_pending=None)
    printing=dict(spooler_running=True,default_queue='office',queues={'office':dict(id='office',name=name,port_ip=printer['ip'],driver_valid=True,paused=False,use_offline=False),'pdf':dict(id='pdf',name='Impression PDF locale',port_ip=None,driver_valid=True,paused=False,use_offline=False)},printer=dict(device_role='printer' if 'printer' in s['devices'] else 'server',proxy='Printer-PT' if 'printer' in s['devices'] else 'Serveur PT proxy (ancienne session)',enabled=True,paper_pages=50),jobs=[],next_job=1)
    ftp=dict(service_running=True,control_allowed=True,data_allowed=True,capacity_bytes=1048576,accounts={'depot':dict(enabled=True,password_hash=password_hash(sim_ad.TRAINING_PASSWORD),read=True,write=True)},files={'Notice.txt':'Dépôt FTP de formation — '+s['company']},revision=1,sessions={})
    s['desktop_services']=dict(version=1,endpoint=endpoint,printing=printing,ftp=ftp);return True

def public(s):
    if not s or 'desktop_services' not in s:return None
    d=copy.deepcopy(s['desktop_services']);d['ftp'].pop('sessions',None)
    for a in d['ftp']['accounts'].values():a.pop('password_hash',None)
    d['ftp']['files']=[dict(name=n,size=len(v.encode())) for n,v in d['ftp']['files'].items()]
    d['endpoint']['local_files']=[dict(name=n,size=len(v.encode())) for n,v in d['endpoint']['local_files'].items()]
    d['printing']['jobs']=[{k:v for k,v in j.items() if k!='content'} for j in d['printing']['jobs'][-40:]]
    return d

def network(s,key,source,target,now):
    p=(s.get('observation') or {}).get('probes',{}).get(key,{})
    valid=p.get('source_device')==s['devices'][source]['name'] and p.get('target')==target and 0<=now-p.get('at',0)<=ad.TTL
    return p.get('status','unknown') if valid and p.get('status') in ('passed','failed') else 'unknown'

def chain(stages):
    nodes=[];blocked=False;code='OK';status='passed'
    for key,label,condition,error in stages:
        st='blocked' if blocked else 'unknown' if condition is None else 'passed' if condition else 'failed'
        nodes.append(dict(stage=key,label=label,status=st,children=[]))
        if not blocked and st!='passed':blocked=True;code=error;status=st
    root=nodes[0]
    for a,b in zip(nodes,nodes[1:]):a['children']=[b]
    return dict(allowed=not blocked,code=code,status=status,tree=root,evidence='icmp_proxy + simulation')

def evaluate_print(s,queue_id,now):
    d=s['desktop_services'];p=d['printing'];q=p['queues'].get(queue_id);physical=queue_id!='pdf';role=p['printer']['device_role'];target=s['devices'][role]['ip'];net=network(s,'printing','client',target,now)
    return chain([
        ('application','Application Imprimantes installée','printers' in d['endpoint']['applications'],'APPLICATION_MISSING'),
        ('queue','File installée',q is not None,'QUEUE_NOT_FOUND'),
        ('spooler','Spouleur démarré',p['spooler_running'],'SPOOLER_STOPPED'),
        ('driver','Pilote utilisable',bool(q and q['driver_valid']),'DRIVER_INVALID'),
        ('pause','File reprise',bool(q and not q['paused']),'QUEUE_PAUSED'),
        ('offline','Mode hors connexion désactivé',bool(q and not q['use_offline']),'OFFLINE_MODE'),
        ('port','Destination de la file correcte',bool(q and (not physical or q['port_ip']==target)),'PRINTER_PORT_WRONG'),
        ('network','Connectivité PT vers l’imprimante (proxy ICMP)',True if not physical else None if net=='unknown' else net=='passed','NETWORK_UNKNOWN' if net=='unknown' else 'NETWORK_DOWN'),
        ('printer','Imprimante disponible',not physical or p['printer']['enabled'],'PRINTER_DISABLED'),
        ('paper','Papier disponible',not physical or p['printer']['paper_pages']>0,'PAPER_EMPTY')])

def process_jobs(s,now):
    if 'desktop_services' not in s:return
    p=s['desktop_services']['printing']
    for j in p['jobs']:
        if j['status'] not in ('queued','blocked'):continue
        r=evaluate_print(s,j['queue_id'],now);j['detail']=r['code']
        if r['allowed']:
            j.update(status='printed',finished_at=now)
            if j['queue_id']!='pdf':p['printer']['paper_pages']-=1
        else:j['status']='blocked'

def print_job(s,name,queue_id=None,now=None):
    now=time.time() if now is None else now;d=s['desktop_services'];p=d['printing'];q=queue_id or p['default_queue']
    if name not in d['endpoint']['local_files']:raise ValueError('Document local absent.')
    if q not in p['queues']:raise ValueError('File d’impression inconnue.')
    if not p['spooler_running'] or 'printers' not in d['endpoint']['applications']:return dict(allowed=False,code='SPOOLER_STOPPED' if not p['spooler_running'] else 'APPLICATION_MISSING')
    if len([j for j in p['jobs'] if j['status'] in ('queued','blocked')])>=40:raise ValueError('File limitée à 40 travaux en attente.')
    j=dict(id=p['next_job'],queue_id=q,name=name,content=d['endpoint']['local_files'][name],created_at=now,status='queued');p['next_job']+=1;p['jobs'].append(j);p['jobs']=p['jobs'][-100:];process_jobs(s,now)
    return dict(allowed=True,code='PRINTED' if j['status']=='printed' else 'QUEUED',job=copy.deepcopy(j))

def ftp_check(s,action,source,now):
    d=s['desktop_services'];f=d['ftp'];target=s['devices']['server']['ip'];key='share' if source=='client' else 'directory';net=network(s,key,source,target,now);session=f['sessions'].get(source,{})
    valid=session.get('environment_id')==s.get('environment_id','legacy') and session.get('source_device')==s['devices'][source]['name'] and now<session.get('expires_at',0)
    account=f['accounts'].get(session.get('username')) if valid else None
    return chain([
        ('application','Client FTP installé',source=='technician' or 'ftp' in d['endpoint']['applications'],'APPLICATION_MISSING'),
        ('network','Connectivité PT vers le dépôt (proxy ICMP)',None if net=='unknown' else net=='passed','NETWORK_UNKNOWN' if net=='unknown' else 'NETWORK_DOWN'),
        ('service','Service FTP démarré',f['service_running'],'FTP_SERVICE_STOPPED'),
        ('control','Connexion de contrôle autorisée',f['control_allowed'],'FTP_CONTROL_BLOCKED'),
        ('session','Compte FTP connecté',action=='login' or valid,'FTP_NOT_AUTHENTICATED'),
        ('account','Compte FTP actif',action=='login' or bool(account and account['enabled']),'FTP_ACCOUNT_DISABLED'),
        ('permission','Permission du transfert',action=='login' or bool(account and account['write' if action=='upload' else 'read']),'FTP_PERMISSION_DENIED'),
        ('data','Connexion de données autorisée',action=='login' or f['data_allowed'],'FTP_DATA_BLOCKED')])

def file_name(name):
    if not isinstance(name,str) or not name.strip() or len(name)>100 or any(c in name for c in '/\\\\\x00\r\n') or name in ('.','..'):raise ValueError('Nom de fichier simple requis.')
    return name

def ftp_action(s,action,payload,source,now):
    f=s['desktop_services']['ftp']
    if action=='logout':f['sessions'].pop(source,None);return dict(allowed=True,code='FTP_LOGGED_OUT')
    if action not in ('login','list','download','upload'):raise ValueError('Action FTP inconnue.')
    if action=='login':f['sessions'].pop(source,None)
    r=ftp_check(s,action,source,now)
    if not r['allowed']:return r
    if action=='login':
        username=payload.get('username');password=payload.get('password');a=f['accounts'].get(username) if isinstance(username,str) else None
        f['sessions'].pop(source,None)
        if not a or not a['enabled'] or not isinstance(password,str) or not hmac.compare_digest(a['password_hash'],password_hash(password)):return dict(allowed=False,code='FTP_AUTHENTICATION_FAILED')
        f['sessions'][source]=dict(username=username,source_device=s['devices'][source]['name'],environment_id=s.get('environment_id','legacy'),expires_at=now+1800)
        return dict(allowed=True,code='230',message='Connexion FTP simulée ouverte.')
    if action=='list':r.update(code='226',files=[dict(name=n,size=len(c.encode())) for n,c in f['files'].items()]);return r
    name=file_name(payload.get('name'))
    if action=='download':
        if name not in f['files']:return dict(allowed=False,code='550_FILE_NOT_FOUND')
        local=s['desktop_services']['endpoint']['local_files']
        if name not in local and len(local)>=100:return dict(allowed=False,code='LOCAL_STORAGE_FULL')
        local[name]=f['files'][name];return dict(allowed=True,code='226',name=name,content=f['files'][name])
    content=payload.get('content');revision=payload.get('expected_revision')
    if not isinstance(content,str) or len(content.encode())>65536:raise ValueError('Texte de 64 Kio maximum.')
    if type(revision) is not int or revision!=f['revision']:return dict(allowed=False,code='REVISION_CONFLICT')
    used=sum(len(c.encode()) for c in f['files'].values())-len(f['files'].get(name,'').encode())+len(content.encode())
    if used>f['capacity_bytes']:return dict(allowed=False,code='552_CAPACITY_EXCEEDED')
    f['files'][name]=content;f['revision']+=1;return dict(allowed=True,code='226',name=name)

def operation(s,app,op,payload):
    d=s['desktop_services'];e=d['endpoint']
    def boolean(key):
        value=payload.get(key)
        if type(value) is not bool:raise ValueError('Valeur oui/non requise.')
        return value
    if app=='endpoint':
        if op=='set_application':
            ident=payload.get('id');installed=boolean('installed')
            if ident not in APPS:raise ValueError('Application inconnue.')
            if ident in ('settings','login','terminal'):raise ValueError('Application essentielle protégée.')
            e['applications']=[x for x in e['applications'] if x!=ident]+([ident] if installed else [])
        elif op=='set_drive':
            path=payload.get('path')
            if not isinstance(path,str) or not path.startswith('\\\\') or len(path)>256:raise ValueError('Chemin UNC requis.')
            e['mapped_drive']['path']=path
        elif op=='save_local':
            name=file_name(payload.get('name'));content=payload.get('content')
            if not isinstance(content,str) or len(content.encode())>65536:raise ValueError('Texte de 64 Kio maximum.')
            if name not in e['local_files'] and len(e['local_files'])>=100:raise ValueError('Stockage local limité à 100 fichiers.')
            e['local_files'][name]=content
        else:raise ValueError('Opération poste inconnue.')
    elif app=='printing':
        p=d['printing'];q=p['queues'].get(payload.get('queue_id','office'))
        if op=='set_spooler':p['spooler_running']=boolean('running')
        elif op=='restart_spooler':p['spooler_running']=True
        elif op=='cancel_job':
            jobs=[j for j in p['jobs'] if j['id']==payload.get('id')]
            if not jobs:raise ValueError('Travail absent.')
            if jobs[0]['status']=='printed':raise ValueError('Travail déjà imprimé.')
            jobs[0]['status']='cancelled'
        elif op=='set_default':
            if q is None:raise ValueError('File absente.')
            p['default_queue']=q['id']
        elif op in ('set_paused','set_offline','set_driver','set_port'):
            if q is None:raise ValueError('File absente.')
            if op=='set_port':q['port_ip']=str(ipaddress.IPv4Address(payload.get('ip')))
            else:q[{'set_paused':'paused','set_offline':'use_offline','set_driver':'driver_valid'}[op]]=boolean('value')
        elif op=='set_printer_enabled':p['printer']['enabled']=boolean('value')
        elif op=='add_paper':
            count=payload.get('pages')
            if type(count) is not int or not 1<=count<=500:raise ValueError('1 à 500 feuilles.')
            p['printer']['paper_pages']=min(1000,p['printer']['paper_pages']+count)
        else:raise ValueError('Opération impression inconnue.')
    elif app=='ftp':
        f=d['ftp']
        if op in ('set_service','set_control','set_data'):f[{'set_service':'service_running','set_control':'control_allowed','set_data':'data_allowed'}[op]]=boolean('value');f['sessions']={}
        elif op=='set_account':
            name=payload.get('username');field=payload.get('field')
            if name not in f['accounts'] or field not in ('enabled','read','write'):raise ValueError('Compte ou permission inconnu.')
            f['accounts'][name][field]=boolean('value');f['sessions']={}
        elif op=='reset_password':
            name=payload.get('username')
            if name not in f['accounts']:raise ValueError('Compte inconnu.')
            f['accounts'][name]['password_hash']=password_hash(sim_ad.TRAINING_PASSWORD);f['sessions']={}
        elif op=='set_capacity':
            count=payload.get('bytes')
            if type(count) is not int or not 1<=count<=104857600:raise ValueError('Capacité de 1 à 104857600 octets.')
            f['capacity_bytes']=count
        else:raise ValueError('Opération FTP inconnue.')
    else:raise ValueError('Application inconnue.')
    return dict(allowed=True,code='UPDATED')


def inspection(s):
    """Read-only projection of simulated services and the existing session journal."""
    desktop=s.get('desktop_services',{})
    def status(value):
        if value is True or value=='running':return 'running'
        if value is False or value=='stopped':return 'stopped'
        return 'unknown'
    services=[
        dict(id='spooler',name='Spouleur d’impression',scope='Poste sélectionné',status=status(desktop.get('printing',{}).get('spooler_running'))),
        dict(id='files',name='Partage de fichiers',scope='Serveur de fichiers',status=status(s.get('file_service',{}).get('service_status'))),
        dict(id='dns',name='Serveur DNS',scope='Infrastructure',status=status(s.get('dns_service',{}).get('service_status'))),
        dict(id='ftp',name='Serveur FTP',scope='Serveur de fichiers',status=status(desktop.get('ftp',{}).get('service_running'))),
        dict(id='directory',name='Annuaire',scope='Infrastructure',status=status(s.get('directory_service'))),
    ]
    events=[dict(at=e.get('at'),text=e.get('text','')) for e in s.get('events',[])[-100:] if isinstance(e,dict)]
    return dict(environment_id=s.get('environment_id'),services=services,events=events,
                evidence='simulation_state',journal_scope='session',limit=100)
