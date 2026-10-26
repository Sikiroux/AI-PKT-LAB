"""Connaissance du demandeur et essais locaux, sans accès réseau réel."""
import time
import client_workspaces as clients
import directory_adapter as ad
import dns_adapter
import files_adapter

LABELS={'scope':'Poste et ressource concernés','when':'Quand l’avez-vous constaté ?',
        'attempts':'Quels essais avez-vous faits ?','changes':'Quel changement avez-vous constaté ?',
        'network':'État de la connexion','ip':'Dernier contrôle par IP','name':'Adresse du service',
        'login':'Session utilisateur','save':'Lecture et enregistrement','retest':'Réessayer maintenant'}
FAMILIES={'printing':('scope','when','attempts','changes','network','ip','retest'),
          'endpoint':('scope','when','attempts','changes','network','name','login','save','retest'),
          'dns':('scope','when','attempts','changes','network','ip','name','login','retest'),
          'ad':('scope','when','attempts','changes','login','network','retest'),
          'ftp':('scope','when','attempts','changes','network','ip','retest'),
          'peripherals':('scope','when','attempts','changes','retest')}

def questions(family):return {key:LABELS[key] for key in FAMILIES[family]}

def snapshot(v,ticket):
    """Le récit initial décrit une tâche et un symptôme, pas le diagnostic privé."""
    family=ticket['live_family'];server=v['devices']['server']['name']
    if family=='printing':
        resource=v['desktop_services']['printing']['queues']['office']['name']
        operation='imprimer un document sur '+resource
    elif family in ('endpoint','dns'):
        resource='\\\\'+server+'\\Documents'
        operation='ouvrir le partage Documents à l’adresse '+resource
    elif family=='ftp':
        resource=ticket.get('request_context',{}).get('resource',server)
        goal=ticket.get('transfer_goal') or {}
        operation=('télécharger '+goal['name']+' depuis le dépôt FTP sur '+server) if goal.get('name') else 'ouvrir le dépôt FTP sur '+server
    elif family=='ad':
        resource=v['directory']['users'][v['directory_user_id']]['username']
        operation='ouvrir ma session avec le compte '+resource
    else:
        resource=ticket['title'];operation='utiliser mon accessoire externe sur ce poste'
    return dict(station=v['devices']['client']['name'],user_id=v['directory_user_id'],resource=resource,operation=operation,
                symptom=ticket['request_context']['complaint'],attempts=[])

def attempt_description(knowledge,at,outcome):
    return dict(at=at,operation=knowledge['operation'],status=outcome)

