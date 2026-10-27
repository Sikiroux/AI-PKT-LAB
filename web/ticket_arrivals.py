"""File procédurale de demandes ; aucune panne injectée à la réception."""
import hashlib
import random
import time
import timers
import ticket_wording

APP_TARGETS=('printing','ftp','endpoint','peripherals','deployment','workstation_setup')
VARIED=(('apps','printing'),('apps','ftp'),('apps','endpoint'),('apps','peripherals'),('mixed','ad'),('mixed','files'),('mixed','dns'))

def receive(tickets,engine='varied',target='random',level=1,minutes=30,client_serial='random',discovery_delay=0):
    if getattr(tickets,'desk',None) and tickets.desk.settings.get('preparing') is True:raise ValueError('Commence la simulation avant de créer un incident.')
    s=tickets.controller.workspace.state
    if not s or s.get('environment_id')!=(tickets.state.get('site') or {}).get('environment_id'):raise ValueError('Entreprise active requise.')
    if engine not in ('varied','apps','mixed') or type(level) is not int or level not in (1,2,3):raise ValueError('Catalogue ou niveau inconnu.')
    if type(minutes) is not int or not 0<=minutes<=1440:raise ValueError('Durée invalide.')
    if s.get('staff_size')==30:
        import enterprise_incidents
        chosen='random' if engine=='varied' else target
        return enterprise_incidents.receive(tickets,chosen,minutes,client_serial,engine=engine,discovery_delay=discovery_delay)
    index=tickets.state.get('arrival_count',0)+1
    seed=hashlib.sha256((str(s['seed'])+':ticket-arrivals:v1:'+str(index)).encode()).hexdigest()
    rng=random.Random(seed)
    previous=next((t for t in reversed(tickets.state['tickets']) if t.get('arrival_plan')),None)
    previous_plan=previous.get('arrival_plan',{}) if previous else {}
    if engine=='varied':
        choices=[x for x in VARIED if x[1]!=previous_plan.get('target')] or list(VARIED)
        if len(s.get('client_workspaces',{}))>1 and previous_plan.get('client_serial')==s['devices']['client']['serial']:
            choices=[x for x in choices if x[0]=='apps'] or choices
        selected,target=rng.choice(choices)
    elif engine=='apps':
        if target not in ('random',*APP_TARGETS):raise ValueError('Application inconnue.')
        selected='apps';target=rng.choice([x for x in APP_TARGETS if x!=previous_plan.get('target')] or list(APP_TARGETS)) if target=='random' else target
    else:
        if target not in ('random','ad','files','dns'):raise ValueError('Les arrivées multi-services concernent AD, fichiers et DNS. Les pannes réseau restent des interventions manuelles.')
        selected='mixed';target=rng.choice(('ad','files','dns')) if target=='random' else target
    candidates=sorted(s.get('client_workspaces',{})) or [s['devices']['client']['serial']]
    alternatives=[x for x in candidates if x!=previous_plan.get('client_serial')] or candidates
    serial=rng.choice(alternatives) if selected=='apps' and client_serial=='random' else s['devices']['client']['serial'] if selected=='mixed' else client_serial
    if serial not in candidates:raise ValueError('Poste inconnu pour cette entreprise.')
    profile=s.get('client_workspaces',{}).get(serial)
    name=profile['device']['name'] if profile else s['devices']['client']['name']
    requester=profile['requester'] if profile else s['requester']
    wording=ticket_wording.compose(seed,target,requester,s['company'],name,serial)
    if target in ('files','dns','ad'):
        wording['request_context'].update(resource='\\\\'+s['devices']['server']['name']+'\\Documents',resource_scope='remote')
    ident=('INC-APP-Q' if selected=='apps' else 'INC-MIX-Q')+str(index).zfill(4)
    plan={'version':1,'seed':seed,'index':index,'engine':selected,'target':target,'level':level,'minutes':minutes,'client_serial':serial}
    ticket={'id':ident,'kind':'workspace','name':name,'target_serial':serial,**wording,
       'workspace_goal':'pending','status':'nouveau','stage':'queued','created':time.strftime('%Y-%m-%d %H:%M:%S'),
       'checks':[],'complete':False,'notes':'','dialogue':[],'arrival_plan':plan,'timer':timers.configure(minutes,'training')}
    tickets.state['tickets'].append(ticket);tickets.state['arrival_count']=index
    import company_registry
    company_registry.ensure(s);company_registry.link_tickets(s,tickets.state['tickets'])
    tickets.event(ident+' : demande reçue en file d’attente, sans modification de l’environnement.')
    return tickets.public()

def activate(tickets,ticket):
    if ticket.get('stage')!='queued':return
    others=[t for t in tickets.state['tickets'] if t['id']!=ticket['id'] and t['kind']=='workspace' and t['status']!='clos' and t.get('stage')!='queued']
    if others:raise ValueError('Termine et clôture l’intervention préparée avant d’activer celle-ci. Les autres demandes restent en attente.')
    c=tickets.controller;p=ticket['arrival_plan'];s=c.workspace.state
    timer=ticket.get('timer') or {}
    minutes=timer.get('limit',p['minutes']*60)//60
    active=next((s[k] for k in ('desktop_incident','mixed_incident','directory_incident','file_incident','dns_incident') if s.get(k)),None)
    closed_active=bool(active and any(t['id']==active['id'] and t['status']=='clos' for t in tickets.state['tickets']))
    if active and not closed_active and not s.get('validated'):raise ValueError('Un exercice non terminé utilise déjà cet environnement.')
    callback=c.on_change;c.on_change=None
    try:
        if p['engine']=='apps':
            if p['target']!='peripherals':c.observe(blocking=True,client_serial=p['client_serial'],accelerate=True)
            if closed_active:c.workspace.state['validated']=True
            c.next_desktop_incident(p['target'],minutes,client_serial=p['client_serial'],generation_seed=p['seed'])
        else:
            c.observe(blocking=True,client_serial=s['devices']['client']['serial'],accelerate=True)
            if closed_active:c.workspace.state['validated']=True
            c.next_mixed_incident(p['level'],p['target'],minutes,include_network=False,generation_seed=p['seed'])
        s=c.workspace.state
        incident=s.get('desktop_incident') or s.get('mixed_incident')
        incident.update(id=ticket['id'],target_serial=p['client_serial'],target_name=ticket['name'],timer_minutes=minutes)
        if ticket.get('request_context'):incident['title']=ticket['title']
        ticket.update(stage='prepared',title=incident['title'],description=incident['description'],workspace_goal=incident['goal'])
        c.workspace.save()
        if callback:callback(s,c.workspace.path.parent)
    finally:c.on_change=callback
