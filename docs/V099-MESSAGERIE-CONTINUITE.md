# v0.99 — Messagerie : continuité de lecture et erreurs partielles

## Historique

Une actualisation indisponible conserve la dernière conversation consultée en lecture. Les commandes sont suspendues jusqu’à une actualisation réussie, et un message indique que les données conservées ne sont pas à jour. Un refus d’environnement ou une réponse destinée à une autre entreprise retire cet historique de l’affichage.

Si une question reçoit sa réponse mais que l’opération suivante de marquage comme lu échoue, la réponse reste affichée. L’interface distingue cette réussite de l’échec secondaire. Aucune réémission automatique de la question, de l’export de note ou des autres écritures n’est effectuée par l’actualisation.

## Lecture

Chaque conversation conserve sa propre position de défilement pendant l’ouverture de la messagerie. Un passage d’Alice à Bob puis un retour à Alice ne reprend plus la position de Bob. L’arrivée d’un message suit le bas de l’historique uniquement si la lecture était déjà en bas ; remonter dans les messages préserve la position.

Ces positions sont gardées en mémoire pendant la vie de la fenêtre. Elles ne sont pas annoncées comme conservées après fermeture du navigateur.

## Validation

53 suites JavaScript et 7 tests Python ciblés passent. Les régressions vérifient les erreurs partielles, la conservation de l’historique, la suspension des commandes, le refus d’environnement, l’absence de réémission lors d’une actualisation et les positions indépendantes des conversations.

Les réponses restent scénarisées. La recette réelle dans Chrome reste ouverte.
