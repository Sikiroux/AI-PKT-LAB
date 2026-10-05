"""Adaptateur des applications : identité et preuves construites côté serveur."""
import time
import desktop_services as ds
import directory_adapter as ad
from workspace_model import evaluate


def remote(s):
    if not s.get('remote_session') or not evaluate(s,'remote')['allowed']:raise ValueError('Reconnecte le bureau client après vérification réseau.')

def admin(s,now):
    n=ad.context(s,'technician',now)['network']
    if n['status']!='passed' or not n['observed_at']<=now<=n['valid_until']:raise ValueError('Vérifie le réseau du technicien et son VPN avant l’administration.')

def handle(c,path,data):
    with c.lock:
        s=c.workspace.state
        if not s or not ds.ensure(s) and 'desktop_services' not in s:raise ValueError('Poste non disponible.')
        now=time.time();app,action=path.split('/',1);payload=data.get('payload',{})
        if not isinstance(payload,dict):raise ValueError('Paramètres invalides.')
        if app not in ('endpoint','printing','ftp'):raise ValueError('Application inconnue.')
        if action=='admin':admin(s,now);return dict(service=ds.public(s)[app],applications=ds.APPS,server=s['devices']['server'],printer=s['devices'].get('printer',s['devices']['server']))
        if action=='operation':
            admin(s,now)
            if app=='endpoint':remote(s)
            outcome=ds.operation(s,app,data.get('operation'),payload)
            ds.process_jobs(s,now);s['validated']=False;c.workspace.event('Application '+app+' : '+str(data.get('operation')))
            return dict(result=outcome,service=ds.public(s)[app])
        remote(s)
        if action=='state':return dict(service=ds.public(s)[app],applications=ds.APPS,network=(s.get('network_observation') or {}).get('interfaces',{}),expected_network=s['desktop_services']['endpoint'].get('expected_network'),server=s['devices']['server'],printer=s['devices'].get('printer',s['devices']['server']))
        if app=='printing' and action=='print':
            r=ds.print_job(s,data.get('name'),data.get('queue_id'),now);s['validated']=False;c.workspace.event('Impression : '+r['code']);return dict(result=r,service=ds.public(s)['printing'])
        if app=='ftp' and action in ('login','logout','list','download','upload'):
            r=ds.ftp_action(s,action,payload,'client',now);s['validated']=False;c.workspace.event('FTP '+action+' : '+r['code']);return dict(result=r,revision=s['desktop_services']['ftp']['revision'])
        if app=='endpoint' and action=='read-local':
            name=ds.file_name(data.get('name'));files=s['desktop_services']['endpoint']['local_files']
            if name not in files:raise ValueError('Fichier local absent.')
            return dict(name=name,content=files[name])
        if app=='endpoint' and action=='save-local':
            r=ds.operation(s,app,'save_local',payload);c.workspace.event('Document local enregistré.');return dict(result=r)
        raise ValueError('Action d’application inconnue.')
