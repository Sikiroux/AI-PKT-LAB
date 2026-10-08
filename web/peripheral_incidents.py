"""Incidents locaux procéduraux : symptômes et validation indépendants d’ICMP."""
import copy
import hashlib
import random
import sim_peripherals as hardware

CAUSES=(('monitor','power'),('monitor','connection'),('monitor','input'),('monitor','working'),
        ('keyboard','connection'),('keyboard','working'),('mouse','connection'),('mouse','working'),('mouse','absent'))

def preserved_state(state):
    """Comparer la configuration, sans confondre caches/journaux avec des dégâts."""
    result={k:copy.deepcopy(state[k]) for k in ('devices','directory','file_service','dns_service') if k in state}
    for key in ('directory','file_service','dns_service'):
        if key in result:
            result[key].pop('revision',None);result[key].pop('audit',None)
    if 'directory' in result:
        for user in result['directory']['users'].values():user.pop('failed_attempts',None)
    if 'dns_service' in result:result['dns_service'].pop('cache',None)
    return result

def prepare(state,now,minutes,generation_seed=None):
    s=copy.deepcopy(state);serial=s['devices']['client']['serial']
    hardware.ensure(s,[{'serial':serial,'remote_supported':True}])
    if not all(c['available'] for c in hardware.evaluate(s['peripherals'],serial).values()):
        raise ValueError('Rétablis les accessoires locaux de ce poste avant le nouvel exercice.')
    index=s.get('desktop_incident_count',0)+1
    rng=random.Random(hashlib.sha256((str(generation_seed or s['seed'])+':peripheral-incidents:v1:'+str(1 if generation_seed else index)+':'+serial).encode()).hexdigest())
    kind,cause=rng.choice(CAUSES)
    item=next(i for i in s['peripherals']['items'].values() if i['station_serial']==serial and i['kind']==kind)
    others=copy.deepcopy({k:i for k,i in s['peripherals']['items'].items() if i['station_serial'] not in (None,serial)})
    baseline=preserved_state(s)
    if cause=='absent':item['station_serial']=None
    elif cause=='input':item['input']='DisplayPort'
    else:item[cause if cause!='connection' else 'connected']=False
    s['peripherals']['revision']+=1
    descriptions={'monitor':'Je n’ai plus d’image sur mon écran externe.','keyboard':'Mon clavier externe ne permet plus de saisir du texte.','mouse':'Je ne peux plus utiliser ma souris externe.'}
    text=f"{s['requester']} : « {descriptions[kind]} » Poste {s['devices']['client']['name']} ({serial}). Interviens sur place dans Fiches des postes → Équipement local. Rétablis les trois accessoires externes et préserve les autres postes, comptes et services. Une connexion distante réussie ne prouve pas que ces accessoires fonctionnent."
    for key in ('desktop_incident','mixed_incident','directory_incident','file_incident','dns_incident'):s.pop(key,None)
    s.update(desktop_incident={'id':'INC-APP-'+str(index).zfill(4),'title':'Accessoire du poste inutilisable','family':'peripherals','goal':'local_peripherals',
       'description':text,'created':now,'timer_minutes':minutes,'dialogue':[],'target_serial':serial,'target_name':s['devices']['client']['name'],
       'cause':cause,'kind':kind,'baseline':baseline,'other_peripherals':others},desktop_incident_count=index,ticket=text,validated=False)
    return s

def checks(s):
    incident=s['desktop_incident'];serial=incident['target_serial'];m=s.get('peripherals')
    if not m or m['environment_id']!=s.get('environment_id','legacy'):
        return [{'label':'Accessoires locaux du poste','status':'inconnu','detail':'Équipement non disponible.'}]
    rows=[{'label':hardware.KINDS[k]+' externe opérationnel','status':'valide' if c['available'] else 'non satisfait','detail':'État local simulé ; aucun ping requis.'} for k,c in hardware.evaluate(m,serial).items()]
    preserved=preserved_state(s)==incident['baseline'] and all(m['items'].get(k)==v for k,v in incident['other_peripherals'].items())
    rows.append({'label':'Autres postes, comptes et services préservés','status':'valide' if preserved else 'non satisfait','detail':'Comparaison avec le début de cette intervention.'})
    return rows

def answer(s,question):
    i=s['desktop_incident']
    if question=='scope':return i['description']
    if question=='when':return 'Les accessoires externes fonctionnaient lors de ma précédente utilisation.'
    if question=='retest':return 'Les trois accessoires sont de nouveau utilisables.' if all(r['status']=='valide' for r in checks(s)) else 'Les accessoires ne sont pas encore tous utilisables.'
    return 'Le symptôme concerne les accessoires externes du poste. Une session distante ou un ping ne teste pas leur fonctionnement local.'
