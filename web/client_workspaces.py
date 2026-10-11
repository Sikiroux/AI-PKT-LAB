"""Bureaux par numéro de série, adaptateur vers les moteurs historiques mono-client.

Le stockage canonique conserve le premier client pour les anciens scénarios.
Une vue temporaire fournit l'alias client aux moteurs, sous le verrou Controller.
Les services serveur sont communs ; observations, sessions et paramètres sont locaux.
"""
import copy
import hashlib
import time
import sim_ad
import files_adapter

INCIDENT_KEYS=('desktop_incident','mixed_incident','directory_incident','file_incident','dns_incident')
LOCAL_KEYS=('remote_service','remote_session','directory_auth','observation','network_observation','last_known_observation')
SHARED_KEYS=('directory','directory_resource','directory_service','file_service','dns_service',
             'desktop_services','events','desktop_incident_count','validated','peripherals','local_access',
             'live_incidents','live_incident_count')

def primary_serial(s):return s.get('devices',{}).get('client',{}).get('serial')

def capture(s, serial):
    d=s['desktop_services'];dns=s['dns_service']
    return dict(device=copy.deepcopy(s['devices']['client']),requester=s['requester'],user_id=s['directory_user_id'],
        local={k:copy.deepcopy(s.get(k)) for k in LOCAL_KEYS},endpoint=copy.deepcopy(d['endpoint']),
        printing={k:copy.deepcopy(v) for k,v in d['printing'].items() if k!='printer'},
        dns_client=copy.deepcopy(dns['clients']['client']),dns_cache=copy.deepcopy(dns['cache'].get('client',{})),
        ftp_session=copy.deepcopy(d['ftp']['sessions'].get('client')))

def ensure(s):
    if not s or not all(k in s for k in ('directory','dns_service','desktop_services')):return False
    profiles=s.setdefault('client_workspaces',{});first=primary_serial(s)
    if not first:return False
    changed=False
    if first not in profiles:profiles[first]=capture(s,first);changed=True
    remaining=[d for role,d in s.get('devices',{}).items() if role=='client2' or role.startswith('employee')]
    for number,second in enumerate(remaining,2):
      if second and second['serial'] not in profiles:
          # Le moteur AD reste responsable de la création et des credentials de formation.
          source=s['directory']['users'][s['directory_user_id']]
          actor=dict(id='technician',environment_id=s['environment_id'],permissions=[sim_ad.CAPABILITY_USERS])
          staff=(s.get('staff') or [])[number-1] if len(s.get('staff',[]))>=number else None
          name=staff['display_name'] if staff else ('Alex '+s['site']);username=staff['username'] if staff else ('alex.'+s['site'].lower())
          outcome=sim_ad.apply_operation(s['directory'],'create_user',dict(username=username,display_name=name,
              ou_id=source['ou_id'],initial_password=sim_ad.TRAINING_PASSWORD,must_change_password=False),actor,time.time())
          generated=outcome['result']['user_id'];s['directory']=outcome['directory']
          # Initialisation procédurale uniquement : une création manuelle dans AD reste aléatoire.
          uid='usr-'+hashlib.sha256((s['seed']+(':client2-account:v1' if number==2 else ':employee-account:v1:'+second['serial'])).encode()).hexdigest()[:16]
          if uid in s['directory']['users']:raise ValueError('Collision d’identité du second poste.')
          user=s['directory']['users'].pop(generated);user['id']=uid;s['directory']['users'][uid]=user
          s['directory']['audit'][-1]['user_id']=uid
          sim_ad.validate_directory(s['directory'])
          record=copy.deepcopy(profiles[first]);record.update(device=copy.deepcopy(second),requester=name,user_id=uid)
          record['local'].update(remote_service=True,remote_session=False,directory_auth=None,observation=None,network_observation=None,last_known_observation=None)
          record['endpoint']['local_files']={'Bienvenue.txt':'Poste de '+name+' — '+s['company']}
          record['endpoint']['network_pending']=None
          record['printing'].update(jobs=[],next_job=1);record['dns_cache']={};record['ftp_session']=None
          record['dns_client']['name']=second['name']
          profiles[second['serial']]=record;files_adapter.sync_catalog(s);changed=True
          # Un poste témoin dispose de la lecture, sans modifier les groupes des autres comptes.
          share=s['file_service']['shares'][s['documents_share_id']]
          for layer in ('share_acl','folder_acl'):
              for action in ('list','read'):
                  if uid not in share[layer][action]['user_ids']:share[layer][action]['user_ids'].append(uid)
    return changed

def sync_primary(s):
    if s and s.get('client_workspaces') and 'desktop_services' in s:
        first=primary_serial(s);s['client_workspaces'][first]=capture(s,first)

