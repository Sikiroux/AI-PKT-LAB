# v0.28 — Postes et bureaux

## Utilisation

Dans **Postes**, le portable du technicien s’ouvre séparément. La liste des postes affiche le nom, l’utilisateur associé, l’adresse IP et le résultat du dernier contrôle pour la cible simulée. Le poste du ticket est présélectionné. Le bouton affiche « Prendre la main sur [nom] » et envoie son numéro de série au serveur. Un appareil renommé ne change pas de cible ; une autre identité est refusée avant toute ouverture.

Les PC et portables relevés dans le bon réseau Packet Tracer apparaissent après une vérification. Ceux qui n’ont pas de bureau simulé associé sont indiqués « Bureau simulé non disponible ». Cette version conserve un bureau client simulé par entreprise : elle ne simule pas encore une session distincte pour chaque PC ajouté dans Packet Tracer. L’utilisateur d’un appareil non associé n’est pas inventé.

Les applications du bureau sont présentées sous forme d’icônes avec un libellé dessous. La couche des fenêtres passe devant les icônes ; elle laisse les clics traverser les espaces vides. La barre des tâches conserve sa propre zone en bas. Agrandir, réduire et fermer restent disponibles.

## Réactivité

La lecture de `/workspace/state` ne bloque plus derrière les pings de surveillance : elle utilise un instantané pris avant les appels au pont, avec recalcul des préconditions à l’heure actuelle. Une preuve expirée n’autorise pas la prise en main. Un instantané d’une autre entreprise n’est jamais renvoyé. Aucun résultat réseau n’est fabriqué et les actions restent contrôlées dans le serveur.

Le démarrage du bureau évite une deuxième lecture immédiate du même état après le démarrage OS.js. La connexion distante affiche son attente explicitement. Les pings, la file d’attente du pont et les actions qui nécessitent le verrou peuvent encore prendre plusieurs secondes. Aucun délai réel Windows/Packet Tracer n’a été mesuré ici.

## Vérification manuelle

1. Ouvrir le portable, vérifier les icônes et lancer deux applications : la fenêtre active doit rester devant les icônes.
2. Dans Postes, vérifier le nom et l’IP de la cible puis ouvrir sa prise en main.
3. Ajouter un PC dans Packet Tracer, actualiser : il doit apparaître comme détecté, sans bureau simulé si aucun ne lui est associé.
4. Pendant une surveillance, ouvrir le portable : son chargement ne doit plus attendre tous les pings.
5. Débrancher le poste client : la session doit se fermer après le contrôle, comme auparavant.

Le placement logique de la topologie reste à traiter : les modèles lus ne donnent pas de champ de cadrage exploitable. Déplacer arbitrairement vers (1950,1950) pourrait ouvrir sur une zone vide ; il faut d’abord vérifier le cadrage avec un fichier sauvegardé dans Packet Tracer.
