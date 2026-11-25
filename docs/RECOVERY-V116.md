# Historique de récupération des sources

La première récupération a utilisé AI-PKT-LAB-v0116b.zip et sauvegardé les refontes UI/bureau dans b61b6c9.

Le dossier installé AI-PKT-LAB-v0111.rar fourni le 25 novembre 2026 complète cette récupération. Malgré son nom v111, il contient le profil v127, les sondes comparatives suivantes et les correctifs de lancement Electron. Le numéro du bureau reste 0.119.0, tel que fourni.

Les diagnostics Qt, les captures natives et les sondes sont des outils optionnels de recherche. Ils ne corrigent pas la fuite de mémoire. La capture UST a provoqué des difficultés de démarrage dans les essais précédents et ne doit pas être lancée pour un usage normal.

Le patch expérimental NETOPS_REFERENCE_CACHE n’est pas intégré : l’inventaire normal garde le chemin de lecture original. Les sessions générées, rapports, caches, dépendances installées et extraits de désassemblage ne sont pas publiés.

Validation de cette récupération : 24 tests mémoire, 5 tests de lecture exclusive, 6 tests de transport, 4 tests de sondes phase 3 et 8 tests Electron passent. Exécution Windows, Packet Tracer et rendu visuel non revérifiés.
