"""Échanges déterministes à choix, réponses issues de l'état courant, sans LLM."""
import hashlib
import time
import directory_adapter as ad
import dns_adapter as da
import mixed_incidents as mi

QUESTIONS={'scope':'Qui est concerné et quel document ?','when':'Depuis quand et après quel changement ?','network':'Que montre votre connexion réseau ?','ip':'Le serveur répond-il à un ping par IP ?','name':'Le nom du serveur est-il retrouvé ?','login':'Que voyez-vous lors de la connexion utilisateur ?','save':'Pouvez-vous lire et enregistrer ?','retest':'Pouvez-vous réessayer maintenant ?'}

def ask(s,ident,question,now=None):
    now=time.time() if now is None else now;i=s.get('mixed_incident')
    if not i or i['id']!=ident:raise ValueError('Ce dialogue ne concerne pas l’incident actif.')
    if question not in QUESTIONS:raise ValueError('Question inconnue.')
    uid=s['directory_user_id'];u=s['directory']['users'][uid]
    p=ad.context(s,now=now)['network'];fresh=p['observed_at']<=now<=p['valid_until']
    net=p['status'] if fresh else 'unknown'
    if question=='scope':answer=f"C’est mon poste {s['devices']['client']['name']}. Je travaille sur {s['file_service']['files'].get(i['target_file_id'],{}).get('name','le document signalé')} dans Documents."
    elif question=='when':
        n=int(hashlib.sha256((s['seed']+i['id']).encode()).hexdigest()[:4],16)
        answer=['Je l’ai remarqué en reprenant mon travail ce matin. Je ne sais pas ce qui a changé.','Ça fonctionnait lors de ma précédente utilisation. Je n’ai pas noté d’autre changement.'][n%2]
    elif question=='network':
        n=s.get('network_observation') or {};fresh=0<=now-n.get('at',0)<=ad.TTL
        link=n.get('client_link') if fresh else None
        answer='Le câble réseau apparaît débranché.' if link is False else 'Le poste indique une liaison réseau. Cela ne me dit pas si le serveur fonctionne.' if link is True else 'Je n’ai pas de constat récent de l’état du câble. Peux-tu vérifier le réseau ?'
    elif question=='ip':answer='Le dernier test par IP a réussi.' if net=='passed' else 'Le dernier test par IP a échoué.' if net=='failed' else 'Je n’ai pas de test récent exploitable. Fais un ping depuis le poste ou vérifie le réseau.'
    elif question=='name':
        proof,r=da.resolution(s,now);answer='Le nom est retrouvé vers '+str(proof['resolved_ip'])+'.' if proof['status']=='resolved' else 'Le nom n’est pas retrouvé.' if proof['status']=='failed' else 'Je ne peux pas confirmer la résolution avec les informations actuelles.'
    elif question=='login':
        answer='Le compte est indiqué désactivé.' if not u['enabled'] else 'Un message indique que le compte est temporairement verrouillé.' if u['locked_until'] and u['locked_until']>now else 'Un changement de mot de passe est demandé.' if u['must_change_password'] or u['password_expires_at'] is not None and u['password_expires_at']<=now else 'Je ne suis pas connecté dans la session utilisateur.' if not ad.context(s,now=now)['authentication'] else 'La session utilisateur est ouverte.'
    elif question in ('save','retest'):
        read=mi.access(s,'read',now);write=mi.access(s,'write',now)
        if net=='unknown':answer='Je n’ai pas de test réseau récent permettant de confirmer l’accès.'
        elif not ad.context(s,now=now)['authentication']:answer='Il faut d’abord ouvrir et authentifier ma session utilisateur pour tester le document.'
        else:answer=('Je peux ouvrir le document.' if read['allowed'] else 'Je ne peux toujours pas ouvrir le document.')+' '+('Je peux enregistrer du texte supplémentaire.' if write['allowed'] else 'Je ne peux pas enregistrer du texte supplémentaire.')
    row=dict(at=now,question=QUESTIONS[question],answer=answer,speaker=s['requester'])
    i['dialogue'].append(row);i['dialogue']=i['dialogue'][-60:];return row
