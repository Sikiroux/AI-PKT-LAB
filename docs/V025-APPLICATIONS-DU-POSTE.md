# v0.25 — Poste client, impression et FTP

Le générateur de labs reste dans son onglet. Ces nouvelles applications travaillent sur **l’entreprise active**, son unique fichier Packet Tracer et son état web. Le correctif v0.24 de création/sélection des environnements est conservé. Lanceur web à la racine : **LANCER-WEB.bat** ; `lancer.bat` reste le menu classique.

## Parcours

1. Reprendre une entreprise ou en créer une avec une seed. Ouvrir son réseau dans Packet Tracer et connecter MCP Builder.
2. Réparer et clôturer le premier ticket (câble client et lecture de Documents).
3. Dans **Postes et environnement**, choisir la famille Applications et le délai, puis **Recevoir un ticket d’application**. L’intervention prépare des dépendances saines, ferme la session cliente et injecte une cause privée. Terminer l’incident avant le suivant.
4. Ouvrir le portable du technicien, vérifier le réseau et se reconnecter au client. Utiliser les icônes du bureau. Si la panne touche Documents, authentifier aussi l’utilisateur.
5. Vérifier puis clôturer depuis Tickets. Une connexion FTP ou un travail simplement accepté ne vaut pas résolution.
6. Pour les arrivées, choisir **Site persistant**, catalogue **Applications**, famille et intervalle. Appliquer les réglages avant de démarrer. Le même délai par ticket est utilisé. Les arrivées sont différées pendant une intervention non résolue.

Les causes sont reproductibles à seed, index d’intervention et famille identiques (`apps:v1`). L’entreprise, les noms et adresses viennent de la seed de l’environnement ; ils ne sont pas redessinés à chaque ticket sur ce même site. Les heures et les observations PT évoluent avec la session.

## Les applications

| Icône | Actions |
|---|---|
| Fichiers locaux | Créer, ouvrir et modifier des textes du poste ; accueillir les téléchargements FTP |
| Documents partagés | Ancien explorateur, avec contrôle supplémentaire de l’application installée et du lecteur Z: |
| Paramètres | Lire les interfaces observées dans PT, installer/retirer les applications facultatives, reconnecter le lecteur Z: |
| Imprimantes | Choisir une file et une imprimante par défaut, soumettre un document, suivre/annuler les travaux, reprendre une file, traiter spouleur, pilote, port et papier |
| Client FTP | Se connecter, lister, télécharger vers le poste, envoyer un fichier local, se déconnecter |
| Serveur FTP — technicien | Régler service, contrôle/données, compte actif, droits lecture/écriture, mot de passe de formation et capacité |

Terminal, DNS, session utilisateur, annuaire, partages, notes et mobilité/VPN sont conservés. Les applications client facultatives absentes perdent leur icône. Paramètres, Terminal et Session utilisateur sont protégés pour garder une voie de réparation. Les fenêtres peuvent être agrandies, réduites et rouvertes avec leur bouton de barre des tâches. Le plein écran du bureau reste disponible.

Les paramètres IP et le câblage se modifient dans **Packet Tracer**, puis se relisent avec **Vérifier maintenant**. Cette version n’ajoute pas de terminal IOS web.

## 18 causes supplémentaires

| Famille | Causes | Résultat demandé |
|---|---|---|
| Impression — 7 | Spouleur arrêté, file suspendue, mode hors connexion, PDF par défaut, pilote inutilisable, port IP erroné, papier absent | Le bordereau exact doit avoir un nouveau travail imprimé sur la file physique ; cette file devient celle par défaut |
| FTP — 8 | Service arrêté, contrôle bloqué, données bloquées, compte désactivé, mot de passe incorrect, lecture refusée, écriture refusée, dépôt plein | Télécharger la notice exacte ou envoyer le rapport exact, selon le ticket |
| Poste — 3 | Client FTP absent, lecteur Z: incorrect, application Documents absente | Installer et tester le client FTP, ou rétablir l’accès au document partagé |

Ces 18 causes sont des interventions à une cause. Elles complètent le catalogue mixte v0.24 (21 causes, 583 ensembles), sans intégrer automatiquement FTP/impression aux mélanges de deux ou trois couches.

Le compte FTP de formation est **depot / Formation!2026**, indépendant de l’authentification AD. Modifier le compte ou le transport invalide les sessions FTP : reconnecter le client. Un dépôt plein refuse le transfert sans supprimer ni remplacer un fichier existant. La version du dépôt empêche un envoi fondé sur une révision ancienne.

## Imprimante et anciennes sauvegardes

Les nouveaux environnements contiennent un **Printer-PT `<SITE>-PRN-USR-01`**, à l’adresse .40 du réseau employés, raccordé au Fa0/9 du switch employés. Son numéro de série est distinct et reproducible. Le générateur de labs n’ajoute pas cette imprimante par défaut : l’option est réservée au réseau de l’entreprise simulée.

