# AI-PKT-LAB / NetOps Lab — Présentation et état du projet

État documenté le **25 novembre 2026**, après récupération des sources dans `main` au commit `8e9dc7c`. Ce document sert de point d’entrée pour comprendre le projet et reprendre le développement. Il distingue les fonctionnalités présentes, les observations faites pendant les essais et les pistes encore expérimentales.

## Sommaire

1. [Objectif et noms](#1-objectif-et-noms)
2. [Fonctionnalités](#2-fonctionnalités)
3. [Fonctionnement technique](#3-fonctionnement-technique)
4. [Démarrage et utilisation](#4-démarrage-et-utilisation)
5. [Interface et expérience utilisateur](#5-interface-et-expérience-utilisateur)
6. [Problème mémoire Packet Tracer](#6-problème-mémoire-packet-tracer)
7. [Autres problèmes rencontrés](#7-autres-problèmes-rencontrés)
8. [Versions et validation](#8-versions-et-validation)
9. [Priorités de développement](#9-priorités-de-développement)
10. [Fichiers utiles et règles de reprise](#10-fichiers-utiles-et-règles-de-reprise)

## 1. Objectif et noms

Exemple de parcours : une entreprise simulée reçoit un ticket « je ne peux plus accéder au document partagé ». Le technicien consulte le contexte, contacte le demandeur, ouvre son poste, teste le réseau et les services, intervient, puis rédige son compte rendu. La résolution doit être confrontée à des vérifications, pas seulement déclarée par le joueur.

**AI-PKT-LAB** est le nom du dépôt et du projet global. Le socle initial génère des exercices et des réseaux Cisco Packet Tracer, avec pannes, missions, consignes, indices et corrections.

**NetOps Lab** est l’environnement de travail qui s’est construit sur ce socle : entreprise générée, centre de tickets, bureau technicien, postes clients, messagerie, documentation et outils d’administration.

**Packet Tracer** reste le simulateur réseau externe. NetOps lui demande certaines observations et actions par un pont communautaire. Le projet n’est pas une réimplémentation complète de Packet Tracer, Windows Server ou Active Directory.

Public visé : entraînement pratique au support informatique et à l’administration systèmes/réseaux, notamment TSSR et notions CCNA.

## 2. Fonctionnalités

### Générateur de labs

- Génération de fichiers `.pkt` et d’activités `.pka`, selon le parcours.
- Topologies et pannes procédurales : adressage, DHCP, commutation, VLAN/trunks, routage, OSPF, NAT et autres familles du catalogue.
- Choix de thèmes, difficulté, pannes et variantes reproductibles.
- Consignes, indices, feuilles compagnons et correction ; vérifications automatiques ou validation manuelle selon l’atelier.
- Exercices de sous-réseaux, VLSM et IPv6.

Le catalogue du générateur est plus large que celui des tickets aléatoires de l’entreprise : la présence d’une panne dans les labs ne signifie pas qu’elle est proposée dans les arrivées du service desk.

### Entreprise et service desk

- Création et reprise d’une entreprise avec personnes, comptes, postes et réseau associés.
- Tickets, prise en charge, suivi du temps de travail, arrivées réglables et compte rendu.
- Premier ticket au démarrage de la simulation, selon le parcours livré.
- Bureau technicien et bureaux clients distincts.
- Parc, stock, préparation et remise de postes.
- Outils pédagogiques d’annuaire, DNS, fichiers partagés, FTP, impression et applications.
- Documentation et procédures ; messagerie et échanges liés au contexte des interventions.
- Vérifications de résultat adaptées à certaines demandes : une configuration apparemment correcte ne suffit pas toujours ; un accès, une connexion ou un transfert doit être constaté.

### Limites des services simulés

Les consoles d’annuaire, de fichiers, d’impression et les postes sont des simulations pédagogiques internes. Elles ne déploient pas un véritable domaine Active Directory ni des machines Windows.

Une partie des observations réseau provient réellement de Packet Tracer. Une autre partie de l’état appartient à NetOps. Il faut conserver cette distinction dans les écrans, les preuves et les bilans.

Les identifiants de formation sont propres aux comptes et à l’entreprise concernée. Consulter les fiches/contacts et la documentation de l’entreprise ; ne pas supposer un mot de passe universel pour toutes les sessions. Les identifiants fictifs du code servent aux exercices et ne doivent jamais être réutilisés pour un service réel.

## 3. Fonctionnement technique

| Élément | Rôle |
|---|---|
| Moteur Python à la racine | Construction des labs, lecture/écriture de fichiers Packet Tracer, pannes et corrections |
| `web/tickets_app.py` | Serveur local et orchestration du portail de simulation |
| `web/sim_*.py` | Services et états pédagogiques : comptes, DNS, fichiers, parc, périphériques… |
| Pages et scripts de `web/` | Interface du service desk et des bureaux |
| `desktop/main.cjs` | Application Electron, fenêtres et cycle de vie du serveur local |
| `web/diagnostic.py` | Interactions et observations réseau via le pont |
| Pont/extension communautaire | Transmission des demandes au moteur de script de Packet Tracer |
| `web/diagnostic_payloads.py` | Code des sondes utilisées pour isoler les opérations coûteuses |
| `web/memory_diagnostic.py`, `web/memory_suite.py` | Relevés mémoire, orchestration des essais et exports |

Le chemin général est : interface → serveur Python → pont → API de Packet Tracer → réponse → mise à jour des informations dans NetOps.

Un inventaire enregistré dans un JSON est une photographie. Pour connaître un nouvel état, il faut une nouvelle observation ou un mécanisme de notification effectivement disponible. Garder une référence d’objet dans le moteur de Packet Tracer est différent : cela permet éventuellement de relire ses propriétés sans redemander cet objet. La validité de cette référence et le coût des lectures doivent être vérifiés.

## 4. Démarrage et utilisation

| Besoin | Point d’entrée |
|---|---|
| Bureau Electron | `LANCER-BUREAU.bat` |
| Portail dans le navigateur | `LANCER-WEB.bat` |
| Générateur historique | `lancer.bat` / `python main.py` |
| Diagnostic mémoire uniquement | Lanceur et protocole du diagnostic choisi |

Lire les prérequis dans [le guide du bureau](V0101-BUREAU.md) et [le guide web](../web/LIRE-MOI.md). Le dépôt complet est nécessaire : le portail réutilise le moteur et les modèles de la racine. La version Electron actuelle dépend encore de son environnement Python/Node ; elle ne doit pas être présentée comme un installateur autonome avec mises à jour automatiques finalisées.

Pour un usage normal, démarrer le bureau ou le portail, créer/reprendre l’entreprise, ouvrir le réseau correspondant et connecter le pont si le parcours le demande. Ne pas lancer les captures mémoire natives pour travailler sur des tickets.

Les sessions et réseaux générés sont des données locales. Les sauvegarder séparément avant une réinstallation ou un essai susceptible de redémarrer Packet Tracer.

## 5. Interface et expérience utilisateur

### Direction retenue

L’objectif est de travailler dans des applications crédibles, avec une organisation proche des logiciels simulés : messagerie, centre de tickets, consoles d’administration et bureau.

Les maquettes validées constituent la référence visuelle. Leur fidélité inclut les icônes, espacements, couleurs de priorité, avatars, pastilles de présence, placement du chronomètre et dernière synchronisation ; elle ne se limite pas à reprendre les grands blocs.

### Travaux présents dans les sources récupérées

- Bureau Electron à plusieurs fenêtres pour libérer l’espace occupé par le navigateur.
- Refonte de la messagerie et de la barre du bureau.
- Centre de tickets retravaillé : informations, actions et détails visuels.
- Ajustements des en-têtes, marges, menus et avatar IT.
- Intervention compacte avec compte rendu dans une modale après les difficultés de défilement.
- Travail sur la réutilisation des espaces/fenêtres plutôt que leur multiplication.

### Points à valider sur le poste réel

- Conserver l’identité bleue du bureau et une hiérarchie visuelle cohérente.
- Vérifier les petites hauteurs d’écran et l’accès aux actions sans blocage de défilement.
- Contrôler qu’une action « contacter le demandeur » retrouve le bureau existant et le contexte attendu.
- Confirmer le placement et la cohérence des éléments sur tous les onglets.
- Garder le temps de travail distinct du temps depuis la création : le chronomètre de travail démarre à la prise en charge.

La récupération des sources ne constitue pas une nouvelle validation visuelle sous Windows.

## 6. Problème mémoire Packet Tracer

### Symptôme observé

Pendant des lectures répétées par le pont, la mémoire de Packet Tracer augmente. L’inventaire, notamment les ports et liens, a produit des hausses beaucoup plus fortes que certains appels simples. Dans plusieurs essais, une partie importante de la mémoire reste allouée après l’arrêt des demandes.

Ce constat ne prouve pas une croissance infinie : il décrit les durées mesurées. Les projections horaires restent des extrapolations.

### Résultat comparatif le plus utile

Dernier essai comparatif rapporté : quatre phases séparées, environ 120 secondes de charge puis 60 secondes de suivi, avec redémarrage de Packet Tracer entre les phases et 100 opérations par cycle. Les valeurs ci-dessous sont issues du diagnostic partagé pendant l’investigation ; le rapport brut n’est pas versionné dans le dépôt.

| Opération | Opérations pendant la charge | Hausse mémoire privée engagée pendant la charge |
|---|---:|---:|
| Témoin sans appel à l’API | 11 800 itérations témoins | +4,2 Mio |
| `getDeviceCount()` | 11 900 | +2,4 Mio |
| `getDeviceAt(0)` | 11 800 | +52,7 Mio |
| `getName()` sur un appareil conservé | 11 800 | +2,5 Mio |

Interprétation : dans cet essai, redemander un objet appareil est nettement plus coûteux que compter les appareils ou lire le nom sur une référence déjà obtenue. Après soustraction du témoin, cela représente environ 4 Kio par demande de référence pour `getDeviceAt(0)`.

Cela ne démontre ni que toutes les méthodes retournant un objet ont le même coût, ni que toutes les lectures de propriétés sont sans coût. La structure exacte qui retient la mémoire n’a pas été identifiée.

### Commandes et objets concernés

Les parcours d’inventaire peuvent demander des appareils, leurs ports, leurs liens, les extrémités de ces liens et leurs propriétaires, notamment via `getDeviceAt`, `getPortAt`, `getLink` et `getOwnerDevice`.

Des appels répétés ou redondants multiplient les demandes d’objets. Une commande de haut niveau telle qu’un inspecteur de ports n’évite pas automatiquement le problème : il faut regarder les opérations API qu’elle exécute réellement.

Les sondes antérieures montraient une hausse plus importante pour les identités, puis les interfaces, puis les liens. Elles orientent l’enquête vers l’obtention et la durée de vie des références ; elles ne prouvent pas à elles seules l’emplacement de la rétention dans JavaScript, l’IPC ou Qt.

### Pistes déjà essayées

| Piste | État constaté |
|---|---|
| Espacer les inventaires | Réduit le nombre d’appels, sans démontrer une correction de la rétention |
| Effacer les logs visibles | Pas de récupération mémoire démontrée |
| Réduire la mémoire résidente | Une baisse de RAM affichée n’établit pas que les allocations privées ont été libérées |
| Garder appareils/ports en cache | Forte réduction dans certains essais ; accumulation résiduelle dans d’autres |
| Cache complet sur dix minutes | Environ +83,9 Mio après l’initialisation dans l’essai rapporté : pas de correction complète |
| Ramasse-miettes appelable depuis le script | Aucun `gc()` exposé dans l’essai concerné ; cela ne signifie pas que le moteur n’a aucun GC interne |
| `QV4_MM_AGGRESSIVE_GC=1` | Essai avec ralentissement marqué et interface peu réactive ; pas de correctif validé |
| Captures natives UST/UMDH/CDB | Difficultés de lancement et blocages pendant certains essais ; pas encore de localisation concluante |

### État du correctif

**Aucun correctif définitif de la rétention mémoire de Packet Tracer n’est validé.**

Le patch expérimental `NETOPS_REFERENCE_CACHE` n’est pas intégré dans `main`. L’inventaire normal conserve son chemin de lecture original. Les sondes et outils de recherche présents dans le dépôt sont optionnels.

La piste de travail reste : obtenir l’inventaire initial, conserver les références réutilisables, relire des propriétés ciblées et limiter les nouvelles demandes aux changements qui l’exigent. Il faut mesurer le résultat avant de l’intégrer au parcours normal.

Points de vigilance :

- Un appareil supprimé/remplacé peut rendre une référence périmée.
- L’index d’un appareil ne constitue pas une identité stable.
- Le nom peut changer ou être ambigu.
- Un nombre d’appareils/liens inchangé ne permet pas de détecter tous les remplacements ou recâblages.
- Un fichier sauvegardé ne représente pas nécessairement l’état actif tant que les modifications ne sont pas enregistrées.
- Un suivi par événements n’est une solution que si les événements nécessaires sont effectivement disponibles et fiables dans l’API utilisée.

### Prochain essai utile

Comparer à charge identique le témoin, les demandes répétées d’objets et les lectures depuis des références conservées. Mesurer séparément l’initialisation et le régime continu. Tester ensuite les changements de topologie sur une copie, en évitant de cumuler plusieurs mécanismes expérimentaux.

Pour chaque résultat, conserver : version de Packet Tracer, topologie, PID, métrique mémoire, cadence, nombre d’appels, erreurs, durée de charge et suivi après arrêt. Distinguer mémoire privée engagée et mémoire privée résidente ; ne pas additionner plusieurs processus pour comparer une valeur à la ligne d’un PID dans le Gestionnaire des tâches.

## 7. Autres problèmes rencontrés

| Problème | Travail effectué / situation |
|---|---|
| Lanceurs de diagnostic qui ouvrent puis ferment des fenêtres | Correctifs de lancement et journalisation récupérés ; double-clic et élévation Windows à revérifier |
| Fermeture Electron refusée avec « wrong token » | Compatibilité du jeton de fermeture récupérée ; confirmation sur le poste Windows nécessaire |
| Consommation d’une commande par une ancienne requête du pont | Gestion de lecture exclusive et tests de transport ajoutés |
| Erreur `record() got multiple values for keyword argument 'probe'` | Correctif présent dans les sources récupérées |
| Cache Chromium/Electron inaccessible pendant les diagnostics | Profil de diagnostic isolé et répertoire de session temporaire ajoutés |
| Interface MCP/PT peu réactive pendant les essais | Observée avec certaines instrumentations et le GC agressif ; ne pas considérer ces profils comme un mode normal |
| Compte rendu inaccessible dans la fiche ticket | Intervention compacte et saisie en modale livrées après plusieurs ajustements de défilement |

La présence d’un correctif dans le code et la réussite de ses tests ciblés ne garantissent pas à elles seules que tous les symptômes ont disparu dans l’environnement Windows de l’utilisateur.

## 8. Versions et validation

Les numéros ne sont pas alignés : le dossier reçu sous le nom `AI-PKT-LAB-v0111.rar` contient des diagnostics jusqu’au profil v127 et des ajouts suivants, alors que `desktop/package.json` indique `0.119.0`. Le README historique contient également plusieurs anciennes mentions « version actuelle ».

Pour identifier le code, utiliser en priorité le commit Git, puis le profil de diagnostic et la date du rapport.

| Commit | Contenu |
|---|---|
| `b61b6c9` | Récupération des refontes UI/bureau depuis l’archive v116b |
| `8e9dc7c` | Récupération des diagnostics et correctifs ultérieurs depuis le dossier installé |

Lors de cette récupération, **47 tests ciblés** ont passé :

- 24 tests mémoire ;
- 5 tests de lecture exclusive ;
- 6 tests de transport ;
- 4 tests de sondes phase 3 ;
- 8 tests Electron.

Ce résultat ne correspond pas à une validation complète de toute la suite du projet. Le lancement Windows, Packet Tracer réel et le rendu visuel n’ont pas été revérifiés à cette occasion.

Les rapports bruts, sessions générées, caches, dépendances installées et extraits de désassemblage n’ont pas été publiés avec la récupération.

## 9. Priorités de développement

1. **Stabiliser l’usage normal** : démarrage/fermeture fiables, réutilisation des fenêtres et tests sur Windows/PT.
2. **Réduire le coût des observations réseau** : cache expérimental mesuré, invalidation sûre et absence de régression fonctionnelle.
3. **Terminer la cohérence UI/UX** : reprendre les applications selon les maquettes, vérifier les petits écrans et les parcours complets.
4. **Renforcer la pédagogie** : documentation de l’entreprise, preuves fraîches, bilan fondé sur les résultats vérifiés et progression des scénarios.
5. **Élargir ensuite** : davantage d’incidents réseau dans le service desk, messagerie enrichie et éventuelle IA conversationnelle.

Deux pistes sont conservées pour plus tard :

- Terminal intégré fidèle aux consoles Packet Tracer PC/IOS : prompts, aide `?`, historique, pagination et sorties réelles. Le ping existant ne constitue pas encore cette console complète.
- Security simulator : extension future après consolidation du simulateur actuel.

Les conversations doivent vivre dans la messagerie du technicien ou dans un salon lié au ticket. L’ajout d’une note au dossier doit être une action explicite, pour éviter de remplir automatiquement le fil d’intervention avec toute la discussion. C’est une direction produit à vérifier au fil des évolutions.

Voir [la roadmap détaillée](ROADMAP.md) pour les chantiers et leurs limites.

## 10. Fichiers utiles et règles de reprise

| Document | Utilité |
|---|---|
| [README historique](../README.md) | Installation, catalogue et historique détaillé |
| [Roadmap](ROADMAP.md) | Chantiers UI, fonctionnalités et évolutions |
| [Récupération des sources](RECOVERY-V116.md) | Provenance, exclusions et validation |
| [Guide web](../web/LIRE-MOI.md) | Utilisation du portail |
| [Bureau Electron](V0101-BUREAU.md) | Prérequis et limites du bureau |
| [Protocole RAM](../DIAGNOSTIC-RAM-LIRE-MOI.txt) | Consignes des essais mémoire |
| [Diagnostic v127](../DIAGNOSTIC-QT-V127-LIRE-MOI.txt) | Profil expérimental concerné |
| [Contexte de développement](../CLAUDE.md) | Instructions et contexte historiques à confronter à cet état |

Pour reprendre le projet avec un autre développeur ou une autre IA, fournir ce document, le commit utilisé et les rapports pertinents. Ne pas présenter une hypothèse de rétention comme une cause prouvée, ni un outil de diagnostic comme un patch.

Mettre à jour ce document après toute validation importante : version testée, protocole, résultat et limites. Garder les données privées des entreprises et les rapports locaux hors du dépôt public.
