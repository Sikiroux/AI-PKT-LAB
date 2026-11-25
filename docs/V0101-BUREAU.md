# v0.101 — Prototype bureau Windows

## Utilisation

1. Extraire toute l’archive dans un dossier accessible en écriture. Conserver l’ancienne version et ses données.
2. Disposer de Python 3.10 ou plus récent et de Node.js LTS avec npm. Ce prototype ne les embarque pas.
3. Fermer la version navigateur du simulateur pour libérer le port 8765. Packet Tracer reste ouvert selon le fonctionnement habituel.
4. Double-cliquer sur `LANCER-BUREAU.bat`. La première fois, npm télécharge Electron ; une connexion Internet est nécessaire. La version résolue est enregistrée exactement dans le package et son verrou local. Les lancements suivants réutilisent cette installation.
5. Le centre de tickets s’ouvre dans une fenêtre de bureau maximisée au premier lancement. Ouvrir le bureau technicien puis un poste depuis un ticket pour éprouver les fenêtres indépendantes. Utiliser les contrôles Windows normaux, sans F11.

Si Python ne répond pas au lanceur `py -3`, définir `NETOPS_PYTHON` avec le chemin de son exécutable. `LANCER-WEB.bat` reste disponible pour le mode navigateur. Ne pas lancer les deux modes simultanément.

## Comportements implémentés

- Démarrage du serveur Python sans ouverture du navigateur habituel.
- Fenêtres Electron sans barre d’adresse, avec bordures et contrôles Windows.
- Ouvertures existantes conservées, y compris le poste d’abord ouvert dans une fenêtre vide puis dirigé vers sa session.
- Fenêtres secondaires non modales et indépendantes de leur ouvreur ; chaque bureau peut être maximisé et déplacé.
- Position, dimensions et maximisation enregistrées dans le profil de l’application ; récupération d’une position inaccessible après débranchement d’un écran. Les fenêtres de même fonction partagent leur préférence.
- Un second lancement Electron remet l’instance existante au premier plan.
- Fermer le centre de tickets demande confirmation puis utilise `/quit`, la procédure d’arrêt existante. Une génération active peut refuser l’arrêt. Aucune destruction forcée du moteur dans ce parcours.
- Fermer une fenêtre secondaire ne demande pas l’arrêt du moteur. La sortie confirmée du logiciel ferme l’ensemble.
- Les pages ne reçoivent pas d’accès Node.js ; navigation limitée au serveur local du simulateur.

## Données et mises à jour

Les entreprises et sauvegardes utilisent encore les emplacements du programme actuel. Ce prototype n’effectue aucune migration et n’offre pas encore de mise à jour automatique. Ne pas remplacer ni supprimer un dossier contenant ses données pour mettre à jour le logiciel.

Les notes locales du navigateur ne sont pas transférées automatiquement au profil Electron. Les préférences de fenêtres internes utilisent encore le stockage de session : la mémorisation native ne restaure pas toutes les applications et tous les brouillons après fermeture. Enregistrer les brouillons avant de quitter.

## Validation

Cinq tests Node réussis avec adaptateurs simulés : navigation autorisée, géométrie, absence de fragments dans les clés, annulation/refus/acceptation de la fermeture et sortie normale du moteur. Deux tests Python de sauvegarde/arrêt réussis ; syntaxe Python et JavaScript vérifiée.

Electron n’est pas installé dans l’environnement de développement de cette livraison. Aucun essai visuel Windows ni essai Packet Tracer réel n’a été effectué. Ce sont des sources de prototype exécutables après installation des prérequis, pas un EXE autonome validé.

Recette Windows : ouvrir deux bureaux ; maximiser chacun ; déplacer entre écrans ; fermer un poste ; relancer ; tester annulation de sortie et refus pendant génération ; arrêter normalement et vérifier qu’un nouveau lancement peut reprendre le port. Tester également les fenêtres de connexion, les exports et les boîtes de confirmation.

## Suite

Valider les fenêtres sur Windows, corriger les écarts, puis préparer un paquet avec Python embarqué, les données séparées et un installateur. Définir ensuite la distribution et la mise à jour. Référence Electron : https://www.electronjs.org/docs/latest/api/window-open .

## Correctif v0.101.1 — lanceur Windows

Le lanceur appelle directement `desktop/node_modules/electron/dist/electron.exe` avec le chemin absolu du dossier de l’application, entre guillemets. Il contourne le raccourci npm qui peut chercher `electron/cli.js` au mauvais emplacement. Si le moteur manque après installation, il tente `npm rebuild electron`, puis signale explicitement son absence. Le mode `ELECTRON_RUN_AS_NODE` est neutralisé dans ce lanceur uniquement.

Pour appliquer le correctif seul : remplacer `LANCER-BUREAU.bat` à la racine du dossier déjà extrait. Conserver le dossier desktop, ses dépendances et les données existantes. Le lancement Windows corrigé reste à confirmer sur la machine concernée.

## Correctif v0.101.2 — téléchargement explicite

Installation npm avec dossier cible explicite, dépendances de développement incluses et scripts activés. Si l’exécutable reste absent, appel direct de `electron/install.js`, avec neutralisation locale de `ELECTRON_SKIP_BINARY_DOWNLOAD`. Le script affiche la véritable erreur de téléchargement si elle survient. Ceci couvre notamment les installations qui omettent les dépendances de développement ou sautent les scripts ; la capture seule ne permet pas d’établir laquelle de ces causes était présente.

## Correctif v0.101.3 — fermeture du terminal de lancement

Après préparation, lancement détaché via `start ""` et chemins entre guillemets. Le fichier batch se termine sans attendre Electron ; la fenêtre de commande créée pour un double-clic peut alors se fermer. Le serveur Python reste géré par Electron. Une console utilisée manuellement pour exécuter le batch reste naturellement ouverte. La préparation et ses erreurs restent visibles tant que l’application ne peut pas être lancée.

Retour utilisateur : lancement et affichage de deux fenêtres maximisées sur ses écrans confirmés par captures ; persistance des dimensions, arrêt et autres interactions non encore validés par ce retour.

## Correctif v0.101.4 — réutilisation des bureaux

Registre en mémoire des fenêtres, identifié par entreprise et type de poste (et numéro de poste pour les clients). Un lien direct vers un bureau déjà ouvert le restaure et le ramène au premier plan. Pour le technicien, le paramètre app est une action dans le bureau existant : contacter un demandeur ouvre la messagerie sur son ticket, même si une autre conversation était affichée, sans recharger tout le bureau. Les filtres de messagerie sont réinitialisés pour retrouver la conversation demandée. Une fenêtre fermée est retirée du registre ; une autre entreprise ne réutilise pas ce bureau. Les ouvertures clientes passant d’abord par about:blank restent à consolider pour éviter tous les doublons de postes clients.

Validation : huit tests Node réussis, dont réutilisation, isolation entre entreprises, retour au premier plan et attente du chargement. Tests de messagerie et bureau simulés réussis. Recette Electron Windows à confirmer : ouvrir le technicien, contacter deux demandeurs successifs, vérifier une seule fenêtre technicien et la bonne conversation sans perte des autres applications.
