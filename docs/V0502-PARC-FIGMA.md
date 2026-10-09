# v0.50.2 — Parc et réseau

## Périmètre livré

Adaptation du design fourni dans Feedback on Design.zip au HTML/CSS existant, sans dépendance React ou Tailwind. Navigation, fond gris, cartes blanches, bordures, boutons et onglets suivent la maquette.

- Aperçu : connexion du pont, nombre présent selon le dernier inventaire, heure de l’observation, réseau reconnu et accès rapides.
- Équipements : inventaire réel, recherche nom/modèle/IP, type, présence et adresses. Les absents restent visibles.
- Fichier réseau : nom et chemin réels, copie, ouverture du réseau actif, association après Enregistrer sous. Aucun sélecteur fictif.
- Diagnostic : observations réelles et contrôle d’identité via le pont ; outils techniques avancés repliés.

La connexion du pont n’est pas une preuve d’accès Internet, SMB ou FTP. Les raccourcis d’ouverture utilisent la même action et le même environnement. Les onglets disposent d’une navigation clavier (flèches, Début, Fin). Le contenu et le tableau ont des zones de défilement internes.

## Recette Windows à effectuer

1. Reprendre une entreprise, ouvrir Parc et réseau ; changer d’onglet sans perdre l’entreprise.
2. Actualiser l’inventaire ; rechercher un nom, un modèle et une IP ; effacer la recherche.
3. Copier le chemin et ouvrir le réseau depuis Fichier réseau ; vérifier qu’il s’agit du même fichier que celui du bandeau.
4. Relancer le diagnostic ; déconnecter le pont et vérifier que l’interface ne dit pas que tous les services fonctionnent.
5. Contrôler à 1080p, fenêtre réduite et zoom 125 % : onglets accessibles et tableau défilant.

## Limites

Le navigateur de rendu automatisé n’a pas pu être installé dans cet environnement ; la fidélité visuelle finale est à confirmer chez Damien. Les tests des interactions JavaScript ne constituent pas une validation visuelle.

Cette livraison concerne uniquement Parc et réseau : topologie compacte, accès distant aux serveurs et expiration des sessions restent des blocs distincts à traiter.