def project(s,serial):
    if serial==primary_serial(s):return copy.deepcopy(s)
    if not serial or serial not in s.get('client_workspaces',{}):raise ValueError('Bureau simulé inconnu pour ce poste.')
    view=copy.deepcopy(s);view['_client_view']=serial;r=view['client_workspaces'][serial]
    view['devices']['client']=copy.deepcopy(r['device']);view['requester']=r['requester'];view['directory_user_id']=r['user_id']
    for key in LOCAL_KEYS:view[key]=copy.deepcopy(r['local'].get(key))
    d=view['desktop_services'];d['endpoint']=copy.deepcopy(r['endpoint'])
    printer=d['printing']['printer'];d['printing']=copy.deepcopy(r['printing']);d['printing']['printer']=printer
    d['ftp']['sessions'].pop('client',None)
    if r['ftp_session']:d['ftp']['sessions']['client']=copy.deepcopy(r['ftp_session'])
    view['dns_service']['clients']['client']=copy.deepcopy(r['dns_client']);view['dns_service']['cache']['client']=copy.deepcopy(r['dns_cache'])
    for key in INCIDENT_KEYS:
        incident=view.get(key)
        if incident and incident.get('target_serial',primary_serial(s))!=serial:view.pop(key)
    if not any(view.get(k) for k in INCIDENT_KEYS):view['ticket']='Bureau de '+r['requester']+' · '+r['device']['name']
    return view

def merge(s,view,serial):
    """Fusion explicite : ne remplace jamais le client canonique par le poste projeté."""
    if serial not in s['client_workspaces']:raise ValueError('Le poste n’appartient plus à cette entreprise.')
    old_users=(s.get('directory') or {}).get('users',{})
    new_users=(view.get('directory') or {}).get('users',{})
    security_fields=('credential','enabled','locked_until','password_expires_at','must_change_password','username')
    changed_users={uid for uid in set(old_users)|set(new_users) if any(old_users.get(uid,{}).get(k)!=new_users.get(uid,{}).get(k) for k in security_fields)}
    ftp_changed=any(s['desktop_services']['ftp'].get(k)!=view['desktop_services']['ftp'].get(k) for k in ('accounts','service_running','control_allowed','data_allowed'))
    record=capture(view,serial)
    if record.get('user_id') in changed_users:record['local']['directory_auth']=None
    s['client_workspaces'][serial]=record
    if s.get('directory_user_id') in changed_users:s['directory_auth']=None
    for key,profile in s['client_workspaces'].items():
        if key!=serial and profile.get('user_id') in changed_users:profile['local']['directory_auth']=None
    primary_endpoint=s['desktop_services']['endpoint'];primary_printing=s['desktop_services']['printing']
    primary_ftp=s['desktop_services']['ftp']['sessions'].get('client')
    primary_dns=s['dns_service']['clients']['client'];primary_cache=s['dns_service']['cache'].get('client',{})
    for key in SHARED_KEYS:
        if key in view and key not in ('validated','desktop_services','dns_service'):s[key]=copy.deepcopy(view[key])
    # Les files et le spooler appartiennent au poste ; papier/état matériel sont communs.
    s['desktop_services']=copy.deepcopy(view['desktop_services']);s['desktop_services']['endpoint']=primary_endpoint
    printer=s['desktop_services']['printing']['printer'];s['desktop_services']['printing']=primary_printing;s['desktop_services']['printing']['printer']=printer
    s['desktop_services']['ftp']['sessions'].pop('client',None)
    if primary_ftp and not ftp_changed:s['desktop_services']['ftp']['sessions']['client']=primary_ftp
    if ftp_changed:
        s['desktop_services']['ftp']['sessions'].clear()
        for profile in s['client_workspaces'].values():profile['ftp_session']=None
    s['dns_service']=copy.deepcopy(view['dns_service']);s['dns_service']['clients']['client']=primary_dns;s['dns_service']['cache']['client']=primary_cache
    incoming=view.get('desktop_incident')
    if incoming and incoming.get('target_serial')==serial and incoming.get('id')!=s.get('desktop_incident',{}).get('id'):
        for key in INCIDENT_KEYS:s.pop(key,None)
    for key in INCIDENT_KEYS:
        incident=view.get(key)
        if incident and incident.get('target_serial')==serial:
            s[key]=copy.deepcopy(incident);s['validated']=view['validated'];s['ticket']=incident['description']
    # Une modification d'une dépendance partagée exige une nouvelle vérification.
    if view.get('validated') is False:s['validated']=False
    files_adapter.sync_catalog(s)

def reset_sessions(s):
    for r in s.get('client_workspaces',{}).values():
        r['local'].update(remote_session=False,directory_auth=None,observation=None,network_observation=None,last_known_observation=None)
        r['ftp_session']=None
