# v0.62.7 — Surveillance réseau et continuité du bureau

## Changements

Pour les entreprises de trente employés, un passage périodique traite un seul poste. Un passage sur deux privilégie la session distante active la moins récemment contrôlée ; les autres passages sélectionnent le poste le moins récemment contrôlé du parc entier. Les résultats inconnus comptent comme tentatives pour éviter de bloquer le tour sur un poste inaccessible. Aucun fast-forward automatique.

La boucle laisse une seconde entre les passages, après la fin du contrôle précédent : ce n'est pas trente pings par seconde. Une action explicite contrôle son poste cible et peut accélérer Packet Tracer. La preuve commune technicien–serveur est partagée avec son horodatage réel, y compris lors d'un contrôle d'un bureau secondaire. Les preuves de chaque client restent indépendantes.

Le bureau distingue vérification périmée, contrôle indisponible et liaison en échec. Les deux premiers affichent un bandeau sans recouvrir les applications ; un échec constaté suspend toujours les actions distantes. Les opérations serveur continuent de refuser une preuve inconnue ou périmée. Un ancien succès ne devient jamais une autorisation actuelle.

Le statut informatif du bureau suit la paire technicien–client, pas l'état global de l'impression ou des partages. L'état public contient le poste contrôlé, la durée du dernier passage, son mode et la présence du fast-forward.

## Recette réelle à effectuer dans Packet Tracer 9

1. Entreprise de trente employés : ouvrir un bureau distant et l'annuaire, passer sur un autre onglet puis revenir. Vérifier la continuité, les dates et le renouvellement du contrôle.
2. Ouvrir plusieurs sessions : vérifier que les autres postes continuent de recevoir des observations.
3. Couper réellement le câble du poste : vérifier le refus des opérations réseau après échec ou expiration ; l'ancien succès ne doit pas permettre une clôture.
4. Arrêter MCP Builder : le bureau et ses fenêtres restent présents avec un bandeau ; les opérations réseau sont refusées. Relancer le pont et lancer un contrôle explicite.
5. Passer en mode Simulation : aucun contrôle ne doit accélérer automatiquement le temps ni changer ce mode.
6. Cliquer sur vérifier : le contrôle cible le bon poste et utilise le fast-forward uniquement si explicitement demandé.

## Limites

Le pont reste séquentiel et chaque lot peut attendre ses délais de transport. Le verrou couvre désormais un poste par passage périodique, mais un contrôle isolé peut encore prendre plusieurs secondes. Aucune garantie de fraîcheur de tous les trente postes en 45 secondes : cela dépend du débit réel de Packet Tracer. Les mesures de durée servent à vérifier cette limite, sans prolonger artificiellement la validité des preuves.

Les tests automatisés couvrent la répartition, la non-famine du parc, le ciblage, le fast-forward, les statuts et la conservation du bureau. Ils ne remplacent pas la recette ci-dessus.
