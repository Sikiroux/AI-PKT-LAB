"""Périphériques locaux pédagogiques, sans influence sur le réseau ou RDP."""
import copy
import hashlib

KINDS={'monitor':'Écran','keyboard':'Clavier','mouse':'Souris'}

def ensure(state, workstations):
    env=state.get('environment_id','legacy')
    model=state.get('peripherals')
    if model is not None and model.get('environment_id')!=env:
        raise ValueError('Périphériques d’un autre environnement.')
    if model is None:
        model={'environment_id':env,'revision':0,'items':{},'history':[]}
        state['peripherals']=model
    for p in workstations:
        if not (p.get('remote_supported') or p.get('role')=='technician'):continue
        serial=p['serial']
        for kind in KINDS:
            key=hashlib.sha256((str(state.get('seed'))+':peripherals:v1:'+serial+':'+kind).encode()).hexdigest()[:16]
            if key not in model['items']:
                model['items'][key]={'id':key,'serial':'PER-'+key.upper(),'kind':kind,'station_serial':serial,
                    'working':True,'connected':True,'power':True,'input':'HDMI'}
    return model

def evaluate(model, serial):
    items=[i for i in model['items'].values() if i['station_serial']==serial]
    def ready(kind):
        i=next((i for i in items if i['kind']==kind),None)
        if not i:return {'available':False,'code':'ABSENT'}
        if not i['working']:return {'available':False,'code':'HARDWARE_FAILED'}
        if not i['connected']:return {'available':False,'code':'CABLE_DISCONNECTED'}
        if kind=='monitor' and not i['power']:return {'available':False,'code':'POWER_OFF'}
        if kind=='monitor' and i['input']!='HDMI':return {'available':False,'code':'WRONG_INPUT'}
        return {'available':True,'code':'READY'}
    return {k:ready(k) for k in KINDS}

def public(state, serial):
    m=state['peripherals']
    if m['environment_id']!=state.get('environment_id','legacy'):raise ValueError('Environnement incohérent.')
    return {'revision':m['revision'],'items':copy.deepcopy([i for i in m['items'].values() if i['station_serial'] in (None,serial)]),
            'checks':evaluate(m,serial),'history':copy.deepcopy([e for e in m['history'] if e['station_serial']==serial][-30:])}

def operate(state, serial, request, now):
    original=state['peripherals']
    revision=request.get('expected_revision')
    if type(revision) is not int or revision!=original['revision']:raise ValueError('Équipement modifié : actualise la fenêtre.')
    if original['environment_id']!=state.get('environment_id','legacy'):raise ValueError('Environnement incohérent.')
    m=copy.deepcopy(original);op=request.get('operation');item=None
    if op=='add':
        kind=request.get('kind')
        if kind not in KINDS:raise ValueError('Type de périphérique inconnu.')
        key=hashlib.sha256((m['environment_id']+':added:'+str(m['revision'])).encode()).hexdigest()[:16]
        if key in m['items']:raise ValueError('Identité déjà utilisée.')
        item={'id':key,'serial':'PER-'+key.upper(),'kind':kind,'station_serial':None,'working':True,'connected':True,'power':True,'input':'HDMI'}
        m['items'][key]=item
    else:
        item=m['items'].get(request.get('item_id'))
        if not item or item['station_serial'] not in (None,serial):raise ValueError('Périphérique hors du poste sélectionné.')
        if op=='attach':
            if item['station_serial'] is not None:raise ValueError('Périphérique déjà installé.')
            for old in m['items'].values():
                if old['station_serial']==serial and old['kind']==item['kind']:old['station_serial']=None
            item['station_serial']=serial
        elif op=='detach':
            if item['station_serial']!=serial:raise ValueError('Périphérique non installé.')
            item['station_serial']=None
        elif op in ('connection','power','input'):
            if item['station_serial']!=serial:raise ValueError('Installe le périphérique avant de le régler.')
            value=request.get('value')
            if op=='input':
                if item['kind']!='monitor' or value not in ('HDMI','DisplayPort'):raise ValueError('Entrée invalide.')
                item['input']=value
            else:
                if type(value) is not bool:raise ValueError('Valeur oui/non requise.')
                if op=='power' and item['kind']!='monitor':raise ValueError('Commande réservée à l’écran.')
                item['connected' if op=='connection' else 'power']=value
        else:raise ValueError('Opération inconnue.')
    m['revision']+=1
    m['history'].append({'at':now,'operation':op,'item_id':item['id'],'serial':item['serial'],'station_serial':serial})
    m['history']=m['history'][-200:]
    state['peripherals']=m
    return public(state,serial)
