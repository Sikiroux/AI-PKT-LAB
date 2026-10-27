# v0.86 — Socle VLAN, préparation et Guide

## VLAN du réseau entreprise

Le socle segmenté des entreprises de trente postes écrivait les déclarations VLAN dans RUNNINGCONFIG/STARTUPCONFIG, mais conservait la base native VLANS du modèle Packet Tracer. Le cas observé par Damien (`Access Mode VLAN: 10 (Inactive)`) et la remise en service après création manuelle concordent avec cette omission.

Le générateur écrit désormais les VLAN nécessaires dans les deux représentations : 10/15/99 sur SW-EMP et SW-EMP2, 20 sur SW-SRV, 40 sur SW-GUEST. Les VLAN par défaut sont conservés ; l’écriture ne crée pas de doublons. Les VLAN et ports métier ne sont pas renumérotés.

Les fichiers déjà générés/sauvegardés ne sont pas modifiés automatiquement. Le correctif s’applique aux prochaines générations. Ne pas réinitialiser une entreprise pour appliquer ce changement sans accepter de perdre sa progression. Une entreprise existante réparée manuellement peut être conservée.

Les tests vérifient les structures XML et les configurations. Ils ne prouvent pas le comportement PT9 : créer une nouvelle entreprise puis vérifier show vlan brief, ports, trunks et pings dans Packet Tracer avant de qualifier ce correctif de validé en situation réelle.

## Préparation avant incidents

Une nouvelle entreprise procédurale ne reçoit plus immédiatement une panne et son premier ticket lors de son association au centre de tickets. Les réglages sont enregistrés avec preparing=true, active=false, next_at=null. Le panneau Préparer l’entreprise est visible dans le centre de tickets.

Commencer la simulation retire le statut de préparation et démarre l’horloge des arrivées avec l’intervalle configuré (cinq minutes par défaut). Ce bouton ne certifie pas le réseau et ne déclenche pas immédiatement une panne. Les demandes manuelles du centre de tickets sont refusées tant que la préparation n’est pas terminée. Aucun incident automatique ni chrono de ticket n’est créé pendant cette phase.

Une simulation démarrée puis quittée avant son premier ticket ne retourne pas en préparation. Les incidents et tickets déjà sauvegardés ne sont pas effacés. Les anciennes entreprises ayant des tickets ne sont pas converties en entreprises vierges. La politique existante de mise en pause des arrivées lors du redémarrage reste en place ; reprendre les arrivées reste explicite. Cette phase concerne les entreprises procédurales, pas les labs indépendants ni les anciens exercices historiques volontairement en panne. Elle n’interdit pas à l’utilisateur de modifier manuellement son lab ou les services.

## Guide, indices et corrections

Nouvel onglet Guide : lieux où trouver les informations, lien vers Documentation du bureau technicien, distinction fichiers locaux/partagés, rôle des consoles, méthode de diagnostic et section « Je ne peux pas prendre la main ».

Le Guide distingue le pont de l’accessibilité du poste et propose une comparaison ICMP manuelle avec la même source et la même destination. Les contrôles de VLAN sont expliqués comme pistes, pas comme prescriptions de recréer systématiquement des VLAN. Aucun test ou changement n’est déclenché par la lecture du Guide.

Le mauvais aiguillage endpoint → files est retiré : les indices poste orientent désormais vers Paramètres → Applications et Lecteur réseau, puis vers la reproduction de l’action attendue. Les autres familles conservent leurs aides spécifiques. Les corrections impression mentionnent la file pour Revenir en ligne et les propriétés → Maintenance pour le spouleur. La correction complète reste une révélation explicite tracée dans le bilan, sans réparation automatique.

Ce n’est pas une réécriture exhaustive de toutes les aides. Le Guide est une première carte des outils, pas une nouvelle base de connaissances d’entreprise générée. Les procédures plus détaillées par famille et la pertinence de chaque correction restent à enrichir avec les retours d’utilisation.

## Recette

1. Nouvelle entreprise trente postes : aucun ticket incident avant le clic, même après dépassement de la cadence.
2. Ouvrir entreprise.pkt, vérifier les VLAN des quatre switches et tester la passerelle depuis plusieurs postes. Vérifier aussi le portable technicien vers les clients et les serveurs.
3. Consulter Guide et Documentation sans déclenchement de panne.
4. Commencer la simulation : le prochain événement suit la cadence configurée. Vérifier l’apparition des incidents puis des signalements et l’absence de doublon au second clic.
5. Reprendre une sauvegarde avec incident : sa panne et son ticket doivent être conservés.
6. Ticket poste : les indices doivent proposer les contrôles du poste avant les droits/quotas du partage. Les solutions restent séparées.

Validation automatisée : 19/19 tests du cœur, 8/8 ateliers, 831/831 tests Python web et 46 suites JavaScript passent. Les tests des arrivées couvrent la création sans incident, le démarrage explicite et la reprise avant premier ticket ; ceux du réseau vérifient les bases VLAN et leur absence de doublons. Rendu navigateur et recette PT9 à effectuer.
