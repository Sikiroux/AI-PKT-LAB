# v0.88 — Première passe de refonte et messagerie

## Parcours livré

- Accès Bureau technicien depuis l’en-tête principal.
- Base visuelle commune pour le centre de tickets et le bureau : couleurs, typographie système, tableaux, actions, états de sélection, focus clavier et disposition adaptative.
- Application Messagerie sur le bureau technicien et dans le lanceur.
- Depuis Communication dans le ticket, ouverture directe de sa conversation.
- Recherche, épingles, historique et suivi des messages lus conservés par entreprise. Actualiser récupère les nouvelles demandes ; aucune notification en temps réel n’est annoncée.
- Les échanges existants restent disponibles dans la messagerie et ne sont plus recopiés automatiquement dans le fil d’intervention.
- Ajouter une note au ticket crée volontairement un suivi interne, sans doublon pour le même échange. Les suivis déjà enregistrés sont conservés.
- Retour au ticket avec contrôle de l’entreprise, sans basculer silencieusement de session.
- Conservation de la recherche, de la catégorie et de l’article documentaire dans le même onglet, par environnement. Un lien contextuel ouvre l’article demandé.

## Limites explicites

Cette version constitue le premier lot de la roadmap. Les conversations utilisent les questions et réponses scénarisées existantes. Les discussions libres avec tous les salariés, le canal collectif, l’IA, les notifications automatiques et l’intégration des incidents réseau aux arrivées ne sont pas livrés ici.

La recette Chrome distante n’a pas pu atteindre le serveur local (connexion refusée). Le rendu visuel n’est donc pas validé. Les tests du DOM simulé ne remplacent pas cette recette ni un essai réel dans Packet Tracer.

## Recette à effectuer

1. Reprendre une entreprise et ouvrir un ticket préparé.
2. Ouvrir Communication puis Contacter le demandeur.
3. Vérifier le nom du demandeur, le poste et le numéro de ticket.
4. Poser une question, consulter la réponse, épingler la conversation.
5. Ajouter une note au ticket ; répéter l’action et vérifier l’absence de doublon.
6. Revenir au ticket : seule la note choisie apparaît dans le suivi interne.
7. Ouvrir Documentation, rechercher un article, fermer puis rouvrir l’application : recherche et article sont conservés.
8. Changer d’entreprise et vérifier que les conversations et préférences sont séparées.
9. Tester le parcours sur un écran étroit et contrôler les défilements, les contrastes et la navigation clavier.
