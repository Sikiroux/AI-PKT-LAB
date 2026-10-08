# v0.46.2 — Fiches des postes et documentation intégrée

## Deux entrées du bureau du technicien

**Fiches des postes** présente le parc de l’environnement actif : postes clients avec un bureau simulé, portable du technicien et appareils observés dans Packet Tracer. La recherche porte sur le nom, l’utilisateur et le numéro de série. Sélectionner explicitement un appareil pour consulter sa fiche.

La fiche affiche son identité, son utilisateur, son rôle, l’adresse IP prévue ou relevée, le lien éventuel avec l’intervention et le résultat d’accès distant calculé par les contrôles existants. Consulter la fiche ne réalise pas un nouveau ping et n’atteste pas d’un accès Internet. Un appareil observé sans bureau simulé ne reçoit pas de bouton de prise en main.

Le bouton **Prendre la main sur [nom]** transmet le numéro de série de la fiche sélectionnée. Une recherche différente n’attribue jamais implicitement cette action à un autre poste. En cas d’échec du rafraîchissement, les anciennes fiches sont retirées.

**Documentation** contient six procédures :

1. Repérer son environnement.
2. Consulter un poste et prendre la main.
3. Accéder aux documents partagés.
4. Utiliser l’annuaire.
5. Préparer et remettre un matériel.
6. Vérifier et terminer une intervention.

Les procédures sont consultables et recherchables sans accès réseau. Le lien depuis une fiche ouvre la procédure des postes, y compris quand la documentation est déjà ouverte. Elles décrivent le fonctionnement du simulateur ; elles ne révèlent ni une cause cachée ni la correction d’un exercice particulier.

## Continuité UX

Les deux applications utilisent le bureau et les fenêtres existantes : icônes SVG, barre des tâches, réduction, agrandissement et fermeture. La fiche sélectionnée et l’article documentaire ont un panneau dédié ; sur les petites fenêtres, les panneaux passent en une colonne avec une liste limitée en hauteur.

La liste d’accès distant séparée n’est plus affichée comme une seconde icône du bureau du technicien : la prise en main part de la fiche du poste. Les anciens chemins serveur restent compatibles.

Pas de nouveau bouton d’ouverture Packet Tracer et pas de second fichier réseau. La prise en main repose sur le même chemin serveur que les autres accès distants.

## Périmètre restant

Le coffre d’accès locaux, l’authentification locale correspondante, les souris/claviers/écrans manipulables et leurs tickets restent à développer. La fiche le précise au lieu d’afficher des mots de passe ou des périphériques factices. L’annuaire AD conserve ses fonctions de réinitialisation ; cette livraison ne rend pas ses credentials lisibles.

Il s’agit d’un premier bloc de navigation et de documentation, pas d’une refonte complète de toutes les fenêtres ou du portail de tickets.

## Tests

Tests DOM : ciblage par numéro de série, recherche sans changement implicite de cible, distinction du technicien, retrait des anciennes fiches après un échec, recherche documentaire et navigation vers une procédure déjà ouverte. La documentation ne produit aucune requête réseau ; consulter une fiche ne lance aucune connexion. Ces contrôles ne remplacent pas une vérification visuelle dans un navigateur.
