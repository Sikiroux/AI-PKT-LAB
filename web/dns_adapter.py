"""DNS simulé : état persistant et contexte provenant des observations PT."""
import time
import directory_adapter as ad
import sim_dns

def ensure(s):
    if not s or 'directory' not in s or 'dns_service' in s:return False
    server=s['devices']['server'];zone=s['directory']['domain']['dns_name'].lower()
    name=server['name'].lower()+'.'+zone
    clients=[dict(id=role,name=s['devices'][role]['name'],dns_server_ip=server['ip'],search_suffix=zone) for role in ('client','technician')]
    s['dns_service']=sim_dns.generate_dns(s['seed'],s.get('environment_id','legacy'),dict(id='server',name=server['name'],ip=server['ip'],zone=zone),clients,[dict(id='documents',dns_name=name,ipv4=server['ip'])],time.time())
    s['documents_dns_name']=name
    return True

def context(s,source,now):
    net=ad.context(s,source=source,now=now)['network']
    return dict(environment_id=s.get('environment_id','legacy'),source_device_id=source,target_device_id='server',network=dict(status={'passed':'up','failed':'down'}.get(net['status'],'unknown'),observed_at=net['observed_at'],valid_until=net['valid_until'],source_device_id=source,target_device_id='server',target_ip=s['devices']['server']['ip'],evidence='icmp_proxy'))

def actor(s,source='technician',admin=False):
    return dict(id=source,device_id=source,environment_id=s.get('environment_id','legacy'),permissions=[sim_dns.CAPABILITY_DNS_MANAGE if admin else sim_dns.CAPABILITY_DNS_FLUSH_OWN])

def resolution(s,now):
    outcome=sim_dns.resolve(s['dns_service'],'client',dict(name=s['documents_dns_name'],type='A'),context(s,'client',now),now)
    r=outcome['result']
    # Une réponse négative est définitive mais n'autorise aucun accès fichier.
    status='resolved' if r['code']=='OK' and r['addresses'] else ('unknown' if r['status']=='unknown' else 'failed')
    return dict(status=status,resolved_ip=r['addresses'][0] if r['addresses'] else None,observed_at=r['observed_at'] if r['observed_at'] is not None else now,valid_until=r['valid_until'] if r['valid_until'] is not None else now),r
