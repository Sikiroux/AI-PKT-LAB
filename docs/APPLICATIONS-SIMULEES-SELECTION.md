# Applications simulées : sélection des briques GitHub

Recherche du 4 octobre 2026. Préparation avant le terminal IOS ; aucune des briques ci-dessous n'est nouvellement intégrée dans la v0.17. OS.js est déjà utilisé pour le bureau.

## Principe

Le serveur existant reste responsable de la seed, des comptes, droits, services, tickets et observations Packet Tracer. Une interface réutilisée n'introduit pas une deuxième simulation indépendante. Chaque action désigne l'environnement, le poste et l'utilisateur. Un état réseau inconnu ne signifie pas connecté.

## Candidats

| Projet | Apport réutilisable | Limite / adaptation | Décision proposée |
|---|---|---|---|
| [OS.js File Manager](https://github.com/os-js/osjs-filemanager-application) | Explorateur de fichiers déjà adapté à OS.js v3 | Raccorder les opérations aux fichiers et droits simulés ; auditer son utilisation du VFS avant adoption. Ne pas donner accès au disque réel. | Premier candidat pour Documents et partages |
| [OS.js Settings](https://github.com/os-js/osjs-settings-application) | Application de paramètres du bureau ; licence BSD-2-Clause vérifiée | Ses réglages OS.js ne simulent pas la carte réseau, Windows ou les services. | Facultatif ; priorité aux paramètres utiles aux exercices |
| [JimSycurity/md2ADUC](https://github.com/JimSycurity/md2ADUC) | Arbre utilisateurs, groupes, ordinateurs et OU, apparence de console ADUC ; MIT annoncée | Le README précise que les boutons de barre d'outils sont visuels. Ce n'est pas un moteur AD. Ajouter propriétés, verrouillage, activation et appartenance aux groupes via notre serveur. | Candidat intéressant pour l'interface Annuaire |
| [InkJS](https://github.com/y-lohse/inkjs) | Dialogues à choix, variables et histoires sauvegardables ; MIT | Écrire les conversations ; injecter les observations validées sans donner à l'interface le droit de modifier la panne. Pour quelques dialogues, un arbre JSON interne peut suffire. | Tester après le premier scénario Annuaire/partages |
| [xterm.js](https://github.com/xtermjs/xterm.js) | Affichage de terminal, saisie et sélection ; MIT | N'exécute aucune commande : notre serveur doit gérer les commandes PC simulées et le pont PT. IOS reste reporté. | Réserve pour le terminal PC, puis IOS |
| [rogeriorch77/it-support-simulator](https://github.com/rogeriorch77/it-support-simulator) | Scénarios français, simulation d'appels, terminal CMD et tickets selon son README | Machines préconfigurées, auth Supabase ; pas de liaison PT décrite. Licence de réutilisation non confirmée lors de cette recherche. | Inspiration ; ne pas copier le code sans licence explicite |
| [nicolas-carolo/adsimulator](https://github.com/nicolas-carolo/adsimulator) | Génération de graphes de relations AD, export JSON | Modélisation de graphes, pas console de support ou simulation d'authentification de postes. | Pas nécessaire au premier prototype |

Les licences doivent être conservées lors de toute intégration, et vérifiées sur la révision exacte retenue. Les versions et dépendances seront figées après un essai technique. Cette sélection s'appuie sur les README/licences disponibles, pas sur un audit complet du code ni des performances.

## Applications à viser, dans l'ordre

1. **Explorateur / Documents** : ouvrir un partage, distinguer lecture/écriture, afficher une erreur adaptée au réseau ou aux droits.
2. **Annuaire simulé** : consulter un utilisateur, débloquer son compte, changer son groupe. Reprendre la présentation ADUC si l'essai confirme qu'elle s'adapte proprement.
3. **Services du poste** : afficher et démarrer/arrêter quelques services choisis. Petite application OS.js dédiée ; aucun moteur compatible identifié dans cette sélection.
4. **Paramètres réseau** : visualiser les données PT observées. La modification devra passer par une capacité réelle du pont ; ne pas inventer une réussite.
5. **Échanges client** : dialogues à choix guidés par l'état du scénario ; InkJS ou JSON selon complexité.
6. **Terminal PC**, puis **IOS** : façade xterm.js si elle améliore la saisie, sans exécuter de commandes sur le PC réel.

## Premier exercice combiné à concevoir

« Documents partagés inaccessibles » avec causes compatibles : réseau inaccessible, utilisateur verrouillé, service simulé arrêté, lecture refusée. Générer un état sain puis une cause précise depuis la seed. Les causes et permissions sont conservées côté serveur ; les symptômes sont calculés depuis l'état actuel. L'étudiant ne voit pas les booléens de correction.

La session entreprise conserve son réseau. Un lab combiné devra disposer de son propre état et fichier PT, sans modifier cette session. Les labs combinés ne sont pas encore implémentés dans v0.17.
