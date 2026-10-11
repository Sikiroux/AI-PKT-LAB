"""Adaptateur des applications : identité et preuves construites côté serveur."""
import time
import sim_deployment
import desktop_services as ds
import directory_adapter as ad
from workspace_model import evaluate


def remote(s):
    if not s.get('remote_session'):raise ValueError('Ouvre une session distante sur ce poste.')
    result=evaluate(s,'remote')
    if not result['allowed']:
        raise ValueError('Le bureau et la session utilisateur sont conservés. '+('Contrôle réseau récent requis pour cette action.' if result['status']=='unknown' else 'Accès distant indisponible selon le dernier contrôle.'))

def admin(s,now):
    n=ad.context(s,'technician',now)['network']
    if n['status']!='passed' or not n['observed_at']<=now<=n['valid_until']:raise ValueError('Vérifie le réseau du technicien et son VPN avant l’administration.')

def handle(c,path,data):
    with c.lock:
        s=c.workspace.state
        if not s or not ds.ensure(s) and 'desktop_services' not in s:raise ValueError('Poste non disponible.')
        now=time.time();app,action=path.split('/',1);payload=data.get('payload',{})
        if not isinstance(payload,dict):raise ValueError('Paramètres invalides.')
        if app=='corporate':
            if s.get('_client_view') or data.get('client_serial'):raise ValueError('Ouvre ces services depuis le bureau du technicien.')
            admin(s,now)
            import sim_corporate
            if sim_corporate.ensure(s):c.workspace.save()
            if action=='state':
                result=sim_corporate.public(s)
                result['evaluations']={ident:sim_corporate.evaluate(s,ident,now) for ident in s['corporate']['requests']}
                return result
            if action!='operation':raise ValueError('Action inconnue.')
            if data.get('operation')=='first-login':
                if type(data.get('expected_revision')) is not int or data['expected_revision']!=s['corporate']['revision']:raise ValueError('Services modifiés. Actualise.')
                if not any(r['username']==payload.get('username') for r in s['corporate']['requests'].values()):raise ValueError('Compte d’arrivée requis.')
                import sim_ad
                outcome=sim_ad.change_password(s['directory'],payload.get('username'),payload.get('old_password'),payload.get('new_password'),ad.context(s,'technician',now),now)
                s['directory']=outcome['directory'];s['corporate']['revision']+=1
                c.workspace.event('Première connexion d’arrivée : '+outcome['result']['code'])
                if outcome['result']['code']!='OK':raise ValueError(outcome['result']['code'])
                return dict(result={'code':'OK'})
            work,result=sim_corporate.operate(s,data.get('operation'),payload,data.get('expected_revision'),now)
            # Commit sous le verrou existant, après validation de toute l’opération.
            s['corporate']=work['corporate'];sim_corporate.sync_people(s)
            c.workspace.event('Services entreprise : '+str(data.get('operation')))
            if c.on_change:c.on_change(s,c.workspace.path.parent)
            return dict(result=result)
        if app=='inspection':
            if action!='state':raise ValueError('Inspection en lecture seule.')
            source=data.get('source','client')
            if source=='technician':admin(s,now)
            elif source=='client':remote(s)
            else:raise ValueError('Source inconnue.')
            return ds.inspection(s)
        if app=='deployment':
            d=s['desktop_services'].get('deployment')
            if action not in ('state','operation'):raise ValueError('Action de déploiement inconnue.')
            if action=='operation':admin(s,now)
            if d is None:
                d=sim_deployment.generate(s['seed'],s.get('environment_id','legacy'))
            if action=='operation':
                operation=data.get('operation');revision=data.get('expected_revision')
                if operation=='reset':
                    if type(revision) is not int or revision!=d['revision']:raise ValueError('L’atelier a changé. Actualise avant de poursuivre.')
                    fresh=sim_deployment.generate(d.get('seed',s['seed']),s.get('environment_id','legacy'))
                    fresh.update(revision=d['revision']+1,attempt=d['attempt']+1);d=fresh
                else:d=sim_deployment.apply(d,operation,payload,revision)
                s['desktop_services']['deployment']=d
                if s.get('desktop_incident',{}).get('family')=='deployment':s['validated']=False
                c.workspace.event('Atelier de déploiement : '+str(operation))
            elif 'deployment' not in s['desktop_services']:
                s['desktop_services']['deployment']=d;c.workspace.save()
            return dict(service=d,result=sim_deployment.evaluate(d))
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
            r=ds.ftp_action(s,action,payload,'client',now)
            if r.get('allowed') and action in ('download','upload'):
                import workstation_requests
                workstation_requests.record(s,action,payload.get('name'),now)
            s['validated']=False;c.workspace.event('FTP '+action+' : '+r['code']);return dict(result=r,revision=s['desktop_services']['ftp']['revision'])
        if app=='endpoint' and action=='read-local':
            name=ds.file_name(data.get('name'));files=s['desktop_services']['endpoint']['local_files']
            if name not in files:raise ValueError('Fichier local absent.')
            return dict(name=name,content=files[name])
        if app=='endpoint' and action=='save-local':
            r=ds.operation(s,app,'save_local',payload);c.workspace.event('Document local enregistré.');return dict(result=r)
        raise ValueError('Action d’application inconnue.')
