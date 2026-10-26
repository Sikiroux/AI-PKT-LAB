"""Collecte par trajet ; une identité manquante ne valide jamais son contrôle."""

def collect(engine, state, found, clock, accelerate=False):
    jobs=[('remote','technician','client'),('share','client','server'),('directory','technician','server')]
    if 'desktop_services' in state:
        jobs.append(('printing','client',state['desktop_services']['printing']['printer']['device_role']))
    outside=state.get('technician_locations',{}).get('outside')
    gateway=outside and (state.get('technician_session') or {}).get('location')=='outside'
    if gateway:jobs.append(('vpn_gateway','technician',None))
    probes={};ready=[]
    def result(key,source,target,ping):
        ping=ping if isinstance(ping,dict) else {'detail':'Réponse de contrôle invalide.'}
        probes[key]=dict(at=clock(),source='Packet Tracer',
            status={'valide':'passed','non satisfait':'failed'}.get(ping.get('status'),'unknown'),
            detail=ping.get('detail',''),
            source_device=found.get(source,{}).get('name',state['devices'].get(source,{}).get('name')),target=target)
    for key,source,role in jobs:
        target=outside.get('gateway') if role is None else state['devices'].get(role,{}).get('ip')
        if source not in found or (role is not None and role not in found) or not target:
            missing=[r for r in (source,role) if r is not None and r not in found]
            names=', '.join(state['devices'].get(r,{}).get('name',r) for r in dict.fromkeys(missing))
            result(key,source,target,dict(detail=('Appareil absent ou identité ambiguë : '+names if names else 'Adresse cible absente')+' ; trajet non vérifié.'))
        else:ready.append((key,source,target))
    if not ready:return probes
    if callable(getattr(type(engine),'quiet_pings',None)):
        try:
            rows=engine.quiet_pings([(found[source]['name'],target) for _,source,target in ready],accelerate=accelerate)
            if not isinstance(rows,list) or len(rows)!=len(ready):raise ValueError('Nombre de résultats ICMP incohérent.')
        except Exception as error:
            rows=[dict(detail='Contrôle discret indisponible : '+str(error)) for _ in ready]
        for (key,source,target),row in zip(ready,rows):result(key,source,target,row)
    else:
        for key,source,target in ready:
            try:row=engine.ping(found[source]['name'],target)
            except Exception as error:row=dict(detail='Contrôle indisponible : '+str(error))
            result(key,source,target,row)
    return probes
