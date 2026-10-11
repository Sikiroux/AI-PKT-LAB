# v0.62.5 — Aides et arrêt

## Indices

Trois niveaux par famille : observer depuis le poste concerné, comparer avec les propriétés et procédures, retester l’usage et les fonctions saines. Les indications AD, DNS, partages, impression, FTP, accessoires et arrivée d’employé sont différentes. Les anciens parcours PC et Wi-Fi gardent leurs instructions adaptées. Les indices ne consultent pas la cause cachée et ne lancent aucune commande. Un symptôme seul n’est jamais une preuve de sa cause. Le catalogue de dépannage indépendant conserve les indices de ses feuilles ; cette version cible le centre de tickets.

## Quitter

Le bouton dans l’en-tête demande de conserver les brouillons non envoyés et d’enregistrer le réseau dans Packet Tracer. La requête locale POST /quit exige le jeton déjà utilisé pour les mutations et un hôte autorisé. Sous les verrous de l’entreprise et des tickets, elle enregistre les deux états avant de stopper les tâches périodiques. Un échec d’écriture refuse l’arrêt. Le serveur est ensuite arrêté dans un autre thread, puis le pont est fermé. Packet Tracer reste ouvert.

Le lanceur web Windows sort sans pause après un arrêt normal ; la pause reste après une erreur. Une console préexistante ouverte manuellement reste celle de l’utilisateur. Le navigateur tente de fermer l’onglet ; Chrome peut le refuser si le script n’a pas ouvert cet onglet. Dans ce cas, un écran « logiciel arrêté » permet de le fermer manuellement. Aucun processus Chrome n’est tué. Aucun réseau Packet Tracer n’est automatiquement enregistré.

## Recette Windows à effectuer

- Comparer les trois indices de deux familles différentes et suivre les outils indiqués sur le poste du ticket.
- Quitter depuis une application lancée par LANCER-WEB.bat : la console dédiée doit se fermer et localhost:8765 ne doit plus répondre.
- Relancer : retrouver les données enregistrées. Les brouillons non envoyés ne sont pas sauvegardés par cette action.
- Vérifier que Packet Tracer reste ouvert et que les autres onglets Chrome restent intacts.

Tests automatisés : sauvegardes avant arrêt, refus sur erreur disque, choix d’indices par famille et recette complète. Fermeture réelle du terminal Windows et politique Chrome à tester sur le poste de Damien.
