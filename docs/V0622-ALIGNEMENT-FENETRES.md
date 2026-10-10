# v0.62.2 — Titres alignés et maquette

## Défaut constaté sur la capture de Damien

Le titre apparaissait au-dessus des contrôles de réduction, agrandissement et fermeture. Les boutons contiennent un div interne d’OS.js et un pseudo-élément ajouté pour le glyphe. La présentation en grille permettait deux lignes ; le titre, occupant toute la hauteur, n’était pas centré verticalement.

## Correctif

- Header OS.js explicitement en ligne flex ; icône, titre et contrôles centrés verticalement.
- Boutons centrés sur une seule ligne ; div décoratif interne masqué, glyphe conservé et zones de clic intactes.
- Titre long tronqué dans l’espace restant, contrôles de taille fixe.
- Fond et grille discrète repris des valeurs de la maquette.
- Raccourcis centrés, jusqu’à dix colonnes, couleurs/bordures/ombres des tuiles reprises. Les quinze applications du technicien restent présentes, contrairement aux dix exemples de la démonstration.
- Icônes SVG des applications correspondantes reprises directement du ZIP de la maquette ; icônes supplémentaires conservées pour les autres outils.
- En-tête avec marque/icône à gauche et informations réelles du poste à droite.
- Fenêtres initialement centrées et positionnées sous les raccourcis lorsque la hauteur disponible le permet. Les positions déjà enregistrées sont conservées.

Ce correctif ne remplace pas les contenus des applications par les données statiques de la maquette. Il ne reproduit pas encore son panneau de mission, sa police externe ou toutes les applications : les moteurs et les fenêtres métier existantes sont conservés.

## Recette Windows à confirmer

1. Ouvrir Arrivées et services, Annuaire et une fenêtre de propriétés : icône/titre/contrôles doivent être sur une ligne.
2. Réduire, restaurer, agrandir et fermer : vérifier que les contrôles restent actifs.
3. Réduire la largeur de la fenêtre : le titre doit céder la place aux boutons.
4. Vérifier la grille du bureau et l’accès aux applications via le lanceur.
5. Déplacer une fenêtre, rouvrir le bureau : la préférence mémorisée doit être conservée.

Les tests automatisés vérifient les interactions ; le rendu Windows reste à confirmer avec Damien.
