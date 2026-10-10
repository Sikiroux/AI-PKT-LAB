# v0.62.1 — Bureau technique et annuaire

Première passe visuelle inspirée de la maquette fournie. Le moteur OS.js, les routes et les services restent ceux du simulateur.

## Changements

- Fond pétrole, icônes en grille compacte et raccourcis conservés.
- Barre des tâches intégrée à la barre système : fenêtres actives et réduites distinctes. Documents et Terminal restent accessibles via Applications et les icônes du bureau.
- Fenêtres et contrôles harmonisés, animation courte désactivée si les mouvements réduits sont demandés.
- Recherche et filtre d’unité regroupés avec les actions de l’annuaire.
- Liste structurée : nom, identifiant, unité et état réel du compte. Les états Actif, Désactivé et Verrouillé concernent le compte, pas sa connectivité.
- Inspecteur : propriétés et groupes directs réels, ouverture des propriétés existantes par bouton, double-clic ou Entrée.
- Contraste de sélection corrigé ; arborescence sans défilement horizontal ; adaptation à la largeur de la fenêtre.

Aucune alerte DNS, dernière connexion, progression ou donnée de démonstration n’est ajoutée. Les appels et contrôles de permissions sont conservés. Le panneau de mission, l’écran de connexion et les applications métier détaillées ne sont pas redessinés dans cette passe.

## Recette visuelle à effectuer

1. Ouvrir le bureau technicien à 1920×1080, puis sur une fenêtre plus petite : tous les raccourcis doivent rester accessibles par Applications.
2. Ouvrir deux applications : réduire/restaurer depuis les boutons de la barre des tâches, puis agrandir et fermer depuis les contrôles OS.js.
3. Annuaire : rechercher un utilisateur, filtrer une unité, choisir un objet ; le résumé et les groupes doivent correspondre au bon compte.
4. Double-cliquer et utiliser Entrée : vérifier les propriétés et les actions administratives existantes.
5. Passer aux Groupes, Ordinateurs, Historique et Stratégie ; réduire la largeur de la fenêtre et vérifier les défilements internes.
6. Vérifier un compte désactivé et un compte verrouillé, puis actualiser après modification.
7. Bureau client : vérifier Documents, Terminal et les seules applications autorisées sur ce poste.

La recette JavaScript/Python vérifie les interactions existantes. Le rendu visuel dans un navigateur Windows et les interactions Packet Tracer restent à confirmer : aucun navigateur graphique local exploitable n’était disponible pour capturer cette passe.
