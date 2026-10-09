# v0.50.3 — Détails visuels Figma

Correction des écarts signalés sur les captures Windows de v0.50.2.

## Changements

- SVG repris depuis src/App.tsx du ZIP Feedback on Design : logo, navigation, actions du header, accès rapides, fichier, diagnostic.
- Bandeau entreprise compact ; badges redondants et ouverture supplémentaire masqués sur Parc et réseau.
- Synchroniser bleu, icônes persistantes même quand un bouton change de libellé.
- Notifications en bas à droite : elles ne déplacent plus les onglets.
- Aperçu avec badge et icône réseau ; fichier avec icône violette ; cartes et séparateurs rapprochés de la maquette.
- Inventaire : type d’icône routeur/serveur/poste, indicateur de présence, recherche arrondie avec loupe. Un seul défilement vertical dans le contenu du site.
- Diagnostic : lignes avec icônes et indicateurs, rappel de sauvegarde titré.

## Limites fonctionnelles conservées

Le fichier est associé par son chemin complet. Le bouton fictif « Parcourir » de Figma n’a pas été ajouté : le serveur local ne propose pas encore de sélecteur natif. L’état des services n’est pas déduit de la seule connexion du pont. Le diagnostic de fichier indique « Non vérifié » faute de preuve de lecture dédiée. Les icônes, couleurs et disposition restent indépendantes de ces limites.

## Recette visuelle Windows

Comparer les quatre onglets aux captures Figma, à zoom identique. Vérifier icônes/logo/header, accès rapides et diagnostic, recherche, état absent, et défilement unique. Vérifier aussi le passage Accueil → Parc et réseau → Tickets et l’écran partagé.

Le navigateur de rendu automatisé est indisponible ici ; le rendu final sous Windows reste à confirmer. Les tests d’interactions ne prouvent pas une correspondance pixel par pixel.
