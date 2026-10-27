"""Aides et bilan factuels : aucune action sur le réseau ni attribution de points."""
from html import escape

REPAIRS={
 'queue_paused':('File d’impression suspendue','Dans Imprimantes, ouvre la file du bureau puis reprends la file.'),
 'offline_mode':('Mode hors connexion activé','Dans Imprimantes, ouvre la file de l’imprimante du bureau puis utilise Revenir en ligne.'),
 'spooler_stopped':('Spooler arrêté','Dans Imprimantes, ouvre les propriétés de l’imprimante puis Maintenance → Redémarrer le spouleur.'),
 'mapped_drive_wrong':('Chemin du lecteur réseau incorrect','Dans Paramètres du poste → Lecteur réseau, remets le chemin Documents de la documentation d’entreprise.'),
 'documents_missing':('Application Documents absente','Dans Paramètres du poste → Applications, installe Documents.'),
 'account_disabled':('Compte du demandeur désactivé','Depuis le technicien, ouvre Annuaire, sélectionne le compte associé au poste et réactive ce compte. Reconnecte ensuite cet utilisateur.'),
 'service_stopped':('Service FTP arrêté','Depuis le technicien, ouvre Serveur FTP → Service et accès et démarre le service. Depuis le poste du demandeur, connecte ensuite le client FTP avec un compte autorisé et télécharge le document indiqué dans le ticket.'),
 'resolver_wrong':('Serveur DNS client incorrect','Dans DNS, sélectionne le client du poste concerné et configure l’adresse du serveur DNS indiqué dans la documentation. Renouvelle la résolution du nom.'),
}

HISTORICAL={
 'ad:account_disabled':'Réactive uniquement le compte du demandeur dans Annuaire.',
 'ad:account_locked':'Déverrouille le compte du demandeur puis teste une nouvelle connexion.',
 'ad:password_expired':'Réinitialise le mot de passe depuis Annuaire, puis réalise le changement exigé à la connexion.',
 'ad:read_group_missing':'Rétablis l’appartenance au groupe autorisé à lire Documents, selon la documentation de l’entreprise.',
 'ad:write_group_missing':'Rétablis l’appartenance au groupe autorisé à écrire dans Documents, sans modifier les autres comptes.',
 'files:service_stopped':'Démarre le service de fichiers depuis Partages.',
 'files:share_disabled':'Réactive le partage Documents.',
 'files:firewall_blocked':'Rétablis l’autorisation du transport SMB simulé dans Partages.',
 'files:share_read_missing':'Dans Partages, rétablis le droit de lecture du demandeur ou de son groupe sur le partage.',
 'files:folder_write_missing':'Dans Partages, rétablis le droit d’écriture du demandeur ou de son groupe dans les droits du dossier.',
 'files:quota_full':'Dans Partages, augmente le quota Documents pour permettre la sauvegarde, selon les besoins de l’exercice.',
 'files:disk_full':'Dans Partages, augmente la capacité simulée du volume ; ne supprime pas les autres fichiers pour contourner le contrôle.',
 'files:file_read_only':'Dans les propriétés du document concerné, retire la lecture seule puis reteste sa sauvegarde.',
 'dns:wrong_resolver':'Configure le client avec le serveur DNS attendu dans la documentation.',
 'dns:missing_record':'Recrée l’enregistrement du serveur documentaire dans la zone DNS avec son adresse attendue.',
 'dns:wrong_address':'Corrige l’adresse de l’enregistrement du serveur documentaire selon la documentation.',
 'dns:service_stopped':'Démarre le service DNS dans la console DNS.',
 'dns:transport_blocked':'Rétablis le transport DNS simulé dans la console DNS.',
 'dns:negative_cache':'Vide le cache DNS du client après avoir vérifié la présence de l’enregistrement attendu.',
 'dns:stale_cache':'Vide le cache DNS du client puis renouvelle la résolution vers l’adresse attendue.',
 'network:cable_disconnected':'Dans Packet Tracer, rebranche le poste concerné à son port d’accès prévu, puis vérifie le réseau.',
}

def historical(ticket,state):
 if not state:return None
 for key,layer in [('mixed_incident',None),('directory_incident','ad'),('file_incident','files'),('dns_incident','dns'),('desktop_incident','desktop')]:
  record=state.get(key)
  if not record or record.get('id')!=ticket['id']:continue
  serial=record.get('target_serial') or state.get('devices',{}).get('client',{}).get('serial')
  if not serial or serial!=ticket.get('target_serial'):return None
  if key=='mixed_incident' and record.get('injection_state')!='applied':return None
  causes=record.get('causes',[]) if layer is None else [(layer,record.get('family'))]
  if layer=='desktop':
   cause=record.get('cause')
   if cause not in REPAIRS:return None
   title,instruction=REPAIRS[cause];steps=[instruction]
  else:
   if not causes or any(l+':'+str(c) not in HISTORICAL for l,c in causes):return None
   title='Correction du scénario actif';steps=[l.upper()+' · '+HISTORICAL[l+':'+c] for l,c in causes]
  return dict(available=True,title=title,steps=steps+['Reteste le document et l’action demandés avec le compte associé au poste.','Contrôle les fonctions saines et consigne les résultats avant la résolution.'],target_serial=serial,limit='Correction de la configuration injectée dans ce scénario actif ; aucune action automatique n’est exécutée.')
 return None

