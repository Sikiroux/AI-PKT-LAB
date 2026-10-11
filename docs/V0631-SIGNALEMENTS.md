# v0.63.1 — Persistance des incidents avant signalement

## Problème corrigé

Les entreprises de trente employés appliquaient déjà la mutation avant réception du ticket, contrairement aux anciennes petites entreprises dont les exercices s’activent à la prise en charge. Mais elles sauvegardaient la mutation avant d’enregistrer son ticket de récupération. Un arrêt entre ces opérations pouvait laisser un problème sans signalement récupérable.

Le premier état sauvegardé avec la mutation contient désormais aussi son signalement, son identifiant et son compteur. Ces données sont partagées avec le stockage canonique lorsque le poste est traité dans une vue projetée. La reprise restaure le ticket manquant depuis cet état ; elle ne réexécute pas la mutation. Les modifications ultérieures du ticket, le regroupement FTP et la clôture restent gérés par les mécanismes existants.

Les incidents concernés sont locaux aux moteurs simulés : compte, DNS simulé, applications, impression, FTP et accessoires. Ce n’est pas un protocole de transaction avec Packet Tracer. Les mutations externes nécessiteront un identifiant d’opération et une réconciliation distincts.

## Textes et chronologie

- Lecteur réseau Documents inaccessible : précise le partage distant et que les fichiers locaux restent accessibles.
- Application Documents absente : indique l’application locale manquante, sans prétendre que le serveur est en panne.
- « Depuis quand ? » : heure du signalement, avec incertitude sur une panne éventuellement antérieure. Les anciens enregistrements sans heure ne reçoivent pas une chronologie inventée.

La découverte reste immédiate dans ce moteur : application, constatation et signalement ne sont pas encore séparés par des activités ou une horloge métier. Les causes cachées restent privées ; le ticket ne contient que le symptôme et le contexte observable.

## Validation

Tests de régression : première sauvegarde d’une mutation accompagnée du ticket récupérable, échec du stockage de tickets puis récupération unique sans nouvelle mutation, chronologie ancienne/nouvelle, distinction application locale/partage distant. La recette complète couvre aussi l’isolation des clients, le regroupement FTP et les contrôles de réparation.

## Suite v0.64

Événements d’entreprise persistants, découverte par activité, impacts et regroupement causal. Incidents réseau réels à ajouter seulement après validation du socle VLAN dans PT9. Petites entreprises historiques : comportement des exercices inchangé.
