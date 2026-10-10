# v0.59 — Services et interfaces, blocs regroupés 0.58–0.59

## Services et événements

Une lecture dédiée `desktop/inspection/state` expose les états réellement présents dans les moteurs : spouleur du poste sélectionné, fichiers, DNS, FTP et annuaire. La réponse omet comptes, mots de passe, contenus de fichiers et états complets. Elle distingue démarré, arrêté et non observé. Le réseau et la configuration restent indépendants.

Source technicien : prérequis d’administration existants. Source client : session distante et accès existants. Autre source/action refusée. La lecture ne lance aucun ping, n’applique aucune opération et n’ajoute aucun événement.

Le journal affiche les 100 dernières entrées conservées, dates et texte, recherchables. Ce sont les événements réels de la session entière, pas des événements Windows par poste, ni des niveaux/identifiants inventés. Les outils d’administration associés conservent leurs validations. Cette première console n’ajoute pas types de démarrage, dépendances, processus ou nouvelles pannes.

## Interfaces

- Partages : quotas/volume dans une fenêtre dédiée ; permissions et commandes de service conservées.
- Administration FTP : capacité dans une fenêtre dédiée ; comptes et droits conservés.
- Mobilité : vue d’état principale, fenêtre Raccordement et fenêtre VPN. Le champ de mot de passe est vidé après tentative et destruction de la fenêtre.
- Parc : vues distinctes Parc connecté, Réserve et remises, Historique. Le stock ne devient pas un appareil PT connecté.
- Aide intégrée : procédure Services et événements. Roadmap actuelle séparée de l’historique.

Une console fichiers/FTP dont la lecture échoue refuse les opérations des fenêtres de configuration déjà ouvertes. Le message de mutation apparaît aussi dans la fenêtre de capacité/quota. Ces fenêtres ne remplacent pas une édition transactionnelle avec résolution de conflits.

Référence de conception : [Microsoft — services et événements dans le Gestionnaire de serveur](https://learn.microsoft.com/fr-fr/windows-server/administration/server-manager/view-and-configure-performance-event-and-service-data). Notre journal reste explicitement celui du simulateur.

## Recette Windows et Packet Tracer 9

1. Sur le technicien avec réseau vérifié, ouvrir Services et événements : comparer chaque état avec sa console associée.
2. Arrêter DNS via sa console puis actualiser Services : DNS doit afficher Arrêté. Réactiver ensuite.
3. Lire Services/Événements en observant la CLI PT : cette lecture ne doit générer aucun ping. Le bouton manuel de vérification réseau conserve son comportement.
4. Effectuer un transfert ou une opération administrative, actualiser Événements et rechercher son texte. Vérifier la portée session entière.
5. Rendre la preuve technicien invalide : la lecture doit refuser et retirer les états périmés. Le bureau client exige sa session distante.
6. Modifier quota et capacité FTP dans leurs fenêtres, provoquer un refus et vérifier le message. Après lecture principale refusée, une fenêtre ouverte ne doit plus modifier.
7. Ouvrir Raccordement et VPN : champs hors de la vue principale, opérations inchangées, mot de passe effacé. Vérification réseau explicite seulement.
8. Dans Parc, passer entre les trois vues ; préparer puis remettre et restituer un article avec les contrôles existants.
9. Contrôler clavier, tailles, scroll, fenêtres et contrastes. Aucun rendu Windows/PT réel n’est déclaré validé par les tests automatisés.
