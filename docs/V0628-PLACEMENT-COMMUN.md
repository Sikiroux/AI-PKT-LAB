# v0.62.8 — Placement logique commun

## Livré

Pour les nouvelles entreprises de trente employés : deux blocs de quinze postes, rangées de cinq, reliés à leur switch existant. Les serveurs ont une grille de deux par deux ; visiteurs, imprimante et portable restent identifiables. Encombrement logique : environ 1660 × 840 unités, dans le canevas de 3900 × 3900. Ce sont des marges conservatrices, pas une mesure des icônes de Packet Tracer.

Le même moteur s’applique aux ateliers utilisant les switches SW-EMP, SW-SRV et SW-GUEST. L’ensemble des appareils de départ et de référence détermine le placement : ajouter un appareil dans la correction ne déplace pas les autres. Tous les instantanés d’une activité PKA sont traités. Aucune adresse, configuration, liaison ou identité physique n’est modifiée par le placement.

Les anciennes entreprises (présentation 0) et les labs classiques restent inchangés. Les réseaux déjà sauvegardés ne sont pas repositionnés automatiquement. Les appareils supplémentaires hors gabarit conservent leur position d’origine.

## Recette Packet Tracer 9 — à effectuer

1. Créer une nouvelle entreprise de trente employés et ouvrir entreprise.pkt.
2. Vérifier les libellés à zoom habituel, les deux blocs utilisateurs et la zone serveurs. Afficher les ports pour contrôler les raccordements.
3. Générer un atelier services d’entreprise en PKT/PKA et comparer départ et correction : les appareils communs doivent rester au même endroit.
4. Vérifier que la correction de l’activité fonctionne toujours.

La validation Python vérifie les espacements, les raccordements inchangés et la concordance des manifestes. Elle ne prouve pas le rendu dans PT9. Le spécimen entreprise saine utilise la seed placement-0628 ; aucun incident initial n’y est injecté.

## Suite

La v0.63 prévoit le réseau V2 : segmentation VLAN, trunks et adressage cohérent. DHCP dynamique et Wi-Fi nécessitent leur propre recette réelle avant d’être déclarés disponibles.
