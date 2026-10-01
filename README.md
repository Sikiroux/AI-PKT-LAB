# pkt_lab — Simulateur de tickets helpdesk sur Packet Tracer

Génère des labs Packet Tracer avec une panne cachée, un ticket utilisateur
réaliste, puis vérifie ta réparation. Propose aussi des missions (déployer un
plan d'adressage) et des exercices papier vérifiés par calcul.

> Projet personnel d'entraînement (TSSR / CCST Networking), développé avec
> l'assistance d'une IA (Claude), testé et validé dans Packet Tracer 9.
> Voir `docs/JOURNAL.md` pour la démarche, les découvertes et les bugs résolus.

## Démarrage

**Option A — sans rien installer de plus** (Python 3.10+ requis) : double-clic sur `lancer.bat`.

**Option B — un vrai .exe** : double-clic sur `build_exe.bat` (une seule fois).
L'exécutable apparaît dans `dist\pkt_lab.exe`. Copie-le où tu veux : les
tickets seront créés dans un dossier `tickets` à côté de lui.

Aucune dépendance à installer : le chiffrement des fichiers Packet Tracer
(Twofish) est réimplémenté en pur Python (`twofish_pure.py`).

Réglage Packet Tracer conseillé : Options > Preferences > Interface >
« Always Show Port Labels in Logical Workspace ».

## Utilisation

1. **Nouveau ticket** : surprise, par thème, ou panne précise ; difficulté 1 à 3
   (niveau 3 = deux pannes simultanées sur des appareils différents, donc deux
   tickets de deux utilisateurs, et un score partiel à la validation).
   Le lab s'ouvre dans Packet Tracer.
2. Tu dépannes dans PT, puis **Ctrl+S** (sauvegarde sur le même fichier).
3. **Valider un ticket** : verdict, avec
   - la cause racine (réparée ou non),
   - les dégâts collatéraux (ce que tu as cassé en réparant),
   - un avertissement si la réparation n'est pas sauvegardée sur l'équipement
     (`copy running-config startup-config`).
   En cas d'échec : retenter, indice (appareil, puis thème), ou abandonner.
4. **Historique** : tickets, tentatives, indices utilisés, taux de réussite des exercices papier.
5. **Exercices papier** (sans Packet Tracer, vérifiés par calcul) : informations de
   sous-réseau, plan d'adressage VLSM (toute réponse valide acceptée, gaspillage
   signalé), IPv6 abréger/développer, calcul EUI-64. Corrigé détaillé en cas d'erreur.
6. **Plan VLSM puis mise en place** : tu conçois le plan de 3 services, puis tu le
   déploies dans Packet Tracer (R1 + 3 switchs + 6 PC câblés, rien de configuré).
   Plan valide → c'est TON plan qui est vérifié ; sinon le corrigé. La mission se
   valide depuis « Valider un ticket », tâche par tâche.

Ne pas ouvrir `tickets/Txxxxx/.solution.json` : c'est la correction.

## Architecture

| Fichier | Rôle |
|---|---|
| `main.py` | Menu, orchestration, dossiers de tickets |
| `builder.py` | Topologies saines (surcouche de `core.Lab` du fork) |
| `faults.py` | Catalogue de pannes, injection dans le XML |
| `ticket.py` | Énoncé côté utilisateur (symptôme, jamais la cause) |
| `checker.py` | Vérification cause racine (par panne, score partiel) + collatéral + sauvegarde |
| `exercises.py` | Exercices papier : sous-réseaux, VLSM, IPv6, EUI-64 |
| `missions.py` | Missions (tâches à réaliser) : déploiement d'un plan VLSM |
| `twofish_pure.py` | Chiffrement Twofish sans compilateur |
| `core.py`, `activity.py`, `scenarios.py`, `profiles.py`, `layouts.py`, `ptexplorer.py` | Fork TeodorPetrovic/tracketpacin (modifications marquées `[pkt_lab]`) |
| `templates/packettracer/catalogue_source.xml` | 74 appareils (catalogue PTBuilder) |

### Modifications apportées au fork
- `core.py` : `shutdown` / `no shutdown` appliqués aux ports (le fork les ignorait).
- `ptexplorer.py` : Twofish pur Python en priorité ; correctif de la détection du
  format (le fork se trompait ~1 fois sur 128 et rendait le fichier illisible).

## Contenu actuel

Topologies : `simple_lan` (R1 2911 → S1 2960 → 2 PC en statique),
`dhcp_lan` (R1 serveur DHCP → S1 → 3 PC en DHCP). Dans les deux : S1 est
administrable (SVI Vlan1 en .2 + ip default-gateway), et un poste PC-ADMIN
(service informatique, supervision) est relié à R1 G0/1 dans un réseau
192.168.x.0/24 à part : il rend visibles les pannes qui ne se voient que depuis
un autre réseau.

| Panne | Niveau | Thème | Validée dans PT |
|---|---|---|---|
| Mauvaise passerelle PC | 1 | adressage | ✅ (mécanisme) |
| Mauvaise IP PC | 1 | adressage | ✅ (mécanisme) |
| PC éteint | 1 | matériel | ✅ (mécanisme) |
| Câble débranché | 1 | câblage | ✅ |
| Interface routeur en shutdown | 1 | routeur | ✅ |
| Masque /30 sur un PC | 2 | adressage | à tester |
| Mauvaise IP routeur | 2 | routeur | ✅ (mécanisme) |
| DHCP : mauvaise passerelle distribuée | 2 | dhcp | ✅ |
| DHCP : pool sur le mauvais réseau | 2 | dhcp | à tester |
| Switch : SVI Vlan1 éteinte | 1 | switch | ✅ |
| Switch : ip default-gateway absente | 2 | switch | ✅ |

## Développement
- Tests : `python tests/test_all.py` (avant chaque commit)
- Contexte pour Claude Code : `CLAUDE.md` ; historique : `docs/JOURNAL.md`

## Licence
MIT (voir `LICENSE`). Réutilise du code MIT de tracketpacin et ptexplorer :
voir `THIRD_PARTY_NOTICES.md`.

## Feuille de route
- Niveaux 4 et 5 : leurres dans les tickets, pannes en cascade.
- Demandes de service (faire évoluer un réseau sain) et missions multi-tâches.
- Exercices papier : tableau d'adressage d'une topologie, analyse de sorties « show ».
- Import des labs GitHub (analyseur de .pkt quelconque) ; IPv6 dans les labs ; audit sécurité.
- Topologies : VLAN, routage inter-VLAN, routage statique, 2 sites.
- Mode documentation/exploration (appareils cachés dans un cluster, telnet/CDP).
- Mode .pka (consignes dans PT, indices, auto-correction ; corriger les 28 % gratuits).
- Choix de la plage d'adressage (10/8, 172.16/12, 192.168/16) ; DNS interne.
