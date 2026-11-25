"""Panne IPv4 ciblée dans Packet Tracer ; mutations journalisées et contrôlées."""
import time
from contextlib import nullcontext
import live_faults
import client_workspaces
from workspace_model import evaluate
import directory_adapter


def supported(controller):
    engine=getattr(controller,'engine',None)
    return all(callable(getattr(type(engine),name,None)) for name in ('snapshot','call','quiet_pings'))

def guard_pending(state):
    if any(r.get('state') in ('pending','uncertain') or (r.get('state')=='applied' and ident not in state.get('live_incidents',{})) for ident,r in state.get('network_injections',{}).items()):
        targets=', '.join(sorted({r.get('mutation',{}).get('device') or r.get('target_serial','poste inconnu') for ident,r in state.get('network_injections',{}).items() if r.get('state') in ('pending','uncertain') or (r.get('state')=='applied' and ident not in state.get('live_incidents',{}))}))
        raise ValueError('Injection réseau non confirmée sur '+targets+'. Rétablis sa configuration de référence dans Packet Tracer, puis réessaie de recevoir un incident.')

def reconcile(tickets):
    c=tickets.controller;s=c.workspace.state
    pending=[r for ident,r in s.get('network_injections',{}).items() if r.get('state') in ('pending','uncertain') or (r.get('state')=='applied' and ident not in s.get('live_incidents',{}))]
    if not pending:return
    try:
        with getattr(c.engine,'lock',nullcontext()):
            snapshot=c.engine.snapshot();tickets.guard(snapshot)
            for record in pending:
                if live_faults.matches(snapshot,record['mutation'],True):record['state']='restored'
        c.workspace.save()
    except Exception:pass

def inject(tickets,serial,ident,seed,fault='ip_wrong'):
    c=tickets.controller;s=c.workspace.state
    guard_pending(s)
    c.observe(blocking=True,client_serial=serial,accelerate=True)
    v=client_workspaces.project(s,serial)
    if not evaluate(v,'remote',time.time())['allowed'] or directory_adapter.context(v,now=time.time())['network']['status']!='passed':
        raise ValueError('Le poste et le serveur doivent être joignables avant de préparer une panne réseau.')
    with getattr(c.engine,'lock',nullcontext()):
        snapshot=c.engine.snapshot();tickets.guard(snapshot)
        candidates=[d for d in snapshot['devices'] if d.get('serial')==serial and d.get('name')==v['devices']['client']['name']]
        if len(candidates)!=1:raise ValueError('Identité réseau du poste non confirmée.')
        target=candidates[0]
        if fault not in ('ip_wrong','mask_wrong') or fault not in live_faults.choices(target):raise ValueError('Cette panne exige un poste IPv4 statique et une API modifiable.')
        mutation=live_faults.plan(target,fault,snapshot,seed,target=v['devices']['client'].get('gateway') or s['devices']['server']['ip'])
        if mutation['before']['ip']!=v['devices']['client']['ip'] or mutation['before']['mask']!=(v['devices']['client'].get('mask') or '255.255.255.0'):raise ValueError('Configuration IPv4 du poste différente de la référence : rétablis son état initial avant injection.')
        record=dict(state='pending',target_serial=serial,mutation=mutation,created_at=time.time())
        s.setdefault('network_injections',{})[ident]=record;c.workspace.save()
        try:
            reply=c.engine.call(live_faults.apply_js(mutation))
            if reply!='ok' or not live_faults.matches(c.engine.snapshot(),mutation):raise ValueError('Mutation IPv4 non confirmée.')
            record['state']='applied';c.workspace.save()
        except Exception:
            rollback(c,record)
            raise
    try:c.observe(blocking=True,client_serial=serial,accelerate=True)
    except Exception:
        with getattr(c.engine,'lock',nullcontext()):rollback(c,record)
        raise
    v=client_workspaces.project(s,serial)
    proof=evaluate(v,'remote',time.time())
    server_status=directory_adapter.context(v,now=time.time())['network']['status']
    if 'failed' not in (proof['status'],server_status):
        with getattr(c.engine,'lock',nullcontext()):rollback(c,record)
        raise ValueError('L’effet réseau de la panne n’est pas confirmé ; aucun ticket réseau créé.')
    record['effect_confirmed_at']=time.time();c.workspace.save()
    return record

def rollback(c,record):
    mutation=record['mutation']
    try:
        snapshot=c.engine.snapshot()
        if live_faults.matches(snapshot,mutation,True):record['state']='restored'
        elif live_faults.matches(snapshot,mutation):
            if c.engine.call(live_faults.apply_js(mutation,True))!='ok' or not live_faults.matches(c.engine.snapshot(),mutation,True):raise ValueError('Rétablissement non confirmé.')
            record['state']='restored'
        else:record['state']='uncertain'
    except Exception:record['state']='uncertain'
    c.workspace.save()

def refresh(tickets,ticket):
    c=tickets.controller;s=c.workspace.state;record=s.get('network_injections',{}).get(ticket['id'])
    if not record:return
    try:
        with getattr(c.engine,'lock',nullcontext()):
            snapshot=c.engine.snapshot();tickets.guard(snapshot)
            restored=live_faults.matches(snapshot,record['mutation'],True)
            devices=[d for d in snapshot['devices'] if d.get('serial')==record['mutation']['serial'] or d.get('name')==record['mutation']['device']]
            identifiable=len(devices)==1 and devices[0].get('serial')==record['mutation']['serial'] and devices[0].get('name')==record['mutation']['device']
            ports=[p for p in devices[0].get('ports',[]) if p.get('name')==record['mutation']['port']] if identifiable else []
            readable=len(ports)==1 and all(ports[0].get(k) is not None for k in ('ip','mask','dhcp_client'))
        record['verification']=dict(at=time.time(),status=('passed' if restored else 'failed') if readable else 'unknown')
    except Exception:record['verification']=dict(at=time.time(),status='unknown')
    c.workspace.save()

def checks(s,ticket,at):
    record=s.get('network_injections',{}).get(ticket['id'])
    if not record or record['target_serial']!=ticket['target_serial']:return [dict(label='Configuration réseau du poste',status='inconnu',detail='Injection réseau non identifiable.')]
    v=client_workspaces.project(s,ticket['target_serial']);proof=record.get('verification',{})
    status=proof.get('status','unknown') if 0<=at-proof.get('at',0)<=directory_adapter.TTL else 'unknown'
    remote=evaluate(v,'remote',at);server=directory_adapter.context(v,now=at)['network']
    def row(label,status,detail):return dict(label=label,status={'passed':'valide','failed':'non satisfait'}.get(status,'inconnu'),detail=detail)
    return [row('Configuration IPv4 de référence rétablie',status,'Lecture de la configuration réelle dans Packet Tracer ; aucune réparation automatique.'),row('Poste joignable depuis le technicien',remote['status'],'Contrôle ICMP ciblé du poste attendu.'),row('Serveur joignable depuis le poste',server['status'],'Contrôle réseau depuis le poste du demandeur ; aucun droit applicatif n’est validé par ce ping.')]
