"""Mail, licences et demandes d'arrivée simulés ; opérations atomiques sans IO."""
import copy
import hashlib
import re
import unicodedata
import sim_deployment


def policy(state):
    seed=str(state.get('seed','legacy'))
    digest=hashlib.sha256((seed+':corporate:v1').encode()).hexdigest()
    slug=re.sub(r'[^a-z0-9]+','-',unicodedata.normalize('NFKD',str(state.get('company','entreprise'))).encode('ascii','ignore').decode().lower()).strip('-') or 'entreprise'
    return dict(domain=slug[:40]+'.example',naming='prenom.nom',approval='Responsable du service',notice_days=3+int(digest[0],16)%5,retention_days=30+int(digest[1],16)%3*15)


def ensure(state):
    if not state or not state.get('directory') or state.get('_client_view'):return False
    if 'corporate' in state:
        if state['corporate'].get('version')!=1 or state['corporate']['environment_id']!=state.get('environment_id','legacy'):raise ValueError('Services d’une autre entreprise.')
        return False
    users=state['directory']['users'];p=policy(state);boxes={}
    for uid,u in users.items():
        address=u['username'].lower()+'@'+p['domain']
        boxes[uid]=dict(id=uid,user_id=uid,address=address,enabled=True,quota_bytes=100000,messages=[])
    welcome='accueil';index=1
    while any(b['address']==welcome+'@'+p['domain'] for b in boxes.values()):
        index+=1;welcome='accueil'+str(index)
    boxes['company-welcome']=dict(id='company-welcome',user_id=None,address=welcome+'@'+p['domain'],enabled=True,quota_bytes=100000,messages=[])
    count=len(users)
    state['corporate']=dict(version=1,environment_id=state.get('environment_id','legacy'),revision=0,policy=p,mail_running=True,mailboxes=boxes,
        licenses={key:dict(id=key,name=name,capacity=count+5,assigned=list(users)) for key,name in [('mail','Messagerie'),('office','Bureautique')]},requests={},history=[],counter=0)
    return True


def _account(state,uid,now):
    u=state['directory']['users'].get(uid)
    return bool(u and u['enabled'] and not u.get('must_change_password') and (u.get('locked_until') or 0)<=now and (u.get('password_expires_at') is None or now<u['password_expires_at']))


def public(state):
    result=copy.deepcopy(state['corporate'])
    for box in result['mailboxes'].values():box['used_bytes']=sum(len(m['body'].encode())+len(m['subject'].encode()) for m in box['messages'])
    result['users']={uid:dict(id=uid,username=u['username'],display_name=u['display_name'],enabled=u['enabled']) for uid,u in state['directory']['users'].items()}
    result['groups']={gid:dict(id=gid,name=g['name']) for gid,g in state['directory']['groups'].items()}
    return result


def _text(p,key,low=1,high=200):
    v=p.get(key)
    if not isinstance(v,str) or not low<=len(v.strip())<=high:raise ValueError('Champ invalide : '+key)
    return v.strip()


