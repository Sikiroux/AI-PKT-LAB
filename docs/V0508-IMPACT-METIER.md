# v0.50.8 — Impact métier des incidents FTP

Chaque employé généré possède une liste de dépendances métier. Dans le scénario par défaut, Commercial et Opérations utilisent FTP : 10 personnes sur 30. Il s’agit d’une configuration pédagogique de cette entreprise, pas d’une règle générale. Les dépendances sont indépendantes des droits techniques : elles ne modifient aucun compte FTP et ne prouvent aucune connexion.

Un incident FTP est signalé par un poste dépendant du service et touche les activités des autres utilisateurs dépendants. Les autres employés ne sont pas marqués dégradés par cette seule panne. Les signalements restent regroupés en un incident partagé. Une demande forcée sur un poste sans dépendance est refusée avant toute mutation.

Les anciens effectifs sans champ de dépendances utilisent la correspondance de leur service métier. Si aucun employé n’est identifiable, seul le poste signalé est compté ; on n’invente pas 30 utilisateurs affectés. Les anciens tickets FTP ouverts sans indication de provenance reçoivent ce périmètre lors de la reprise ; cible, notes, priorité choisie et historique restent conservés. Les tickets clos conservent leur impact historique.

La fiche indique « Impact estimé » et les services concernés. L’application Documentation contient une rubrique expliquant les dépendances. Cette liste est un modèle métier, pas un test réseau individuel. Le détail des activités, délais, commandes et tâches reste à simuler ultérieurement.

## Recette
- Nouvelle entreprise : provoquer un incident FTP et lire 10 personnes / Commercial, Opérations.
- Vérifier que le demandeur appartient au périmètre et que les autres services restent disponibles dans la vue des activités.
- Rétablir le service : les activités dégradées doivent redevenir disponibles.
- Lire Documentation > Activités et dépendances des services.
- Reprendre une ancienne sauvegarde : vérifier les notes et la cible du ticket ouvert, ainsi que son impact ajusté.

Aucun changement de topologie, de pont ou de mode Fast Forward dans cette version.
