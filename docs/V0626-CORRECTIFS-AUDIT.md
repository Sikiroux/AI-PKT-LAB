# v0.62.6 — Correctifs issus des deux audits

- Catalogue des labs : suppression de la référence JavaScript inexistante dans labOptions.
- Dialogue réseau : fraîcheur calculée depuis la date effectivement enregistrée, avec rejet des dates futures et périmées.
- Annuaire : partage de la preuve technicien–serveur entre bureaux du même environnement, uniquement après correspondance exacte source/cible. Les preuves propres aux clients ne sont jamais fabriquées ni partagées.
- Observations : conservation séparée du dernier résultat connu, exposé en lecture seule ; les autorisations continuent d'utiliser exclusivement la preuve actuelle et sa durée de validité.
- Exceptions de contrôle et d'arrivée périodique : journalisation avec trace, au lieu d'une disparition silencieuse.

## Limites

Ce lot ne termine pas v0.62.7 : le coût des contrôles, la planification de trente postes, la présentation du dernier état connu et les délais sous Packet Tracer restent à mesurer et à corriger. Aucune durée de validité n'a été augmentée pour masquer le problème.

Aucun ping réel ni modification du réseau n'a été réalisé lors de cette livraison. Validation réelle dans Packet Tracer 9 à effectuer : catalogue des labs, changement de bureau avec annuaire ouvert, coupure du pont, puis câble réellement coupé. Une liaison passée ne prouve pas l'état actuel après coupure.
