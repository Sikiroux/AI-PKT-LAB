# pkt_lab — instructions pour Claude Code

## Qui, pourquoi
Projet de **Damien**, en fin de parcours NetAcad *Network Technician* (prépa CCST
Networking), départ en France pour un **TP TSSR**, puis Security+ et alternance en
cybersécurité. pkt_lab sert à **s'entraîner** : il génère des labs Packet Tracer
avec pannes cachées et tickets helpdesk réalistes, puis vérifie la réparation.

Damien est **apprenant** : explique chaque changement en français, simplement,
avec le « pourquoi ». Il détecte les erreurs (y compris les tiennes) : ne jamais
affirmer un comportement de Packet Tracer sans l'avoir vérifié ou fait tester.

## Commandes
- Lancer : `python main.py` (ou `lancer.bat`) — Python 3.10+, **aucune dépendance**
- Tests : `python tests/test_all.py` → **obligatoire avant chaque commit**, 100 % vert
- Exe Windows : `build_exe.bat` (PyInstaller)

## Architecture
| Fichier | Rôle |
|---|---|
| `main.py` | Menu CLI, dossiers `tickets/Txxxxx` (pannes) et `tickets/Mxxxxx` (missions) |
| `builder.py` | Topologies saines = surcouche de `core.Lab` (fork) + `topology_info` (état sain attendu) |
| `faults.py` | Catalogue de pannes : `fn(root, topo, rng) -> rapport {device, cause, solution, checks}` |
| `ticket.py` | Énoncés côté utilisateur (`SYMPTOMS`) : le symptôme, **jamais** la cause |
| `checker.py` | Lit le .pkt sauvegardé, évalue les `checks` : cause racine, collatéral, sauvegarde |
| `missions.py` | Tâches à réaliser (pas des pannes), ex. déployer un plan VLSM |
| `exercises.py` | Exercices papier vérifiés par calcul (sous-réseaux, VLSM, IPv6, EUI-64) |
| `twofish_pure.py` | Twofish pur Python (le paquet PyPI exige un compilateur C sous Windows) |
| `core.py`, `ptexplorer.py`, `activity.py`, `scenarios.py`, `profiles.py`, `layouts.py` | Fork TeodorPetrovic/tracketpacin (MIT). Toute modification marquée `[pkt_lab]` |

## Règles du projet (apprises à la dure, voir docs/JOURNAL.md)
1. **Règle d'or** : n'injecter que des pannes que Packet Tracer sait lui-même créer
   ET réparer depuis son interface (ex. un 2960 éteint via XML ne se rallume pas).
2. **Zéro point gratuit** : un lab vierge ou non réparé doit valoir 0. Un check ne
   doit jamais être vrai « par défaut » (ex. interface sans bloc de config = éteinte).
3. **Vérifier l'état, pas les commandes** : plusieurs solutions valides doivent être
   acceptées (ex. un PC en .3 au lieu de .2). Parser la config par bloc d'interface.
4. **Pas de dégâts collatéraux** : tout ce qui est sain au départ (`healthy_checks`)
   doit le rester ; les pannes ne touchent que leur bloc (cf. `router_wrong_ip`).
5. **Une panne observable** : si elle ne se voit que depuis un autre réseau, la
   topologie doit contenir cet autre réseau (d'où PC-ADMIN sur R1 G0/1).
6. **Énoncés** : toujours dire QUOI, COMMENT (statique/DHCP…), JUSQU'OÙ (quels
   appareils, lesquels non) et COMMENT SAVOIR QU'ON A FINI.
7. **Statut « validé »** : un mécanisme n'est validé qu'après test réel de Damien
   dans PT 9. Sinon : « à tester » dans le README + fichier de test à lui fournir.

