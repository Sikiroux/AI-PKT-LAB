# v0.96 — Annuaire : clavier et conservation du contexte

## Interactions

- Flèches Haut/Bas, Début/Fin : sélectionner un objet et déplacer le focus sans reconstruire la liste ni modifier l’objet.
- Entrée et Alt+Entrée : ouvrir les propriétés de cet objet.
- Maj+F10 : menu contextuel. Flèches et Début/Fin parcourent les commandes ; Échap ferme le menu et restaure le focus.
- Ctrl+F : accéder à la recherche. F5 : relire l’annuaire.
- La sélection au clic conserve l’élément DOM pour préserver le double-clic.
- Les propriétés déjà ouvertes continuent de viser leur objet, même lorsque la sélection de la console change.

## Contexte

La vue active, les recherches propres aux vues, les sélections et l’unité d’organisation sont conservées dans le stockage de session du navigateur, par environnement et bureau. Les identifiants d’objets disparus sont revérifiés lors de la lecture. Aucun mot de passe saisi dans un formulaire n’est enregistré dans cette préférence.

Une actualisation conserve les filtres ; un changement de vue retrouve sa recherche. Une indisponibilité de l’annuaire continue de retirer les commandes reposant sur des données devenues indisponibles.

## Validation

50 suites JavaScript passent. Le nouveau parcours vérifie sélection sans opération, navigation entre objets, stabilité de la cible, menu clavier, recherches par vue, actualisation, ouverture des propriétés et restauration du contexte. Les régressions existantes vérifient aussi l’identité des opérations sur des propriétés déjà ouvertes.

La recette visuelle et clavier réelle dans Chrome reste ouverte. Cette version n’ajoute pas de nouvelle opération administrative et ne constitue pas une reproduction complète d’ADUC.
