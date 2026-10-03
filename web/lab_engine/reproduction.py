import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[2]))
"""Exercices inverses : démarrer sain, reproduire des symptômes délimités."""
import workshops
SCENARIOS={
 'reproduce:dns':dict(source='dns_record_delete',title='Reproduire : un seul nom devient inaccessible',
 statement='Le client rapporte : « L’intranet fonctionne quand je saisis son adresse IP, mais intranet.entreprise.test ne se résout plus. ftp.entreprise.test fonctionne toujours. » Le réseau fourni est sain. Vérifie cet état, puis reproduis exactement ces symptômes pour PC-ALICE et PC-BOB. Conserve les IP, les câbles, le service web et la résolution du nom FTP. Documente tes changements et tes tests.',
 hints=['Compare la résolution de deux noms et l’accès HTTP direct par IP.','Cherche une modification limitée à un seul nom, sans interrompre tout le service de résolution.'],
 solution='Une méthode : SRV-INFRA > Services > DNS, supprimer uniquement l’enregistrement A intranet.entreprise.test. Garder DNS actif et conserver ftp.entreprise.test. Pour revenir à l’état sain, recréer cet enregistrement vers {SRV-WEB}.',
 tests=['Avant modification : les noms intranet.entreprise.test et ftp.entreprise.test se résolvent et l’intranet s’ouvre par nom et par IP.','Après modification : nslookup intranet.entreprise.test échoue depuis les deux postes.','Ouvrir http://{SRV-WEB} reste possible ; ftp.entreprise.test se résout toujours vers {SRV-FTP}.','Ne juge pas uniquement le navigateur : son cache peut conserver une résolution antérieure. Vérifie explicitement la résolution avec nslookup.']),
 'reproduce:web':dict(source='http_service_off',title='Reproduire : serveur joignable, page indisponible',
 statement='Le client rapporte : « Je peux encore joindre le serveur et son nom se résout, mais sa page intranet ne s’ouvre plus, même avec l’adresse IP. » Le réseau fourni est sain. Vérifie-le, puis reproduis ce problème depuis PC-ALICE et PC-BOB. Préserve DNS, le ping vers SRV-WEB, le FTP et la messagerie. Conserve les IP et le câblage.',
 hints=['Distingue résolution de nom, connectivité IP et service applicatif.','Une panne peut concerner seulement le service utilisé par le navigateur.'],
 solution='Une méthode : SRV-WEB > Services > HTTP : Off pour HTTP. Ne pas changer son IP ni arrêter le serveur entier. Les tests demandés concernent http://, pas HTTPS. Remettre HTTP sur On pour restaurer.',
 tests=['Avant modification : ouvrir http://intranet.entreprise.test et http://{SRV-WEB} depuis les employés.','Après modification : ces deux accès HTTP échouent.','Le ping vers {SRV-WEB} fonctionne ; nslookup intranet.entreprise.test renvoie toujours {SRV-WEB}.','FTP et messagerie restent utilisables : comparer leurs tests avant/après.']),
 'reproduce:ftp':dict(source='ftp_write_denied',title='Reproduire : connexion acceptée, dépôt refusé',
 statement='Le client rapporte : « Mon compte depot arrive à se connecter et à lire la liste des fichiers, mais le dépôt de mon document est refusé. » Le réseau fourni est sain. Reproduis ce symptôme depuis PC-ALICE pour depot/Depot123. Préserve la connexion, la lecture et la liste des fichiers pour ce compte. Ne modifie pas lecteur/Lecture123, le service FTP, les adresses ni les autres services.',
 hints=['Un refus de transfert ne signifie pas que le serveur est injoignable.','Compare les autorisations nécessaires pour se connecter, lister et écrire.'],
 solution='Une méthode : SRV-FTP > Services > FTP : garder depot et son mot de passe Depot123, retirer Write en conservant Read et List. Le réseau de correction fourni utilise les droits Read/List. Ne pas modifier lecteur. Pour restaurer, rendre au compte depot ses droits initiaux Read, Write, Rename et List.',
 tests=['Avant modification : créer preuve.txt dans le Text Editor de PC-ALICE et réussir put preuve.txt avec depot/Depot123 sur {SRV-FTP}.','Après modification : la connexion et dir réussissent, mais put preuve2.txt (nouveau fichier local) est refusé.','Avec depot, lire un fichier existant avec get reste possible.','lecteur/Lecture123 conserve sa connexion et Read/List ; son écriture reste refusée.','HTTP et DNS fonctionnent toujours.'])
}
def install(ident):
 s=SCENARIOS[ident];base=workshops.CATALOGUE[s['source']]
 workshops.KINDS['reproduction']='Reproduire une panne'
 workshops.CATALOGUE[ident]=dict(base,title=s['title'],kind='reproduction',mutate=workshops.noop,statement=s['statement'],hints=s['hints'],solution=s['solution'],tests=s['tests'])
 return base['mutate']
