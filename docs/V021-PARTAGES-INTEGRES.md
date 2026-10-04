# v0.21 — fichiers, partages et permissions intégrés

Le moteur de fichiers provient de `codex/file-sharing-simulation-engine`, commit corrigé `7fcc9b4a75c6071529f65d6ec3700f542d660811`. Ses tests et documentation sont conservés. L'intégration ajoute un adaptateur au serveur unique et au même environnement Packet Tracer.

## Installation et sauvegardes

Remplacer le code de la précédente version en conservant les dossiers de sessions. Arrêter le serveur précédent avant de lancer la nouvelle version. Actualiser le navigateur avec Ctrl+F5. La reprise d'une session sauvegarde son JSON dans `session.before-files.json` avant migration ; les sessions déjà migrées ne sont pas recréées.

Le partage Documents conserve ses noms de fichiers et les grants utilisateurs/groupes de l'annuaire précédent. L'ancienne version ne stockait que des noms : les contenus initiaux sont donc des textes fictifs de formation, pas des documents récupérés. Les contenus saisis ensuite sont réellement persistés dans le JSON de simulation.

Les permissions migrées sont copiées dans deux couches : partage et fichiers. Lecture donne list/read ; écriture donne write/delete. Les memberships AD restent ceux de l'annuaire. Les métadonnées directory_resource identifient les groupes historiques pour les boutons et les tickets AD ; elles ne constituent plus un correcteur d'accès parallèle. file_service est l'autorité des permissions sur les fichiers.

## Essai du parcours

1. Reprendre l'environnement et ouvrir son réseau dans Packet Tracer. Rétablir et sauvegarder la liaison du client si nécessaire, puis Vérifier maintenant.
2. Ouvrir le bureau technicien, puis Annuaire. Ajouter le demandeur aux groupes Documents-Lecture et Documents-Ecriture selon l'objectif du ticket.
3. Ouvrir l'accès distant. Dans Session utilisateur, connecter le demandeur avec son mot de passe de formation actuel.
4. Dans Documents : Actualiser, choisir un fichier, Ouvrir. Modifier son texte puis Enregistrer. Nouveau crée un fichier sous un nouveau nom. Supprimer retire le fichier choisi après confirmation.
5. Dans le bureau technicien, ouvrir Partages. Choisir la couche Partage ou Fichiers et l'action Lister/Lire/Écrire/Supprimer ; cocher les utilisateurs et groupes autorisés.
6. Retirer la lecture dans une seule couche : l'ouverture doit être refusée malgré les grants de l'autre couche. Rétablir ce grant pour réparer.
7. Appliquer un quota dur de 1 octet : la croissance est refusée, la lecture reste possible. Sans quota retire cette limite ; un quota souple autorise l'écriture avec avertissement. Les valeurs affichées et saisies sont en octets.
8. Arrêter le service ou bloquer TCP 445 simulé : les fichiers deviennent indisponibles ; le bureau distant peut rester connecté. La console technicien permet de réparer sans accès au partage utilisateur.

Les boutons de groupe historiques restent disponibles, mais un groupe ne contourne pas une ACL devenue restrictive. Le moteur exige un compte utilisable, une authentification actuelle, une observation fraîche, les deux couches de droits et les contraintes du fichier. Les noms ne sont pas retournés dans l'état utilisateur quand le droit de liste est refusé.

## Compatibilité tickets et concurrence

Les cinq familles AD v0.20 sont conservées. Le nouvel exercice prépare les grants du demandeur dans les deux couches puis injecte l'incident AD ; les autres utilisateurs et groupes sont préservés. Les réglages disque, quotas et service ne sont pas réinitialisés : des modifications administratives laissées en panne peuvent donc ajouter un obstacle. Les rétablir avant de lancer un exercice AD isolé.

Le contrôle d'écriture des anciens tickets évalue une création ou mise à jour du fichier Test.txt, sans l'écrire lors du contrôle. Le bouton historique d'écriture réalise cette opération. L'explorateur permet de travailler sur d'autres fichiers. Les éditions utilisent la revision reçue lors de l'ouverture ; une modification concurrente du service impose une nouvelle ouverture après REVISION_CONFLICT. Une création/suppression vérifie également la revision.

Une reprise ferme les anciennes sessions et efface les observations. Contenus, ACL, quotas et incidents persistent. Toutes les routes de fichiers exigent l'environnement actif ; les actions utilisateur exigent la prise en main distante actuelle. Identité, memberships et preuve réseau sont construits par le serveur, pas acceptés du navigateur. L'administration reste une console locale de formation avec rôle technicien imposé : ce n'est pas un modèle d'authentification administrateur de production.

## Limites et validation

Le contrôle réseau reste ICMP dans PT, indiqué comme `icmp_proxy`. Le pare-feu TCP 445 et le service SMB sont simulés côté web ; aucun test TCP ou vrai SMB n'est prétendu. Les adresses sont utilisées directement ; chemins UNC, lecteurs mappés et résolution DNS simulée attendent un prochain bloc. L'UI gère le partage Documents migré ; le moteur supporte plusieurs partages mais leur création n'est pas encore exposée.

Pas de sous-dossiers, deny-ACE, héritage NTFS, verrouillage SMB réel ou disque du système hôte. La permission « fichiers » de cette v1 est celle de la racine du partage, commune aux fichiers. Les fichiers peuvent être marqués lecture seule dans Partages après Choisir un fichier. La console n'expose jamais leur contenu.

Tests Python : migration avec sauvegarde et idempotence, deux ACL, auth, lecture/création/édition/suppression, conflit de version, quotas et disque, administration depuis le technicien, environnement et prise en main, persistance et compatibilité avec les incidents AD. Syntaxe JavaScript vérifiée. Le parcours graphique et Packet Tracer réel restent à tester.
