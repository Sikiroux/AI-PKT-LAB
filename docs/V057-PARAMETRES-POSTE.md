# v0.57 — Paramètres du poste

La fenêtre principale conserve les rubriques Réseau, Applications et Lecteur réseau. Les observations réseau proviennent de Packet Tracer : aucune modification IP ou validation de connectivité n’est inventée.

Les applications non essentielles ont une fenêtre dédiée de gestion, ciblée par identifiant. Une désinstallation exige une confirmation. Le bouton et l’état sont relus après opération. Les applications essentielles restent protégées.

Le lecteur Z: présente son chemin en lecture seule. Modifier le lecteur… ouvre ses propriétés dans une fenêtre séparée. Enregistrer le chemin ne prouve pas son accessibilité : Documents partagés reste l’outil de vérification par les moteurs.

Une lecture refusée retire les informations périmées de la fenêtre principale. Les fenêtres déjà ouvertes gardent leur saisie mais toute modification est refusée tant qu’une lecture n’a pas rétabli l’état. Les erreurs du moteur restent visibles ; aucun installateur Windows réel ni nouveau réglage réseau n’est ajouté.

## Recette manuelle Windows

1. Ouvrir Paramètres puis Réseau : vérifier interface, adresse, masque et les distinctions observé/non observé.
2. Dans Applications, ouvrir Gérer une application : la liste principale ne contient plus de commandes de désinstallation directes.
3. Refuser puis accepter une désinstallation. Vérifier état et libellé après opération. Les applications essentielles ne sont pas désinstallables.
4. Dans Lecteur réseau, ouvrir Modifier le lecteur…, saisir le chemin et enregistrer. Vérifier ensuite son accès depuis Documents partagés.
5. Provoquer un refus de lecture du poste : la vue principale ne doit pas continuer à présenter d’anciens réglages. Une fenêtre de lecteur déjà ouverte doit refuser de modifier.
6. Reprendre une lecture réussie et retester les actions.
7. Vérifier dimensions, clavier et défilement. Les tests automatiques ne valident pas le rendu Windows ou une session Packet Tracer réelle.
