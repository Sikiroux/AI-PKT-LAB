v118 — Diagnostic ciblé I puis J

Sauvegarde puis ferme NetOps et Packet Tracer. Remplace les fichiers avec la mise à jour dans ton dossier actuel.
Lance LANCER-DIAGNOSTIC-COMPLET.bat. Garde NetOps ouvert et ne modifie pas les réseaux de test.
Deux nouveaux essais uniquement, un nouveau processus PT et une copie identique du réseau par essai.
Durée environ 13 à 16 minutes : 3 minutes de test puis 3 minutes de suivi pour chacun.
Le rapport diagnostic-complet-netops.json se télécharge à la fin et est aussi sauvegardé après chaque essai dans web/diagnostics-ram.

I : lecture des propriétés avec conservation du réseau, des appareils, ports, liens, extrémités et propriétaires.
Les références sont obtenues au premier cycle puis réutilisées. Les propriétés sont relues ; aucun nouveau getLink ou getOwnerDevice au fil des cycles.
J : même préparation et mêmes références gardées, puis petite réponse de télémétrie sans lecture de propriétés et sans nouvel appel à ipc.network().
F redemandait encore ipc.network() à chaque cycle : I et J conservent aussi cet objet.
Le compteur objects indique les récupérations d’objets instrumentées, pas toutes les allocations internes.

I stable et J stable : piste d’intégration du cache renforcée, stabilité longue durée restant à valider.
I augmente mais J stable : l’écart oriente vers les lectures de propriétés et/ou la fabrication/transmission de la réponse.
Les deux augmentent : une autre source d’accumulation persiste ; la simple conservation des objets ne suffit pas.
Aucune de ces observations seule ne prouve le mécanisme interne exact de Packet Tracer.

Ce sont des sondes diagnostiques sur une topologie inchangée. Aucune intégration à la surveillance normale pour le moment.
Le contrôle de nombre d’appareils/liens arrête I si ces nombres changent ; il ne détecte pas toutes les modifications à effectif constant.
Une future intégration devra gérer les changements de fichier, remplacements d’équipements, câblage, ports et références invalides.
Aucun nettoyage de mémoire forcé, aucune suppression de fichiers temporaires, aucune modification du fichier original.
Les essais déjà terminés A à H ne sont pas relancés automatiquement.
Les protections de la suite v117b sont conservées : uniquement processus créés pour le test, arrêt à 2 Gio engagés ou mesure indisponible.

35 tests locaux ciblés réussis, syntaxe JS contrôlée. Comportement natif et stabilisation mémoire à confirmer sur le PC utilisateur.