Une ancienne sauvegarde web acquiert les applications sans écraser ses données de services existantes. Si son réseau ne contient pas d’imprimante associée, le test d’impression utilise explicitement le serveur existant comme **proxy ICMP** ; il ne prétend pas constater une imprimante physique. Créer une nouvelle entreprise pour tester le Printer-PT. Conserver et sauvegarder l’ancien .pkt avant de changer d’entreprise. Le ZIP n’importe pas les sauvegardes automatiquement.

## Ce qui est réel et ce qui est simulé

- Réel dans PT : réseau ouvert, identité des appareils, câblage, IP des interfaces, pings du portable/client et ping vers le Printer-PT. Une preuve doit correspondre à sa source et sa cible et dater de moins de 45 secondes.
- Simulé dans le serveur web : applications installées, fichiers locaux, file d’impression, pilote, papier, comptes FTP, permissions et transfert de texte. Aucun document n’est imprimé sur ton imprimante Windows. Aucun serveur FTP réel n’est lancé.
- Les connexions de contrôle et de données FTP sont des préconditions distinctes, inspirées du protocole. Aucun PORT/PASV, TLS, SFTP, paquet FTP ni port TCP n’est réellement testé dans cette version.
- Le changement du port IP d’une file ne modifie pas l’IP de l’imprimante PT : c’est la destination configurée sur le poste.
- L’impression termine un travail immédiatement une fois ses préconditions réunies ; pas de durée matérielle, rendu de pages ni simulation de bourrage. Un travail accepté reste bloqué si réseau/file/papier ne conviennent pas.
- Fichiers texte seulement : 64 Kio par édition/envoi, 100 fichiers locaux, 40 travaux simultanément en attente ; historique de 100 travaux dont 40 exposés. Les travaux imprimés ne consomment du papier qu’une fois. Les sessions FTP durent 30 minutes et sont vidées à la reprise d’une sauvegarde.

## Validation et état conservé

La validation exige le résultat exact du ticket et une connectivité récente. PDF ne suffit pas pour le bordereau physique. Installation seule ne suffit pas pour la demande FTP : une connexion utilisable est également requise. Les autres textes locaux, fichiers du dépôt, documents partagés, comptes et droits des autres utilisateurs sont comparés au début de l’intervention. Supprimer les autres documents pour gagner de la place échoue à cette comparaison.

La perte du réseau distant ferme les fenêtres clientes comme avant. Une panne propre à l’imprimante n’a pas à fermer la prise en main si la liaison technicien-client fonctionne. Les comptes FTP et les preuves PT ne sont pas réutilisés après redémarrage. Les routes continuent de refuser les mutations issues d’un onglet d’un autre environnement.

## Architecture

- `web/desktop_services.py` : état des applications, files et comptes ; chaînes imbriquées, actions bornées, projection publique.
- `web/desktop_incidents.py` : génération seed/index, objectifs, validation et échanges client.
- `web/desktop_controller.py` : identité cliente imposée, session distante, accès d’administration depuis le portable, persistance.
- `web/workspace_app.py`, `workspace_model.py`, `workspace_routes.py` : migration, observation et routes `desktop/<application>/<action>`.
- `web/desktop.html`, `workspace.html`, `tickets.html`, `service_desk.py` : icônes, consoles, choix et arrivées.
- `workshops.py`, `web/workspace_network.py` : option Printer-PT sur les nouveaux environnements.

## Références de comportement

Sources officielles consultées pour définir ce sous-ensemble pédagogique, sans recopier une interface Windows complète :

- Microsoft Learn : [service Spouleur arrêté](https://learn.microsoft.com/en-us/troubleshoot/windows-server/printing/print-spooler-service-not-running).
- Microsoft Learn : [scénarios de dépannage impression](https://learn.microsoft.com/en-us/troubleshoot/windows-server/printing/troubleshoot-printing-scenarios).
- Microsoft Support : [mode hors connexion et file suspendue](https://support.microsoft.com/en-us/windows/hardware/printer/troubleshooting-offline-printer-problems-in-windows).
- RFC Editor : [RFC 959, contrôle et données FTP](https://www.rfc-editor.org/rfc/rfc959.html).

## Vérifications et limites de livraison

Tests Python : toutes les 18 causes échouent puis réussissent après réparation ; preuve réseau périmée/mauvaise source refusée ; PDF/connexion seule insuffisants ; annulation, reprise et papier ; révision et capacité atomiques ; session FTP expirée/autre environnement ; protection des fichiers/comptes ; migration, routes, observation et catalogue automatique. Vérification structurelle XML du Printer-PT, noms/séries/IP et ports de liaison uniques. Les 19 tests du moteur et les 8 des ateliers doivent aussi passer avant livraison.

La syntaxe des trois interfaces JavaScript est contrôlée. La vérification visuelle automatisée n’a pas pu démarrer ici : le navigateur Chromium n’est pas installé dans cet environnement. L’affichage réel OS.js, la mise en veille/restauration des fenêtres, le nouveau Printer-PT et son ping restent **à tester dans Packet Tracer 9 sur Windows** ; les tests Python ne prouvent pas ce comportement.
