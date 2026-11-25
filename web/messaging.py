"""Messagerie interne liée aux tickets, indépendante de leur fil d'intervention."""
import copy
import hashlib
import json

DEFAULT_QUESTIONS={'scope':'Poste et ressource','when':'Depuis quand ?', 'network':'Connexion réseau','ip':'Accès par IP','name':'Accès par nom','login':'Session utilisateur','save':'Enregistrer','retest':'Réessayer'}

def message_key(message):
    return hashlib.sha256(json.dumps(message,sort_keys=True,ensure_ascii=False).encode()).hexdigest()[:24]

def channels(tickets):
    result=[]
    for t in tickets.state['tickets']:
        if t.get('kind')!='workspace':continue
        context=t.get('request_context') or {}
        messages=copy.deepcopy(t.get('dialogue',[]))
        seen=t.get('messaging_seen',[])
        for message in messages:
            message['key']=message_key(message)
            message['exported']=message['key'] in t.get('messaging_exported_keys',[])
        available=t.get('stage')!='queued' and t.get('status') not in ('clos','resolu') and (t.get('live_incident') or t['id'].startswith(('INC-MIX-','INC-APP-')))
        questions=t.get('dialogue_questions') or ({'scope':'Configuration demandée','when':'Contexte de la demande','retest':'Préparation terminée ?'} if t.get('workspace_goal') in ('deployment','workstation_setup') else DEFAULT_QUESTIONS)
        result.append(dict(id=t['id'],title=t.get('title',t['id']),requester=context.get('requester') or context.get('requester_name') or t.get('name','Demandeur'),station=t.get('name',''),status=t.get('status'),messages=messages,pinned=t.get('messaging_pinned',False),unread=sum(m['key'] not in seen for m in messages),questions=questions if available else {},available=bool(available)))
    return dict(environment_id=(tickets.state.get('site') or {}).get('environment_id'),channels=sorted(result,key=lambda c:not c['pinned']))

def operate(tickets,data):
    t=tickets.get(data.get('ticket_id'))
    if t.get('kind')!='workspace':raise ValueError('Conversation indisponible pour cette demande.')
    action=data.get('operation')
    if action=='read':
        keys=data.get('keys');known={message_key(m) for m in t.get('dialogue',[])}
        if not isinstance(keys,list) or len(keys)>60 or any(not isinstance(k,str) or k not in known for k in keys):raise ValueError('Position de lecture invalide.')
        t['messaging_seen']=list((set(t.get('messaging_seen',[]))|set(keys))&known);tickets.save()
    elif action=='pin':
        if type(data.get('pinned')) is not bool:raise ValueError('État d’épingle invalide.')
        t['messaging_pinned']=data['pinned'];tickets.save()
    elif action=='ask':
        channel=next(c for c in channels(tickets)['channels'] if c['id']==t['id'])
        if not channel['available'] or data.get('question') not in channel['questions']:raise ValueError('Question indisponible. Actualise la conversation.')
        tickets.controller.dialogue(dict(ticket_id=t['id'],question=data['question']))
    elif action=='export':
        key=data.get('key');message=next((m for m in t.get('dialogue',[]) if message_key(m)==key),None)
        if message is None:raise ValueError('Message inconnu. Actualise la conversation.')
        if key in t.get('messaging_exported_keys',[]):return channels(tickets)
        text=('Échange avec le demandeur — '+t['id']+'\n'+str(message.get('question',''))+'\n'+str(message.get('answer','')))[:2000]
        tickets.add_followup(t,dict(entry_kind='followup',visibility='private',text=text))
        t.setdefault('messaging_exported_keys',[]).append(key);tickets.save()
    else:raise ValueError('Action de messagerie inconnue.')
    return channels(tickets)
