# v0.110 — Hauteur de la fiche ticket

Le correctif v109 activait le défilement mais la règle historique `#tickets .ticket-body { align-items:start }` laissait la colonne centrale prendre sa hauteur naturelle. La ligne de grille était contrainte, pas son enfant. La v110 impose l’étirement de cette colonne dans la ligne et sa hauteur maximale à 100 %. Le défilement central de v109 est conservé. La feuille de style principale possède une version dans son URL pour éviter la réutilisation d’une ancienne feuille en cache.

Trois suites JavaScript ciblées passent (onglets, centre, résolution). Elles contrôlent les interactions, pas le calcul de mise en page du navigateur. Rendu Electron Windows non vérifié ici.

Fermer le logiciel avant d’extraire le patch dans le dossier contenant LANCER-BUREAU.bat. Le patch contient les règles cumulées de v109 et v110.