## Ajouter une panne (procédure)
1. `faults.py` : fonction `f_xxx` + entrée `CATALOGUE` (level, theme, target, topos).
2. `ticket.py` : au moins 2 formulations dans `SYMPTOMS`.
3. `checker.py` : nouveau type de check si nécessaire (+ `healthy_checks` si état sain).
4. `python tests/test_all.py` (le test « chaque panne détectée » la couvre seul).
5. Générer un .pkt de validation pour Damien, avec le setup exact (IP, appareils).
6. README : tableau des pannes, colonne « Validée dans PT ».

## Particularités Packet Tracer 9 (vérifiées)
- .pkt/.pka = XML compressé + Twofish/EAX. PT recharge la **running-config** du XML
  et l'applique réellement (description, IP, shutdown…), et ajoute ses lignes (`no profinet`).
- Câbles : le générateur écrit FROM/TO en numéros d'ordre ; PT 9 resauvegarde en
  `save-ref-id`. Le checker lit les deux.
- IP de management d'un switch (SVI Vlan1) et `ip default-gateway` : stockées
  **uniquement** dans la running-config.
- Gateway d'un PC : `ENGINE/GATEWAY` + `PORT_GATEWAY`. Port cuivre : type `eCopperFastEthernet`.
- Étiquettes de ports : réglage PT (Options > Preferences > Always Show Port Labels).

## Feuille de route
- [ ] Validation PT en attente : SVI éteinte, masque /30, pool DHCP mauvais réseau ;
      câble droit vs croisé routeur↔PC (auto-MDIX ?)
- [ ] Demandes de service (faire évoluer un réseau sain), missions multi-tâches
- [ ] Niveaux 4-5 : leurres dans les tickets, pannes en cascade
- [ ] IPv6 dans les labs (tester d'abord les champs IPv6 des PC dans PT)
- [ ] Analyseur de .pkt quelconque → réutiliser des labs externes
- [ ] Mode documentation (cluster caché + telnet/CDP), mode .pka (indices, auto-correction)
- [ ] Audit sécurité (ports inutilisés, telnet vs SSH, port-security) → pont Security+


## Ateliers à validation manuelle (demande explicite de Damien)
- Le logiciel combine un générateur de missions Packet Tracer et un simulateur de service desk : annuaire, fichiers, DNS, parc et bureaux simulés. Packet Tracer reste la référence réseau ; les services web sont des simulations pédagogiques, pas des services Windows réels.
- Le correcteur automatique est FACULTATIF et ne doit pas limiter le catalogue.
- `workshops.py` gère 3 nouveaux gabarits et 40 ateliers ; menu 5 dans `main.py`.
- Une feuille HTML contient contexte, consignes, table, indices repliables et correction finale avec tests observables. Configurer, ajouter un appareil et appliquer une politique sont aussi des missions valides.
- `validation=manual` : `checker.check` renvoie `success=None`. Ne jamais attribuer une réussite faute de checks. Le menu autorise seulement une déclaration « vérifié manuellement » après consultation des tests.
- Les incidents en plusieurs étapes (mail, Wi-Fi, WAN Meraki) font configurer un état sain puis injecter/réparer dans PT ; ne pas les annoncer comme pannes déjà injectées.
- Ces nouveaux modèles et mutations sont **à tester dans PT 9** ; les tests Python ne prouvent pas le comportement réseau réel.
- Exécuter `python tests/test_all.py` et `python tests/test_workshops.py` avant livraison.
- Les anciens templates serveur DNS n’offrent pas tous les services. WorkshopLab préfère le Server-PT complet du catalogue, sans changer les 6 anciens gabarits.
- Ne pas élargir ce projet aux VM/Windows Server/Docker.

## Recette unifiée
- `python tests/run_tests.py` lance séparément le cœur, les ateliers, les tests web Python et chaque suite JavaScript. Cette séparation évite les collisions de modules entre la racine et `web/`.
- Python 3.10+ et Node.js sont nécessaires pour la recette complète. Un outil manquant ou une suite en échec produit un code de sortie non nul ; ce n'est jamais une validation partielle présentée comme complète.
- Les tests automatisés ne remplacent pas les vérifications réelles dans Packet Tracer 9.
