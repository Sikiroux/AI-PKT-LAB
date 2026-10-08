# v0.39 — Deux bureaux clients dans une entreprise

Les nouveaux environnements associent deux postes clients et le portable technicien aux numéros de série de leurs appareils Packet Tracer. Ils partagent un réseau et une sauvegarde d’entreprise. Aucun réseau de test séparé n’est nécessaire.

## Utilisation

1. Lance `LANCER-WEB.bat`, crée une entreprise depuis l’accueil et ouvre son réseau depuis le bandeau principal.
2. Dans **Postes**, sélectionne un utilisateur et prends la main sur son poste. La cible affiche son nom et son adresse IP.
3. Le portable technicien propose également une application **Accès distant** avec le choix du poste.
4. Dans **Tickets**, une intervention de préparation, impression ou FTP peut viser un poste choisi ou un poste choisi procéduralement. Le bouton de prise en main ouvre la cible du ticket.
5. Agrandir, réduire et ouvrir dans un onglet utilisent les commandes existantes de la session distante. Déconnecter ferme uniquement la session sélectionnée.

## État local et services partagés

| Propre à chaque client | Commun à l’entreprise |
| --- | --- |
| Utilisateur AD associé, session distante et preuves réseau | Annuaire et comptes |
| Applications installées et fichiers locaux | Partages et leurs ACL |
| Lecteur mappé, réglages DNS et cache DNS | Zones DNS |
| File d’impression, spooler et imprimante par défaut | État physique de l’imprimante |
| Connexion FTP | Comptes et fichiers du dépôt FTP |

Les droits de lecture du deuxième utilisateur sont ajoutés explicitement au partage Documents. Les changements de comptes FTP invalident les connexions existantes ; les modifications d’annuaire invalident les authentifications concernées. La reprise conserve les réglages mais referme les sessions et exige des observations réseau fraîches.

## Intégration

`client_workspaces.py` stocke les profils par numéro de série. Le premier client reste l’état canonique pour les anciens moteurs. Les requêtes du second client utilisent une projection temporaire sous le verrou du contrôleur ; la fusion sauvegarde les services communs sans remplacer le premier poste. Le navigateur transmet la série de sa cible et l’identifiant d’environnement. Les contrôles périodiques interrogent les deux appareils réels et enregistrent leurs preuves séparément.

## Périmètre et limites

- Les nouveaux environnements ont deux bureaux clients ; les anciennes sauvegardes gardent leurs appareils existants. Créer une nouvelle entreprise permet de tester les deux bureaux.
- Les tickets applicatifs prennent en charge le choix de la cible. Les autres catalogues historiques AD, fichiers, DNS et incidents mixtes conservent leur premier client ; ce n’est pas encore une généralisation de tous les scénarios à tous les postes.
- L’atelier de déploiement du disque reste distinct de cette extension des bureaux.
- Le contrôle réseau utilise les observations du pont PT et des proxys ICMP : un ping ne prouve pas qu’un service SMB ou FTP réel fonctionne.
- Deux clients ajoutent des contrôles au cycle de surveillance. Aucun gain de latence n’est annoncé.
- Les tests Python et DOM ne remplacent pas une vérification visuelle dans un navigateur ni un essai du pont sur Packet Tracer.

## Vérification

La suite `test_client_workspaces.py` vérifie les identités distinctes, les fichiers et applications isolés, la persistance, les sessions FTP et caches DNS distincts, la connexion avec les seules preuves du poste cible, le refus des identités ou environnements incorrects, les deux sources de ping, les tickets secondaires et l’invalidation des sessions. Les trois suites DOM vérifient les applications, les consoles et le parcours de sélection des postes. Les suites web, génération et workshops complètent ces contrôles.