def evaluate(state,ident,now):
    c=state['corporate'];r=c['requests'].get(ident)
    if c['environment_id']!=state.get('environment_id','legacy') or state['directory']['environment_id']!=c['environment_id']:raise ValueError('Demande ou annuaire d’une autre entreprise.')
    if not r:raise ValueError('Demande inconnue.')
    uid=next((k for k,u in state['directory']['users'].items() if u['username'].lower()==r['username'].lower()),None)
    rows=[]
    def row(label,ok,detail):rows.append(dict(label=label,status='valide' if ok else 'non satisfait',detail=detail))
    u=state['directory']['users'].get(uid,{})
    row('Compte actif et utilisable',bool(uid and _account(state,uid,now) and u.get('display_name')==r['display_name']),'Identité, activation, verrouillage et stratégie de mot de passe de l’annuaire simulé.')
    row('Groupes demandés',bool(uid and all(uid in state['directory']['groups'].get(gid,{}).get('member_user_ids',[]) for gid in r['group_ids'])),'Appartenance réelle aux groupes ; ne prouve pas une ACL SMB.')
    row('Licences attribuées',bool(uid and all(uid in c['licenses'][key]['assigned'] for key in r['license_ids'])),'Attribution dans les capacités disponibles du catalogue.')
    box=c['mailboxes'].get(uid,{})
    row('Boîte mail disponible',bool(uid and c['mail_running'] and box.get('enabled') and uid in c['licenses']['mail']['assigned']),'Service mail, boîte et licence ; pas un serveur SMTP réel.')
    messages=box.get('messages',[])
    delivered=any(m['direction']=='inbox' and m['sender']==c['mailboxes']['company-welcome']['address'] and r['created_at']<=m['created_at']<=now and m['body']==r['welcome_document'] and len(r['welcome_document'])>=20 for m in messages)
    sent=any(m['direction']=='sent' and m['recipient']!=box.get('address') and r['created_at']<=m['created_at']<=now for m in messages)
    row('Accueil envoyé et échange testé',delivered and sent,'Lettre d’accueil effectivement livrée et message envoyé depuis cette boîte dans le moteur simulé.')
    items=state.get('inventory',{}).get('items',{})
    prepared=state.get('inventory',{}).get('environment_id')==c['environment_id'] and any(i.get('employee_id')==r['employee_id'] and i['status']=='assigned' and i.get('deployment') and i['deployment'].get('environment_id')==c['environment_id'] and sim_deployment.evaluate(i['deployment'])['passed'] for i in items.values())
    row('Matériel préparé et remis',bool(uid and prepared),'Déploiement validé dans l’atelier et remise administrative ; aucun poste PT ajouté.')
    return dict(passed=all(x['status']=='valide' for x in rows),checks=rows,user_id=uid)


