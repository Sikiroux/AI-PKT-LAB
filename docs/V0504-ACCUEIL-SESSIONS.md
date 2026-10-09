# v0.50.4 — Accueil et sessions

## Changements
- Carte du prochain ticket : demandeur, poste, date, statut réel, accès au ticket et à son équipement.
- État du site : pont, reconnaissance réseau et fichier associé. Un fichier associé ne prouve pas son accessibilité.
- Raccourcis Réseau, Équipements et Tickets ; équipements ouvre directement l’inventaire.
- Entreprises sauvegardées compactes avec seed et badge Active ; création repliable, seed facultative, reprise inchangée.
- Formation indépendante et rappel de sauvegarde Packet Tracer.
- Icônes SVG de l’export Figma, cartes en deux colonnes puis une colonne sur écran étroit.

## Vérification
Tests de navigation, états vides, statut du ticket, poste ciblé et absence de preuve réseau. Suites Python, JavaScript, cœur et ateliers à exécuter avant commit.
Le rendu navigateur Windows doit être vérifié par Damien : aucun navigateur de rendu disponible dans cet environnement. La fidélité pixel par pixel n’est pas déclarée validée.

## Recette utilisateur
1. Sans entreprise : vérifier l’état vide et créer une entreprise sans seed.
2. Avec une entreprise : contrôler la correspondance du ticket, de la personne et du poste.
3. Voir le poste doit ouvrir l’inventaire filtré, sans connexion distante automatique.
4. Vérifier le réseau utilise le même contrôle que Parc et réseau.
5. Reprendre une entreprise sauvegardée puis revenir à Accueil : aucune donnée de l’ancienne entreprise.
6. Vérifier cartes, icônes et disposition sur grand écran et fenêtre étroite.
