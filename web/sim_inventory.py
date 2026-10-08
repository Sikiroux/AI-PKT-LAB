"""Stock pédagogique persistant. Aucune création implicite d'appareil PT."""
import copy
import hashlib


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
    return copy.deepcopy(inventory)


def operate(state,request,now):
    inventory=public(state)
    if type(request.get('expected_revision')) is not int or request['expected_revision']!=inventory['revision']:
        raise ValueError('Le stock a changé. Actualise avant cette opération.')
    item=inventory['items'].get(request.get('item_id'))
    if item is None:raise ValueError('Matériel de stock inconnu.')
    operation=request.get('operation');person=None
    if operation=='prepare':
        if item['status']!='stock':raise ValueError('Restitue le matériel avant sa préparation.')
        item['prepared']=True
    elif operation=='assign':
        registry=state.get('company_registry') or {}
        if registry.get('environment_id')!=inventory['environment_id']:raise ValueError('Référentiel de cette entreprise requis.')
        person=registry.get('people',{}).get(request.get('employee_id'))
        if not person or not person.get('represented') or not person.get('account_present'):raise ValueError('Employé représenté inconnu.')
        if item['status']!='stock' or not item['prepared']:raise ValueError('Matériel disponible et préparé requis.')
        item.update(status='assigned',employee_id=person['id'])
    elif operation=='return':
        if item['status']!='assigned':raise ValueError('Ce matériel n’est pas attribué.')
        item.update(status='stock',employee_id=None,prepared=False)
    else:raise ValueError('Opération de stock inconnue.')
    inventory['revision']+=1
    inventory['history'].append({'at':now,'operation':operation,'item_id':item['id'],'employee_id':person['id'] if person else state['inventory']['items'][item['id']]['employee_id']})
    state['inventory']=inventory
    return public(state)