def operate(state,operation,payload,expected_revision,now):
    """Copie entière : toute exception laisse l'état original intact."""
    if not isinstance(payload,dict):raise ValueError('Paramètres invalides.')
    work=copy.deepcopy(state);ensure(work);c=work['corporate']
    if type(expected_revision) is not int or expected_revision!=c['revision']:raise ValueError('Services modifiés. Actualise avant cette opération.')
    users=work['directory']['users'];result={'code':'OK'}
    if operation=='create-mailbox':
        uid=payload.get('user_id');u=users.get(uid)
        if not u or uid in c['mailboxes']:raise ValueError('Compte inconnu ou boîte déjà présente.')
        address=u['username'].lower()+'@'+c['policy']['domain']
        if any(b['address']==address for b in c['mailboxes'].values()):raise ValueError('Adresse mail déjà utilisée.')
        c['mailboxes'][uid]=dict(id=uid,user_id=uid,address=address,enabled=True,quota_bytes=100000,messages=[])
    elif operation in ('set-mailbox','set-mail-service'):
        if type(payload.get('enabled')) is not bool:raise ValueError('État booléen requis.')
        if operation=='set-mail-service':c['mail_running']=payload['enabled']
        else:
            box=c['mailboxes'].get(payload.get('mailbox_id'))
            if not box or box['user_id'] is None:raise ValueError('Boîte utilisateur requise.')
            box['enabled']=payload['enabled']
    elif operation in ('assign-license','remove-license','license-capacity'):
        license=c['licenses'].get(payload.get('license_id'))
        if not license:raise ValueError('Licence inconnue.')
        if operation=='license-capacity':
            cap=payload.get('capacity')
            if type(cap) is not int or not len(license['assigned'])<=cap<=1000:raise ValueError('Capacité de 0 à 1000, au moins égale aux attributions.')
            license['capacity']=cap
        else:
            uid=payload.get('user_id')
            if uid not in users:raise ValueError('Compte inconnu.')
            if operation=='remove-license':license['assigned']=[x for x in license['assigned'] if x!=uid]
            elif uid not in license['assigned']:
                if len(license['assigned'])>=license['capacity']:raise ValueError('Aucune licence disponible.')
                license['assigned'].append(uid)
    elif operation=='send':
        src=c['mailboxes'].get(payload.get('mailbox_id'));address=_text(payload,'recipient').lower()
        dst=next((b for b in c['mailboxes'].values() if b['address']==address),None)
        if not c['mail_running']:raise ValueError('Service de messagerie arrêté.')
        if not src or not dst or not src['enabled'] or not dst['enabled']:raise ValueError('Boîte expéditrice ou destinataire indisponible.')
        for b in (src,dst):
            if b['user_id'] is not None and (not _account(work,b['user_id'],now) or b['user_id'] not in c['licenses']['mail']['assigned']):raise ValueError('Compte ou licence de messagerie indisponible.')
        subject=_text(payload,'subject',1,200);body=_text(payload,'body',1,10000);size=len(subject.encode())+len(body.encode())
        for b in (src,) if src is dst else (src,dst):
            used=sum(len(m['body'].encode())+len(m['subject'].encode()) for m in b['messages'])
            if len(b['messages'])+ (2 if src is dst else 1)>200 or used+size*(2 if src is dst else 1)>b['quota_bytes']:raise ValueError('Quota de boîte atteint ; aucun message livré.')
        c['counter']+=1;mid='MSG-'+str(c['counter']).zfill(5)
        message=dict(id=mid,sender=src['address'],recipient=address,subject=subject,body=body,created_at=now)
        src['messages'].append(dict(message,direction='sent'));dst['messages'].append(dict(message,direction='inbox'));result['message_id']=mid
    elif operation=='create-request':
        name=_text(payload,'display_name',3,100);username=_text(payload,'username',3,64).lower()
        if not re.fullmatch(r'[a-z][a-z0-9._-]*',username):raise ValueError('Identifiant : lettres ASCII, chiffres, point, tiret.')
        if any(u['username'].lower()==username for u in users.values()) or any(r['username']==username for r in c['requests'].values()):raise ValueError('Arrivée déjà enregistrée ou compte existant.')
        department=_text(payload,'department',2,80);manager=_text(payload,'manager',3,100);start=_text(payload,'start_date',10,10)
        import datetime
        try:datetime.date.fromisoformat(start)
        except ValueError:raise ValueError('Date d’arrivée invalide.') from None
        groups=payload.get('group_ids',[]);licenses=payload.get('license_ids',['mail','office'])
        if not isinstance(groups,list) or any(not isinstance(g,str) for g in groups) or len(groups)!=len(set(groups)) or any(g not in work['directory']['groups'] for g in groups):raise ValueError('Groupes inconnus ou dupliqués.')
        if not isinstance(licenses,list) or not licenses or any(not isinstance(k,str) for k in licenses) or len(licenses)!=len(set(licenses)) or 'mail' not in licenses or any(k not in c['licenses'] for k in licenses):raise ValueError('Licences invalides ; messagerie requise.')
        if len(c['requests'])>=100:raise ValueError('Limite de 100 arrivées.')
        ident='DEM-ARR-'+str(len(c['requests'])+1).zfill(4);employee='arrival-'+hashlib.sha256((c['environment_id']+':'+username).encode()).hexdigest()[:20]
        c['requests'][ident]=dict(id=ident,employee_id=employee,display_name=name,username=username,department=department,manager=manager,start_date=start,group_ids=list(groups),license_ids=list(licenses),created_at=now,welcome_document='Bienvenue '+name+' chez '+work['company']+'. Votre responsable est '+manager+'.',status='open')
        result['request_id']=ident
    elif operation=='welcome-document':
        r=c['requests'].get(payload.get('request_id'))
        if not r:raise ValueError('Arrivée inconnue.')
        r['welcome_document']=_text(payload,'body',20,10000)
    else:raise ValueError('Opération inconnue.')
    c['revision']+=1;c['history'].append(dict(at=now,operation=operation,code='OK'));c['history']=c['history'][-200:]
    return work,result


def sync_people(state):
    """Arrivants administratifs distincts des postes déjà représentés."""
    registry=state.get('company_registry')
    if not registry:return
    for r in state.get('corporate',{}).get('requests',{}).values():
        uid=next((k for k,u in state['directory']['users'].items() if u['username'].lower()==r['username']),None)
        registry['people'][r['employee_id']]=dict(id=r['employee_id'],environment_id=registry['environment_id'],account_id=uid,display_name=r['display_name'],username=r['username'],department=r['department'],represented=False,administrative_arrival=True,account_present=uid is not None)
