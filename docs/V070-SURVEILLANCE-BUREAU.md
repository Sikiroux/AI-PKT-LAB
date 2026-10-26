# v0.70 — Priorité au bureau consulté

## Constat et portée

Le parc de 30 postes est contrôlé un poste à la fois. La preuve ICMP expire après 45 secondes. La priorité précédente portait sur toutes les sessions distantes ouvertes, y compris les onglets abandonnés. Un tour complet peut donc dépasser la durée de validité d'une preuve. Ce constat explique un risque de passage à « non vérifié », sans démontrer la cause de chaque incident signalé.

## Changement

Le GET d'état d'un bureau visible signale sa présence, avec environnement et numéro de série vérifiés contre la réponse serveur. Une présence est valable 15 secondes, en mémoire seulement, sur horloge monotone. Un onglet masqué continue à lire son état mais ne renouvelle plus cette priorité. La disparition d'une présence ne déconnecte jamais le compte.

Un passage périodique sur deux privilégie les bureaux récemment consultés, le moins récemment contrôlé d'abord. L'autre reste destiné au parc entier. Sans présence récente, le comportement précédent est conservé. Le bureau technicien contribue à prioriser le poste principal et ses trajets communs vers les services.

La présence ne modifie ni authentification, ni preuve réseau, ni état du ticket. Aucune accélération automatique n'est ajoutée. Les contrôles explicites conservent leur comportement. Aucun allongement de la durée de validité, aucune réussite par défaut.

## Limites

Ce changement réduit la concurrence avec les onglets abandonnés, mais ne garantit pas un contrôle toutes les 45 secondes : un pont lent ou plusieurs bureaux visibles peuvent toujours laisser expirer une preuve. Ce n'est pas un moteur Packet Tracer indépendant sans interface. Les autres points du bloc stabilité/cohérence restent à traiter et les incidents ne sont pas déclarés tous corrigés.

## Recette Windows / Packet Tracer 9, à faire

1. Ouvrir une entreprise à 30 postes et plusieurs bureaux distants. Laisser un bureau visible, masquer les autres. Comparer l'horodatage des contrôles avant/après, sans lancer de vérification manuelle.
2. Revenir sur un autre bureau : vérifier qu'il redevient prioritaire après ses lectures d'état. La priorité précédente doit disparaître après 15 secondes sans lecture visible.
3. Fermer/recharger un onglet : la présence ne doit jamais ouvrir ou fermer une session utilisateur.
4. Débrancher volontairement un câble dans une entreprise de test : attendre le contrôle puis constater un échec réel. Rebrancher et contrôler de nouveau. Une simple présence ne doit rien valider.
5. Arrêter le pont : état inconnu, fenêtres conservées, aucune réparation ni clôture automatique. Le rétablir puis vérifier les outils AD/DNS.

Tests automatisés : présence bornée, isolation d'environnement, priorité avec équité sur 30 postes, absence d'authentification/validation implicite, GET contrôlé, paramètres navigateur visible/masqué. Ces tests ne remplacent pas la recette PT9.
