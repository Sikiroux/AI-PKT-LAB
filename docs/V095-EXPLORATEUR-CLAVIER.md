# v0.95 — Interactions de l’Explorateur

La séparation existante entre sélection et ouverture est conservée. Les interactions sont affinées :

- Flèches Haut/Bas, Début et Fin : déplacer la sélection et le focus sans lire le contenu.
- Entrée : ouvrir explicitement le fichier.
- Alt+Entrée : propriétés du fichier sélectionné, sans contrôle réseau supplémentaire.
- Maj+F10 : menu contextuel, avec navigation aux flèches et fermeture par Échap.
- Ctrl+F : focus dans la recherche de fichiers.
- F5 : actualiser la liste dans la fenêtre.
- Clic et double-clic possibles sur la ligne, en complément du nom.
- Ouvrir et Propriétés désactivés sans sélection visible ou pendant une opération.
- Une recherche qui masque la sélection retire celle-ci et ferme le menu contextuel.
- Recherche et sélection conservées dans le même onglet, par entreprise, poste et emplacement local/partagé.

Les protections des brouillons et l’identité du fichier concerné restent en place. Les propriétés présentent les métadonnées enregistrées, pas une vérification en direct des permissions.

## Validation

49 suites JavaScript passent, dont un nouveau parcours clavier avec plusieurs fichiers. Le test vérifie la sélection sans lecture, l’ouverture explicite, les propriétés, la sélection masquée, l’actualisation et l’isolation des recherches entre local et partagé.

Le rendu visuel et le comportement clavier dans Chrome restent à contrôler en recette réelle. Aucun accès au réseau ou aux fichiers réels de l’ordinateur n’a été ajouté.
