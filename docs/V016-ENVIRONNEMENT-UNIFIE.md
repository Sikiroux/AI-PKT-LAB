# Version 0.16 — tickets et environnement commun

## Parcours

1. LANCER.bat ouvre l'interface sur Environnements et postes.
2. Créer une entreprise ou choisir un environnement et Reprendre.
3. Ouvrir son réseau dans Packet Tracer ; activer MCP BUILDER et sauvegarder.
4. Tickets contient l'incident Documents partagés de cette entreprise.
5. Réparer le câble dans Packet Tracer, contrôler le réseau, ouvrir le bureau,
   puis corriger les permissions simulées. Vérifier et fermer le ticket.
6. Réseau et inventaire utilise le même fichier. Actualiser depuis PT pour voir
   les appareils. Les incidents et ajouts de PC utilisent les noms et IP actifs.
7. Avant de changer d'entreprise, sauvegarder dans Packet Tracer. Les arrivées
   automatiques sont mises en pause et les bureaux distants sont fermés.

## Sauvegardes

Chaque environnement conserve session.json (simulation web) et tickets.json
(tickets, notes, inventaire, réglages d'arrivées). Le réseau de travail est le
même pour les deux. L'ancien donnees-netops.json reste intact ; il n'est pas
converti automatiquement en entreprise, car il concernait un autre réseau.
L'ancien workspace-session/session.json est reconnu sans déplacement.

Après Enregistrer sous dans PT, associer le nouveau fichier dans Réseau et
inventaire : les deux outils utilisent alors ce même chemin et invalident les
anciennes observations. Réinitialiser l'exercice recrée son réseau et archive les
anciens tickets dans tickets-before-reset-<identifiant>.json.

## Vérifications

Le serveur vérifie chemin et identités avant les opérations réseau. Les requêtes
web portent l'identité de l'environnement pour refuser une page devenue obsolète.
La clôture du ticket Documents exige un contrôle réseau frais et la permission
simulée de lecture. Prendre en charge, notes, sévérité et chronomètre restent
utilisables. La présence d'un appareil n'est pas considérée comme une preuve de
communication. La validation des permissions reste simulée, pas un test SMB réel.

## Ce qui reste à faire

- Accueil dédié et navigation plus simple : la présente interface conserve les
  écrans existants, renommés ; elle n'est pas une refonte visuelle complète.
- Davantage de familles de tickets web ; le dossier partagé reste le scénario
  complet initial. Les noms/adresses sont procéduraux, pas toutes les causes.
- Wi-Fi dans l'entreprise générée : demande bloquée tant que l'environnement ne
  contient pas un point d'accès configuré. Les anciens tests Wi-Fi restent disponibles
  sur le réseau historique, et les labs Wi-Fi du générateur sont conservés.
- Incidents VLAN des entreprises : bloqués jusqu'à adaptation des fonctions IOS.
- Labs complets avec copie du réseau et état web ; actuellement Formation génère
  des PKT/PKA indépendants. Les réseaux indépendants de tickets historiques ne sont
  plus proposés comme source d'arrivées dans une entreprise active.
- Pannes matérielles reportées à la demande de Damien.

Tests Python et JavaScript ne prouvent pas le comportement de PT9 : cette version
nécessite un essai réel du parcours ci-dessus, notamment injection et masquage sur
un switch nommé procéduralement. Aucune opération ne doit être annoncée validée
par ces seuls tests.
