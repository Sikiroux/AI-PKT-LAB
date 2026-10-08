"""Comptes locaux de formation et registre de credentials, distincts d’AD."""
import copy
import hashlib
import hmac

def digest(env,serial,password):
    return hashlib.sha256((env+':local-access:'+serial+':'+password).encode()).hexdigest()

def ensure(state,rows):
    env=state.get('environment_id','legacy')
    model=state.get('local_access')
    if model is not None and model['environment_id']!=env:raise ValueError('Accès locaux d’un autre environnement.')
    if model is None:
        model={'environment_id':env,'revision':0,'accounts':{},'vault':{},'sessions':{},'history':[]}
        state['local_access']=model
    for p in rows:
        if not (p.get('remote_supported') or p.get('role')=='technician'):continue
        serial=p['serial']
        if serial in model['accounts']:continue
        token=hashlib.sha256((str(state.get('seed'))+':local-access:v1:'+serial).encode()).hexdigest()[:12]
        password='Lab!'+token+'A7'
        model['accounts'][serial]={'username':'support.local','enabled':True,'password_hash':digest(env,serial,password)}
        model['vault'][serial]={'password':password,'updated_at':None}
    return model

def public(state,serial):
    m=state['local_access'];a=m['accounts'][serial]
    return {'revision':m['revision'],'username':a['username'],'enabled':a['enabled'],'authenticated':bool(m['sessions'].get(serial)),
            'updated_at':m['vault'][serial]['updated_at'],'history':copy.deepcopy([e for e in m['history'] if e['station_serial']==serial][-20:])}

def operate(state,serial,request,now):
    m=copy.deepcopy(state['local_access']);op=request.get('operation')
    if m['environment_id']!=state.get('environment_id','legacy'):raise ValueError('Environnement incohérent.')
    if serial not in m['accounts']:raise ValueError('Compte local inconnu.')
    a=m['accounts'][serial];secret=None;result=None
    if op in ('reveal','reset','enable'):
        revision=request.get('expected_revision')
        if type(revision) is not int or revision!=m['revision']:raise ValueError('Accès modifiés : actualise la fiche.')
        if op=='reveal':secret=m['vault'][serial]['password']
        elif op=='reset':
            password=request.get('password')
            if not isinstance(password,str) or not 12<=len(password)<=128:raise ValueError('Mot de passe local de formation : 12 à 128 caractères.')
            a['password_hash']=digest(m['environment_id'],serial,password)
            m['vault'][serial]={'password':password,'updated_at':now};m['sessions'].pop(serial,None);m['revision']+=1
        else:
            value=request.get('enabled')
            if type(value) is not bool:raise ValueError('État oui/non requis.')
            a['enabled']=value;m['sessions'].pop(serial,None);m['revision']+=1
    elif op=='login':
        password=request.get('password');username=request.get('username')
        allowed=a['enabled'] and isinstance(password,str) and username=='.\\'+a['username'] and hmac.compare_digest(a['password_hash'],digest(m['environment_id'],serial,password))
        m['sessions'].pop(serial,None)
        if allowed:m['sessions'][serial]={'at':now,'username':a['username']}
        result={'allowed':bool(allowed),'code':'LOCAL_AUTHENTICATED' if allowed else 'LOCAL_AUTHENTICATION_FAILED'}
    elif op=='logout':m['sessions'].pop(serial,None);result={'allowed':False,'code':'LOCAL_LOGGED_OUT'}
    else:raise ValueError('Opération locale inconnue.')
    m['history'].append({'at':now,'operation':op,'station_serial':serial,'allowed':result['allowed'] if result else None})
    m['history']=m['history'][-200:];state['local_access']=m
    response=public(state,serial)
    if secret is not None:response['password']=secret
    if result:response['result']=result
    return response
