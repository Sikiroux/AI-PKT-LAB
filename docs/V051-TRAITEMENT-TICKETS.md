# v0.51 — Traitement des tickets (livré avec v0.52)

## Comportement

La fiche conserve les onglets Échanges, Intervention et Contrôles et aide. Le fil d’activité réunit la réception de la demande, les dialogues datés, les suivis, les changements de statut, les tâches et les qualifications de priorité. Les anciens dialogues sans horodatage affichent « Date non enregistrée » ; aucun horaire n’est inventé.

Un suivi peut être public (destiné au demandeur) ou interne. Une proposition de solution est publique. Les anciens suivis sont considérés publics. L’application reste mono-technicien : ces catégories ne constituent pas une protection multi-utilisateur et aucun message réel n’est envoyé. La vue publique du fil exclut les entrées internes ; les exports du technicien contiennent les deux catégories.

Les tâches sont persistantes : description, durée prévue, état À faire / En cours / Terminée. Les mises à jour vérifient l’identifiant de tâche et sa révision ; une réponse obsolète est refusée. Une tâche terminée est une déclaration, pas une preuve réseau. Les tâches ne bloquent pas à elles seules la résolution ; les contrôles existants restent nécessaires. Les tickets clos gardent leurs tâches et leur fil en lecture seule.

La qualification distingue urgence et impact métier. La matrice pédagogique à quatre niveaux propose une priorité ; la changer nécessite une justification de dix caractères minimum. La matrice est explicitement consultable et définie dans `web/ticket_processing.py`. Elle reprend le principe urgence × impact de GLPI, mais ne prétend pas reproduire toutes ses configurations. Un nombre de personnes affectées suggère un périmètre ; il ne suffit pas à établir la gravité métier.

Les tickets sans qualification conservent leur priorité actuelle jusqu’à qualification explicite. Aucune migration ne change silencieusement leur priorité. Les nouveaux champs restent optionnels dans les sauvegardes. Tâches, suivis et classification utilisent le chemin de métadonnées du serveur : aucun ping ni observation Packet Tracer n’est déclenché.

## Recette utilisateur

1. Reprendre une entreprise et ouvrir un ticket : retrouver la priorité et les anciens suivis.
2. Ajouter un suivi public, puis une note interne ; filtrer le fil et vérifier leur destination.
3. Ajouter une tâche avec dix minutes prévues, la démarrer puis la terminer ; vérifier que cela ne valide pas automatiquement le ticket.
4. Qualifier urgence et impact ; consulter la matrice. Choisir une priorité différente sans justification : refus. Ajouter une justification : enregistrement.
5. Reprendre la sauvegarde : retrouver tâches, suivis et qualification.
6. Résoudre puis confirmer selon la procédure existante. Sur ticket clos, vérifier que le traitement reste en lecture seule ; la réouverture conserve l’historique.

## Références officielles

- GLPI, gestion des tickets : https://help.glpi-project.org/documentation/modules/assistance/tickets/ticketmanagement
- GLPI, suivis : https://help.glpi-project.org/documentation/modules/assistance/tabs/followup
- GLPI, tâches : https://help.glpi-project.org/documentation/modules/assistance/tabs/task

## Limites

Pas de notifications réelles, équipes multi-techniciens, SLA, pièces jointes, planning de tâches, validations hiérarchiques ni journal d’audit immuable. Les notes du compte rendu restent une synthèse modifiable ; le fil ne reconstitue pas leurs anciennes versions. Une qualification ne modifie ni la panne ni les droits du demandeur.
