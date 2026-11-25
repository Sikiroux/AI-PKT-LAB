v119 — Test I prolongé : références conservées, cadence inchangée

Sauvegarde puis ferme Packet Tracer et NetOps. Applique la mise à jour dans ton dossier actuel.
Lance LANCER-DIAGNOSTIC-COMPLET.bat. Un seul test, sur une copie automatiquement ouverte du réseau.
10 minutes de lectures, puis 3 minutes de suivi sans lectures. Durée totale 13 à 15 minutes.
Cadence inchangée : attente d’une seconde après chaque réponse, comme les essais précédents.
Aucun ancien test A à H ni test J n’est lancé par la suite.

Le réseau, les appareils, les ports, les liens, leurs extrémités et propriétaires sont récupérés au premier cycle.
Les valeurs sont ensuite relues depuis les références conservées ; pas de nouvelles récupérations par cycle.
Le compteur objects permet de vérifier built une fois, reused ensuite, et 0 récupération instrumentée pendant les cycles suivants.
Le rapport sépare la mémoire engagée pendant la préparation et pendant les lectures suivantes, par PID.
Il calcule aussi une pente après les 30 premières secondes, sans déclarer automatiquement la fuite corrigée.
Les changements de valeurs sont comptés via une empreinte des données renvoyées.

Pour cette mesure de stabilité, laisser le réseau inchangé. Les événements ne sont pas encore ajoutés.
La bonne détection des changements de topologie devra être validée dans un essai distinct avant intégration normale.
Le contrôle de nombre d’appareils et de liens ne couvre pas un déplacement de câble à nombre constant.
Aucun succès fonctionnel sur les changements n’est déduit d’une courbe stable.
La surveillance normale conserve son fonctionnement actuel.

Garde NetOps ouvert jusqu’au téléchargement de diagnostic-complet-netops.json puis envoie-le.
Le rapport est également conservé dans web/diagnostics-ram/suite-*/diagnostic-complet.json.
Les protections de lancement sur copie et la limite de 2 Gio engagés sont conservées.
37 tests locaux ciblés réussis : exécution simulée de 600 cycles, conservation du premier événement, variation des valeurs, séparation de la mémoire et pente, routes et suite.
L’évolution réelle de mémoire doit être mesurée sous Windows dans Packet Tracer.