def answer(s,record,question,at,checks):
    if question not in LABELS:raise ValueError('Question inconnue.')
    if record.get('lifecycle') in ('awaiting_activity','resolved_before_report'):
        raise ValueError('Cet événement n’a pas encore de signalement client.')
    ticket=record['ticket'];v=clients.project(s,record['target_serial']);family=record['family']
    knowledge=record.get('client_report')
    if not knowledge:
        # Compatibilité : ne pas inventer un essai ou une heure dans les anciens tickets.
        knowledge=snapshot(v,ticket);knowledge['legacy']=True;record['client_report']=knowledge
    if question in ('login','save','retest') and knowledge.get('user_id')!=v['directory_user_id']:
        response='Le compte associé à ce poste a changé depuis mon signalement. Cet essai ne confirmerait pas mon accès personnel.'
    elif question not in FAMILIES[family]:
        response='Cette question ne correspond pas à ma demande : '+knowledge['symptom']
    elif question=='scope':
        response='Au signalement, sur '+knowledge['station']+', je cherche à '+knowledge['operation']+'. '+knowledge['symptom']+' Je n’ai pas testé les autres postes.'
    elif question=='when':
        stamp=record.get('reported_at')
        response=('Je l’ai constaté à '+time.strftime('%H:%M:%S',time.localtime(stamp))+', au moment de mon signalement. Je ne sais pas si le problème avait commencé plus tôt.') if stamp else 'Je n’avais pas noté l’heure à mon signalement ; je ne peux pas préciser quand le problème a commencé.'
    elif question=='changes':
        response='Je n’ai pas relevé de changement avant mon signalement. Je ne peux pas confirmer s’il y a eu une intervention technique.'
    elif question=='attempts':
        attempts=knowledge['attempts']
        if not attempts:response='Je n’avais pas détaillé mes essais au signalement. Tu peux me demander de réessayer maintenant.'
        else:
            response=' '.join('À '+time.strftime('%H:%M:%S',time.localtime(a['at']))+', j’ai essayé de '+a['operation']+' : '+{'failed':'sans succès','passed':'avec succès','unknown':'résultat non confirmé'}[a['status']]+'.' for a in attempts[-3:])
    elif question in ('network','ip'):
        proof=ad.context(v,now=at)['network']
        status=proof['status'] if proof['observed_at']<=at<=proof['valid_until'] else 'unknown'
        response={'passed':'Le dernier contrôle réseau par IP est positif. Cela ne confirme pas l’accès à la ressource.',
                  'failed':'Le dernier contrôle réseau par IP a échoué.'}.get(status,'Je ne dispose pas encore d’un contrôle réseau récent pour ce poste et ce serveur.')
        if question=='network':
            observed=v.get('network_observation') or {}
            stamp=observed.get('at',0)
            fresh=type(stamp) in (int,float) and 0<=at-stamp<=ad.TTL
            link=observed.get('client_link') if fresh else None
            if link is False:response='Le dernier relevé du poste indique une liaison réseau débranchée. Il faut vérifier le câble et le port avant de conclure sur le service.'
            elif link is True:response='Le dernier relevé indique une liaison réseau présente. '+response
            else:response='Je n’ai pas de relevé récent de la liaison du poste. '+response
    elif question=='name':
        observation,_=dns_adapter.resolution(v,at)
        response='L’adresse habituelle est '+knowledge['resource']+'. '
        response+=('Le dernier contrôle retrouve le nom vers '+str(observation['resolved_ip'])+'. Cela ne prouve pas l’accès aux fichiers.') if observation['status']=='resolved' else 'Le dernier contrôle ne retrouve pas le nom.' if observation['status']=='failed' else 'Je n’ai pas de contrôle exploitable de la résolution du nom.'
    elif question=='login':
        user=v['directory']['users'][v['directory_user_id']]
        response='La connexion est refusée ; je ne connais pas la raison technique.' if not user['enabled'] else 'Ma session utilisateur est ouverte.' if ad.context(v,now=at)['authentication'] else 'Ma session utilisateur n’est pas ouverte. Je n’ai pas encore validé une nouvelle connexion.'
    else:
        if question=='save':
            read=files_adapter.access(v,'read',at);write=files_adapter.access(v,'write',at)
            endpoint=v['desktop_services']['endpoint']
            reachable='documents' in endpoint['applications'] and endpoint['mapped_drive']['path'].casefold()==('\\\\'+v['devices']['server']['name']+'\\Documents').casefold()
            if not reachable:
                read=dict(allowed=False,status='failed');write=dict(allowed=False,status='failed')
            response=('Je peux lire le document du partage.' if read['allowed'] else 'Je ne peux pas confirmer la lecture du document du partage.')+' '+('Le contrôle autorise son enregistrement.' if write['allowed'] else 'Le contrôle ne permet pas de confirmer son enregistrement.')+' Aucun fichier n’a été modifié pendant cet essai.'
            outcome='passed' if read['allowed'] and write['allowed'] else 'unknown' if 'unknown' in (read['status'],write['status']) else 'failed'
            operation='lire et vérifier l’enregistrement dans '+knowledge['resource']
        else:
            rows=checks(s,ticket,at)
            outcome='passed' if all(r['status']=='valide' for r in rows) else 'unknown' if any(r['status']=='inconnu' for r in rows) else 'failed'
            if family=='ad' and outcome=='passed' and not ad.context(v,now=at)['authentication']:outcome='unknown'
            response={'passed':'Je peux à nouveau '+knowledge['operation']+'.',
                      'failed':'Je ne peux toujours pas '+knowledge['operation']+'.',
                      'unknown':'Je ne peux pas confirmer cet essai : la session ou les observations nécessaires ne sont pas disponibles.'}[outcome]
            if family=='ftp' and outcome=='passed':response='Le contrôle permet de joindre le service FTP. Je dois encore me connecter avec mon compte pour vérifier mes fichiers.'
            operation=knowledge['operation']
            if family=='dns':
                operation='retrouver le nom du serveur documentaire'
                name_status=rows[0]['status'] if rows else 'inconnu'
                if name_status!='valide':
                    outcome='failed' if name_status=='non satisfait' else 'unknown'
                    response='Le nom habituel ne permet toujours pas de confirmer le serveur documentaire attendu.' if name_status=='non satisfait' else 'Je n’ai pas de contrôle récent permettant de confirmer la résolution du nom.'
                elif len(rows)<2:
                    outcome='unknown'
                    response='Le contrôle retrouve le nom du serveur documentaire. Il faut encore vérifier l’accès au partage.'
                else:
                    operation='retrouver le serveur et lire un document du partage '+knowledge['resource']
                    response={'passed':'Le nom est retrouvé et le contrôle autorise la lecture d’un document du partage. Aucun fichier n’a été modifié.',
                              'failed':'Le nom est retrouvé, mais la lecture du document du partage reste indisponible sur mon poste.',
                              'unknown':'Le nom est retrouvé, mais je ne peux pas encore confirmer la lecture du document. Vérifie ma session et les contrôles Documents du poste.'}[outcome]
            elif family=='ftp':
                operation=knowledge['operation'] if len(rows)>1 else 'joindre le service FTP'
                if rows and rows[0]['status']=='non satisfait':
                    outcome='failed';response='Je ne peux toujours pas joindre le service FTP depuis mon poste.'
                elif len(rows)>1 and outcome=='passed':
                    response='Le téléchargement demandé est confirmé sur mon poste et la copie locale correspond au document actuel du dépôt.'
                elif rows and rows[0]['status']=='valide':
                    outcome='unknown';response='Le service FTP est accessible, mais le téléchargement demandé sur mon poste n’est pas encore confirmé. Je dois me connecter au client FTP et télécharger le document indiqué.'
                else:response='Je ne dispose pas de contrôles récents permettant de confirmer le service FTP et le téléchargement.'
        knowledge['attempts'].append(dict(at=at,operation=operation,status=outcome));knowledge['attempts']=knowledge['attempts'][-20:]
    row=dict(at=at,question=LABELS[question],answer=response,speaker=ticket['requester'])
    ticket.setdefault('dialogue',[]).append(row);ticket['dialogue']=ticket['dialogue'][-60:]
    return row
