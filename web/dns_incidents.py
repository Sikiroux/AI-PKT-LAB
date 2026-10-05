"""Incidents DNS déterministes sur le réseau de l'environnement actif."""
import copy
import hashlib
import random
import directory_adapter as ad
import dns_adapter as da
import sim_dns

FAMILIES=('wrong_resolver','missing_record','wrong_address','service_stopped','transport_blocked','negative_cache','stale_cache')

def prepare(state,now):
    if any(state.get(k) for k in ('directory_incident','file_incident','dns_incident','mixed_incident','desktop_incident')) and not state.get('validated'):raise ValueError('Résous et vérifie l’incident actuel.')
    s=copy.deepcopy(state);da.ensure(s)
    for k in ('directory_incident','file_incident','mixed_incident','desktop_incident'):s.pop(k,None)
    fs=s['file_service'];share=fs['shares'][s['documents_share_id']];uid=s['directory_user_id']
    u=s['directory']['users'][uid];u.update(enabled=True,locked_until=None,failed_attempts=0,must_change_password=False,password_expires_at=now+s['directory']['policy']['password_max_age_seconds'])
    s['directory_service']=True;fs['service_status']='running';fs['firewall_tcp445_allowed']=True;share['enabled']=True
    for layer in ('share_acl','folder_acl'):
        for action in ('list','read'):
            if uid not in share[layer][action]['user_ids']:share[layer][action]['user_ids'].append(uid)
    dns=s['dns_service'];dns.update(service_status='running',transport_allowed=True)
    dns['clients']['client'].update(dns_server_ip=dns['server']['ip'],search_suffix=dns['server']['zone']);dns['cache']['client']={}
    name=s['documents_dns_name'];rid=next((rid for rid,r in dns['records'].items() if r['name']==name and r['type']=='A'),None)
    if rid is None:
        rid='documents-primary';dns['records'][rid]=dict(id=rid,name=name,type='A',value=fs['server']['ip'],ttl=300,enabled=True)
    target=dns['records'][rid];target.update(value=fs['server']['ip'],enabled=True,ttl=300)
    index=s.get('dns_incident_count',0);order=list(FAMILIES)
    random.Random(hashlib.sha256((s['seed']+':dns-incidents:'+str(index//len(order))).encode()).hexdigest()).shuffle(order)
    family=order[index%len(order)]
    baseline=dict(records={x:copy.deepcopy(r) for x,r in dns['records'].items() if x!=rid},technician=copy.deepcopy(dns['clients']['technician']),files=copy.deepcopy(fs['files']))
    wrong='192.0.2.254' if fs['server']['ip']!='192.0.2.254' else '192.0.2.253'
    if family=='wrong_resolver':dns['clients']['client']['dns_server_ip']=wrong
    elif family=='missing_record':target['enabled']=False
    elif family=='wrong_address':target['value']=wrong
    elif family=='service_stopped':dns['service_status']='stopped'
    elif family=='transport_blocked':dns['transport_allowed']=False
    else:
        if family=='negative_cache':target['enabled']=False
        else:target['value']=wrong
        outcome=sim_dns.resolve(dns,'client',dict(name=name,type='A'),da.context(s,'client',now),now)
        dns=outcome['service'];dns['records'][rid].update(value=fs['server']['ip'],enabled=True)
        s['dns_service']=dns
    dns['revision']+=1;sim_dns.validate_dns(dns)
    description=f"{s['requester']}, sur {s['devices']['client']['name']}, ne peut plus ouvrir Documents via {name}. Rétablis la résolution vers le serveur et la lecture du partage. Préserve les autres enregistrements, le poste du technicien et les fichiers."
    s.update(dns_incident=dict(id='INC-DNS-'+str(index+1).zfill(4),family=family,goal='read',title='Partage inaccessible par son nom',description=description,created=now,baseline=baseline),dns_incident_count=index+1,ticket=description,remote_session=False)
    ad.invalidate(s);return s

def public_incident(s):
    i=s.get('dns_incident');return {k:i[k] for k in ('id','title','description','goal','created')} if i else None

def checks(s,now):
    import files_adapter
    resolution,r=da.resolution(s,now)
    ok=resolution['status']=='resolved' and resolution['resolved_ip']==s['file_service']['server']['ip']
    access=files_adapter.access(s,'read',now)
    base=s['dns_incident']['baseline'];dns=s['dns_service']
    preserved=all(dns['records'].get(k)==v for k,v in base['records'].items()) and dns['clients']['technician']==base['technician'] and s['file_service']['files']==base['files']
    return [dict(label='Nom du partage vers le bon serveur',status='valide' if ok else ('inconnu' if r['status']=='unknown' else 'non satisfait'),detail=r['code']),dict(label='Lecture du document partagé',status='valide' if access['allowed'] else 'non satisfait',detail=access['code']),dict(label='Autres enregistrements et fichiers préservés',status='valide' if preserved else 'non satisfait',detail='Comparaison avec l’état de départ.')]
