# v0.38 — Bureaux, consoles et préparation des postes

Livraison groupée depuis v0.37, sur `codex/ui-ux-v029`. Le générateur de labs indépendants reste disponible ; les nouvelles demandes utilisent l’entreprise active et son réseau existant.

## Utilisation

1. Extraire l’archive et lancer `LANCER-WEB.bat` (Python 3.10+).
2. Reprendre ou créer l’entreprise, ouvrir son réseau avec le bouton du bandeau et connecter le pont MCP BUILDER.
3. Dans Tickets → Recevoir une nouvelle intervention, choisir le catalogue **Poste, préparation, impression et FTP**, puis **Préparer un poste · Applications**.
4. Le profil est choisi à partir de la seed et du numéro d’intervention. La consigne précise les applications, documents, imprimante et transferts nécessaires. Le délai reste réglable ; 0 signifie libre.
5. Depuis Postes, ouvrir le bureau client concerné. Se connecter à son compte avec Session utilisateur, puis installer/configurer les applications dans Paramètres. Réaliser les actions demandées avant Vérifier et Clôturer.

La famille est aussi proposée dans les arrivées automatiques. Le choix général « Aléatoire » conserve son ancien catalogue de pannes : pour recevoir ces nouvelles demandes, choisir explicitement **Préparer un poste**. Les trois profils de cette famille sont procéduraux.

## Bureaux et applications

- **Applications** ouvre un lanceur filtrable. Il respecte le rôle du bureau et les applications installées sur le client. Échap ou Fermer le referme.
- Les fenêtres nouvelles restent en cascade ; le décalage revient au début après cinq ouvertures pour limiter les sorties d’écran. Le clic sur une tâche relève la fenêtre sans annuler son agrandissement.
- **Partages** : vue d’ensemble, permissions, partages/fichiers, quotas/volume. Les deux couches de droits restent distinctes ; les fichiers affichés appartiennent au partage sélectionné.
- **DNS** : résultat de résolution lisible, adresses et TTL, diagnostic détaillé replié. Le bureau technicien dispose en plus des enregistrements, de la configuration client et du service. Une réponse DNS ne valide pas un accès fichier. Le vidage du cache du client depuis le technicien requiert une session distante active.
- **Serveur FTP** : service et canaux, comptes et droits, fichiers et capacité. Cette console administre le dépôt ; les transferts se font avec Client FTP sur le poste utilisateur.
- Les consoles effacent les contrôles anciens si leur actualisation échoue. Une mutation refusée réaffiche les valeurs reçues du serveur. Les opérations simultanées sont sérialisées dans chaque console.

## Liste des postes

La recherche filtre par nom, utilisateur ou IP. Les lignes distinguent le poste du ticket, les postes détectés et leur disponibilité au dernier contrôle. Le portable du technicien reste séparé de cette liste. Filtrer ne change pas silencieusement la cible de connexion ; la recherche est remise à zéro lors du changement d’entreprise. Les appareils de l’inventaire sans bureau simulé sont indiqués comme tels et leur connexion reste désactivée.

## Trois profils de demandes

| Profil | Actions attendues |
|---|---|
| Documentaire | Installer Documents, corriger le lecteur partagé, ouvrir le document ciblé |
| Bureautique | Actions documentaires + installer Imprimantes, choisir la file physique par défaut et imprimer la fiche désignée |
| Échanges de fichiers | Actions bureautiques + installer Client FTP, se connecter, télécharger le guide et envoyer le rapport désigné |

Le générateur prépare les dépendances des services nécessaires. Pour les documents, il accorde la lecture au seul demandeur, sans élargir les groupes des collègues. Les services d’impression/FTP nécessaires sont rendus utilisables avant la capture de l’état de référence. Ensuite les applications demandées sont retirées du client, le lecteur pointe vers un ancien partage, et la file par défaut est PDF si une impression physique est demandée.

Les noms des fichiers varient avec la seed et le numéro de demande. Le nombre de fichiers et la capacité du dépôt sont contrôlés avant de générer, avec refus sans modification si la demande ne tient pas dans le stockage. Aucun fichier de préparation inutile n’est ajouté au profil documentaire.

## Vérification et sauvegarde

- Les simples cases « application installée » ne terminent pas la demande.
- La lecture doit réussir via l’API du document ciblé. Les transferts doivent réussir via les routes du Client FTP. Copier un contenu dans l’état ne remplace pas cette preuve.
- Les preuves sont liées à l’environnement, au poste client, à la cible et au début de la demande. Le contrôle exige aussi que l’accès actuel reste possible.
- L’impression doit être traitée sur la bonne file et porter le contenu demandé ; imprimer en PDF ne suffit pas.
- L’état de référence protège les appareils, les fichiers préexistants, les comptes FTP, les autres utilisateurs et leurs droits effectifs, ainsi que les autres applications.
- Demande, références et preuves sont persistées avec l’entreprise. Reprendre une sauvegarde invalide les sessions distantes/FTP : il faut se reconnecter ; la progression reste conservée.
- La clôture utilise les vérifications du ticket actif. Le pont et les gardes d’environnement restent nécessaires ; le générateur ne fabrique aucune preuve réseau.

## Périmètre et limites

Ces demandes préparent **le poste client simulé existant** ; elles ne créent ni un nouveau PC Packet Tracer, ni un bureau pour chaque machine de l’inventaire. Le disque de l’atelier Windows reste distinct. Le modèle réseau repose sur les observations du pont ; ICMP est une approximation et ne prouve pas un service SMB/FTP réel. Aucun Windows, serveur de fichiers ou transfert disque réel n’est exécuté.

Pas de nouveau LLM ni de réduction annoncée de la latence du pont dans ce bloc. L’installation visuelle Windows, les scénarios existants, les labs PKT/PKA et les sauvegardes conservent leur fonctionnement.

## Vérifications de livraison

- `python -m unittest discover -s web -p 'test_*.py'` : 510/510, incluant 12 tests nouveaux de préparation (trois profils, actions réussies/refusées, preuves hors contexte, collatéraux, sauvegarde, clôture et notification des tickets).
- `node web/test_desktop_ui.js` : applications existantes.
- `node web/test_desktop_consoles.js` : ciblage ACL, annulation visuelle d’une mutation refusée, filtrage par partage, quota, compte/capacité FTP, DNS, rôle et recherche du lanceur.
- `node web/test_workspace_ui.js` : cible de connexion, recherche sans changement de cible, séparation du portable, changement d’environnement et fermeture du bureau après perte réseau.
- Deux tests AD supplémentaires : création/déplacement/appartenance conservés à la sauvegarde, et refus de création hors réseau.
- Syntaxe JavaScript des trois pages.
- `python tests/test_all.py` : 19/19.
- `python tests/test_workshops.py` : 8/8.

Les tests DOM utilisent un environnement simulé sans navigateur. Le rendu visuel, les interactions OS.js réelles et le parcours avec Packet Tracer restent à essayer côté utilisateur. Aucune validation visuelle réelle de cette nouvelle version n’est annoncée.
