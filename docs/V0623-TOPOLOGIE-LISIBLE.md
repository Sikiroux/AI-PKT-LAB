# v0.62.3 — Topologie lisible et icônes des fenêtres

## Changements

Le placement précédent mélangeait dans la même grille les postes des deux switches et occupait environ 3300 × 2500 unités. Les 30 clients sont désormais répartis en deux éventails circulaires selon leur switch réellement câblé : postes impairs sur SW-EMP, pairs sur SW-EMP2. Serveurs et visiteurs occupent une zone distincte à droite ; portable du technicien et imprimante restent sous leur groupe. L’étendue des centres est inférieure à 2000 × 1000 unités, sans étirer le réseau jusqu’aux limites disponibles.

Le rayon réserve une marge conservatrice pour les icônes et libellés. Il ne prétend pas mesurer les pixels de Packet Tracer : zoom, modèles et affichage des ports influencent le rendu réel. Les câbles restent les lignes droites de Packet Tracer ; les liaisons entre switches et routeur peuvent encore croiser certains traits. Aucun routage orthogonal fictif n’est ajouté.

Le plan enregistré porte la version 2. La seed et les noms restent reproductibles. Aucune modification des ports, IP, droits, pannes ou contrôles. Les réseaux déjà sauvegardés conservent leur placement ; créer une nouvelle entreprise pour essayer cette disposition. Pas d’outil de réagencement de sauvegarde dans ce correctif.

Les barres de titre affichent directement le même SVG que les raccourcis et boutons de tâches, dans la tuile OS.js. Cela évite le rendu d’une image SVG via background-image. Les contrôles réduire, agrandir et fermer sont conservés.

## Vérification automatisée

Tests de séparation des rectangles de réservation (110 × 80 unités), étendue totale, couverture des appareils et proximité du switch réellement associé sur 30 seeds. Les tests existants vérifient la correspondance XML/manifest et que seules les coordonnées logiques sont modifiées. La recette unifiée couvre également les autres moteurs et applications.

## Recette réelle à effectuer

1. Extraire la nouvelle version, redémarrer le logiciel et recharger le navigateur avec Ctrl + F5.
2. Ouvrir Annuaire, Parc et DNS : contrôler l’icône à gauche du titre, puis réduction, restauration et agrandissement.
3. Créer une nouvelle entreprise de 30 employés ; ouvrir son fichier dans Packet Tracer. Vérifier la lisibilité du placement, des noms et câbles au zoom de travail habituel.
4. Vérifier que chaque groupe de postes se raccorde à son propre switch et que serveurs/visiteurs restent distincts. Les étiquettes de ports dépendent des préférences PT.
5. Essayer plusieurs seeds et un petit site ; le petit site conserve sa disposition précédente.
6. Reprendre une ancienne sauvegarde et confirmer que ses positions et interventions sont conservées.

Ces tests visuels sont à effectuer dans PT9. Aucun ping ni changement de réseau actif n’est lancé par la livraison elle-même.
