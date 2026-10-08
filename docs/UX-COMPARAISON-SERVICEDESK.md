# Comparaison et priorités UI/UX — 8 octobre 2026

Comparaison des fonctionnalités documentées publiquement par ServiceDesk Simulator avec le code local v0.31. Aucun test de leur application connectée ni mesure comparative de latence n’a été effectué.

## Écarts prioritaires

1. Ticket et outil côte à côte : leur écran partagé conserve le ticket pendant l’intervention. Notre séparation Tickets/Postes oblige encore à naviguer. Prévoir deux panneaux sur grand écran et deux vues alternables sur petit écran, sans dupliquer les sessions.
2. Bureau et appareils : leur bureau présente explorateur, paramètres, gestionnaire des tâches, observateur d’événements, applications et outils de réparation. Notre OS.js fournit des fenêtres et des applications pédagogiques mais les interfaces restent essentiellement des formulaires. Un seul bureau client simulé par entreprise est associé ; les appareils relevés seuls ne disposent pas chacun d’un état simulé.
3. Documentation : leur base de connaissances contient les politiques, procédures et accès de l’entreprise. Générer chez nous cette documentation depuis la même seed et le même modèle que les équipements, comptes et services. Les indices restent séparés de la documentation professionnelle.
4. Relation client : leurs échanges, appels et messagerie occupent une place importante. Nos questions prédéfinies pourraient devenir des dialogues à embranchements, avec confirmation du rétablissement et informations partielles cohérentes avec le moteur. Pas besoin de LLM pour ce premier bloc.
5. Parc : aller au-delà de l’inventaire observé : propriétaire, localisation, état, stock, attribution et remplacement. Ne pas annoncer ces opérations comme disponibles avant leur réalisation.
6. Formation : ajouter un bilan par compétence et un historique du diagnostic. Un succès de contrôle technique ne suffit pas à mesurer la qualité du diagnostic ou du compte rendu.

## Services et fonctions à développer ensuite

Messagerie (quota, règles, envoi/réception), quarantaine et expéditeurs bloqués ; logiciels, installation et réparation ; événements et processus simulés ; vérification d’identité et escalade. Les moteurs actuels annuaire, fichiers, DNS, impression et FTP restent des bases à enrichir, pas à remplacer.

## À conserver

Packet Tracer comme moteur réseau, observations avec statut inconnu/périmé, sessions reproductibles par seed, génération PKT/PKA et feuille HTML autonome, fonctionnement local. Les outils web doivent lire ces états plutôt que fabriquer des succès.

## Ordre de travail proposé

A. Maquette puis espace Ticket/Outil et navigation cohérente.
B. Bureau multi-postes et applications visuellement adaptées aux tâches.
C. Documentation procédurale et dialogue client.
D. Logiciels, événements, mail et gestion du matériel.
E. Bilans pédagogiques et progression.

## Sources officielles consultées

- https://servicedesk-simulator.com/help/articles/open-a-tool-beside-your-ticket
- https://servicedesk-simulator.com/course/remote-desktop
- https://servicedesk-simulator.com/help/articles/documentation
- https://servicedesk-simulator.com/help/articles/choose-which-tickets-land-in-your-queue
- https://servicedesk-simulator.com/help/articles/preferences
- https://servicedesk-simulator.com/help