def correction(ticket,state):
 record=(state or {}).get('live_incidents',{}).get(ticket['id'])
 if not record:
  result=historical(ticket,state)
  if result:return result
 if not record or not record.get('target_serial') or record.get('target_serial')!=ticket.get('target_serial') or record.get('lifecycle')=='awaiting_activity':
  return dict(available=False,reason='Correction détaillée non disponible pour ce scénario historique. Consulte les indices et, pour un lab, sa feuille de correction.')
 cause=record.get('cause');family=record.get('family')
 if family=='peripherals':
  kind,_,fault=str(cause).partition(':');names={'monitor':'écran','keyboard':'clavier','mouse':'souris'}
  actions={'working':'Remplace cet accessoire défectueux par un exemplaire fonctionnel du stock simulé.','absent':'Installe un accessoire disponible compatible depuis le stock.','connection':'Rebranche le câble de cet accessoire.','power':'Allume cet accessoire.','input':'Sélectionne HDMI comme entrée vidéo de l’écran.'}
  if kind not in names or fault not in actions:return dict(available=False,reason='Ce scénario ne dispose pas encore de correction documentée.')
  title='Accessoire local : '+names[kind];instruction='Ouvre Équipement local du poste ciblé. '+actions[fault]
 elif cause in REPAIRS:title,instruction=REPAIRS[cause]
 else:return dict(available=False,reason='Ce scénario ne dispose pas encore de correction documentée.')
 if cause=='mapped_drive_wrong':instruction+=' Chemin attendu : '+(ticket.get('request_context',{}).get('resource') or '\\\\'+state['devices']['server']['name']+'\\Documents')+'.'
 return dict(available=True,title=title,steps=[instruction,'Reteste l’action initiale sur '+ticket.get('name','le poste concerné')+' avec le compte du demandeur.','Vérifie les fonctions auparavant saines, consigne les résultats, puis utilise la vérification du ticket.'],target_serial=record['target_serial'],limit='Cette correction décrit la panne injectée à la création. D’autres changements peuvent nécessiter un diagnostic complémentaire. Elle n’effectue aucune réparation.')

def assessment(ticket):
 learning=ticket.get('learning',{})
 family=ticket.get('live_family') or ticket.get('workspace_goal') or ticket.get('kind')
 skill={'ad':'Administration des comptes','dns':'Résolution de noms','files':'Accès aux partages','endpoint':'Configuration du poste','printing':'Dépannage de l’impression','ftp':'Transfert de fichiers','peripherals':'Diagnostic des accessoires','onboarding':'Préparation d’une arrivée','deployment':'Déploiement d’atelier'}.get(family,'Diagnostic et suivi d’intervention')
 return dict(competency_practised=skill,checked_at=ticket.get('checked'),created=ticket.get('created'),ticket_id=ticket['id'],category=ticket.get('live_family') or ticket.get('workspace_goal') or ticket.get('kind'),status=ticket.get('status'),
  hints=sorted(learning.get('hints',[])),correction_viewed=bool(learning.get('correction_viewed_at')),
  checks=[dict(label=c.get('label','Contrôle'),status=c.get('status','inconnu')) for c in ticket.get('checks',[])],
  notes=ticket.get('notes',''),resolution=(ticket.get('resolution') or {}).get('text',''),
  conclusion='Clôture déclarée avec tests manuels' if ticket.get('status')=='clos' and ticket.get('manual_tests') else 'Clôture enregistrée après contrôles disponibles' if ticket.get('status')=='clos' else 'Intervention non clôturée')

def export_html(tickets,company):
 rows=[]
 for t in tickets:
  a=assessment(t);e=lambda x:escape(str(x))
  checks=''.join('<li>'+e(c['label'])+' : '+e(c['status'])+'</li>' for c in a['checks']) or '<li>Aucun contrôle enregistré</li>'
  rows.append('<article><h2>'+e(t['id'])+' · '+e(t.get('title','Intervention'))+'</h2><p>'+e(a['conclusion'])+'</p><p>Poste : '+e(t.get('name','Non renseigné'))+' · Famille : '+e(a['category'])+'</p><p>Domaine travaillé : '+e(a['competency_practised'])+' · Dernier contrôle : '+e(a['checked_at'] or 'non enregistré')+'</p><p>Indices consultés : '+e(', '.join(map(str,a['hints'])) or 'aucun')+' · Correction consultée : '+('oui' if a['correction_viewed'] else 'non')+'</p><h3>Contrôles enregistrés</h3><ul>'+checks+'</ul><h3>Compte rendu</h3><p class="notes">'+e(a['notes'] or 'Non renseigné')+'</p><h3>Solution du technicien</h3><p class="notes">'+e(a['resolution'] or 'Non renseignée')+'</p></article>')
 return '<!doctype html><html lang="fr"><meta charset="utf-8"><title>Bilan des interventions</title><style>body{font:15px system-ui;max-width:900px;margin:40px auto;padding:20px;color:#203e4d}article{border:1px solid #d6e3e8;border-radius:8px;padding:22px;margin:20px 0;break-inside:avoid}h2{font-size:20px}.notes{white-space:pre-wrap}@media print{body{margin:0}}</style><h1>Bilan · '+escape(str(company))+'</h1><p>Historique pédagogique de la session. Ce document ne certifie ni une compétence ni un fonctionnement réel dans Packet Tracer. La consultation d’une correction ne valide pas un ticket.</p>'+(''.join(rows) or '<p>Aucune intervention enregistrée.</p>')+'</html>'
