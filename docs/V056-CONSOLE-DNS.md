# v0.56 — Console DNS

## Changement

La rubrique Enregistrements affiche la zone interne existante et une liste recherchable par nom, type ou valeur. Le clic sélectionne sans ouvrir de formulaire ; le double-clic ou Entrée ouvre les propriétés. Le bouton Nouvel enregistrement ouvre une fenêtre dédiée. Les noms, types, valeurs, TTL et états viennent du moteur.

Chaque fenêtre conserve son identifiant cible même si la liste est filtrée. Après un rafraîchissement, une entrée supprimée ou une console inaccessible bloque son édition. Les erreurs s’affichent dans la fenêtre concernée. Une nouvelle lecture réussie réactive les fenêtres encore valides.

Résolution, cache, configuration client et service conservent leurs routes et validations existantes. La simulation reste limitée à une zone interne et aux types A/AAAA/CNAME ; ni nouvelles zones, ni réplication AD, ni récursion Internet, ni tous les outils du DNS Windows ne sont ajoutés. Cette version ne prétend pas reproduire intégralement DNS Manager.

Référence de conception : [Microsoft — gestion des enregistrements DNS](https://learn.microsoft.com/fr-fr/windows-server/networking/dns/manage-resource-records).

## Recette manuelle

1. Depuis le portable technicien, ouvrir DNS puis Enregistrements : zone et tableau visibles, aucun formulaire d’édition dans la liste.
2. Sélectionner une entrée, filtrer la liste puis ouvrir les propriétés de l’entrée sélectionnée ; vérifier sa cible.
3. Modifier une adresse, enregistrer, vérifier la nouvelle valeur après relecture.
4. Créer un A puis un CNAME via Nouvel enregistrement. Tester une valeur invalide : le moteur doit refuser, la fenêtre montrer l’erreur.
5. Supprimer une entrée après confirmation : sa fenêtre doit devenir indisponible. Refuser la confirmation : aucune modification.
6. Provoquer une lecture de console refusée puis reprendre : les commandes périmées doivent être bloquées puis les fenêtres valides réactivées.
7. Résoudre un nom et vérifier nom canonique, réponses, TTL et cache. Une résolution réussie ne prouve pas l’accès SMB.
8. Vérifier clavier, dimensions, défilement et contraste sur Windows. Les tests automatiques ne remplacent pas cette recette visuelle ou Packet Tracer.
