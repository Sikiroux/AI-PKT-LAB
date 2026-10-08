"""Stock pédagogique persistant. Aucune création implicite d'appareil PT."""
import copy
import hashlib
import sim_deployment


def ensure(state):
    if not state or not state.get('devices') or state.get('_client_view'):return False
    if 'inventory' in state:return False
    suffix=hashlib.sha256((str(state['seed'])+':stock:v1').encode()).hexdigest()[:10].upper()
    state['inventory']={'environment_id':state.get('environment_id','legacy'),'revision':0,'items':{
        'reserve-laptop':{'id':'reserve-laptop','name':'Portable de réserve','serial':'STK-'+suffix,'kind':'laptop','status':'stock','employee_id':None,'prepared':False}},'history':[]}
    return True


def public(state):
    inventory=state['inventory']
    if inventory['environment_id']!=state.get('environment_id','legacy'):raise ValueError('Stock d’un autre environnement.')
    result=copy.deepcopy(inventory)
    for item in result['items'].values():
        if item['status']=='stock':item['prepared']=bool(item.get('deployment') and sim_deployment.evaluate(item['deployment'])['passed'])
    return result


def operate(state,request,now):
    inventory=public(state)
    if type(request.get('expected_revision')) is not int or request['expected_revision']!=inventory['revision']:
        raise ValueError('Le stock a changé. Actualise avant cette opération.')
    item=inventory['items'].get(request.get('item_id'))
    if item is None:raise ValueError('Matériel de stock inconnu.')
    operation=request.get('operation');person=None
    if operation=='prepare':
        if item['status']!='stock':raise ValueError('Restitue le matériel avant sa préparation.')
        raise ValueError('Prépare ce matériel dans l’atelier visuel avant sa remise.')
    elif operation=='assign':
        registry=state.get('company_registry') or {}
        if registry.get('environment_id')!=inventory['environment_id']:raise ValueError('Référentiel de cette entreprise requis.')
        person=registry.get('people',{}).get(request.get('employee_id'))
        if not person or not person.get('represented') or not person.get('account_present'):raise ValueError('Employé représenté inconnu.')
        if item['status']!='stock' or not (item.get('deployment') and sim_deployment.evaluate(item['deployment'])['passed']):raise ValueError('Matériel disponible et préparé requis.')
        item.update(status='assigned',employee_id=person['id'])
    elif operation=='return':
        if item['status']!='assigned':raise ValueError('Ce matériel n’est pas attribué.')
        item.update(status='stock',employee_id=None,prepared=False,cycle=item.get('cycle',0)+1)
        item.pop('deployment',None)
    else:raise ValueError('Opération de stock inconnue.')
    inventory['revision']+=1
    inventory['history'].append({'at':now,'operation':operation,'item_id':item['id'],'employee_id':person['id'] if person else state['inventory']['items'][item['id']]['employee_id']})
    state['inventory']=inventory
    return public(state)


def deployment(state, action, request, now):
    inventory=public(state)
    item=inventory['items'].get(request.get('item_id'))
    if not item or item['status']!='stock':raise ValueError('Matériel disponible en stock requis.')
    cycle=item.get('cycle',0)
    d=item.get('deployment')
    if d is None:
        d=sim_deployment.generate(str(state['seed'])+':stock:'+item['id']+':'+str(cycle),inventory['environment_id'])
        d['station']=item['name']+' · '+item['serial']
    if action=='deployment-operation':
        if type(request.get('expected_cycle')) is not int or request['expected_cycle']!=cycle:
            raise ValueError('Le cycle de préparation a changé. Rouvre ce matériel.')
        if request.get('operation')=='reset':
            if type(request.get('expected_revision')) is not int or request['expected_revision']!=d['revision']:
                raise ValueError('L’atelier a changé. Actualise avant de poursuivre.')
            fresh=sim_deployment.generate(d['seed'],inventory['environment_id'])
            fresh.update(station=d['station'],revision=d['revision']+1,attempt=d['attempt']+1);d=fresh
        else:d=sim_deployment.apply(d,request.get('operation'),request.get('payload',{}),request.get('expected_revision'))
        item['deployment']=d;item['prepared']=sim_deployment.evaluate(d)['passed']
        inventory['revision']+=1
        inventory['history'].append(dict(at=now,operation='deployment',item_id=item['id'],employee_id=None,stage=d['stage'],passed=item['prepared']))
        state['inventory']=inventory
    elif action!='deployment-state':raise ValueError('Action de préparation inconnue.')
    return dict(service=copy.deepcopy(d),result=sim_deployment.evaluate(d),item_id=item['id'],cycle=cycle)
