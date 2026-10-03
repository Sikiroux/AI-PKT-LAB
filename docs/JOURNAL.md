# Journal du projet pkt_lab

Ce qui a été découvert, décidé et corrigé, dans l'ordre. Sert de mémoire au projet
(et de matière pour expliquer la démarche en entretien).

## 1. Le format des fichiers Packet Tracer
- Un .pkt/.pka est du XML compressé (zlib) puis chiffré (Twofish, mode EAX).
  Découverte : axcheron/ptexplorer ; adaptation PT ≥ 7.3 : prathamps ; générateur
  de labs : AlexSvobo/tracketpacin.
- Le dépôt d'origine ne fonctionnait pas (0/16 scénarios) : dossier de modèles
  exclu par son `.gitignore`. Le fork **TeodorPetrovic/tracketpacin** les fournit
  et ajoute la génération de .pka. → choisi comme base.
- Un .pka contient trois réseaux (départ, travail, réponse), les consignes et les
  critères de correction. Appareils « invisibles » = regroupés dans un cluster
  verrouillé (`LOCKINGTREE`).

## 2. Comportements de PT 9 validés par test réel
- PT recharge la running-config du fichier et l'applique (hostname, description
  appliquée aussi à l'objet interface, IP). Il régénère la config (ajoute `no profinet`).
- IP et passerelle d'un PC injectées : prises en compte.
- Changement de module (carte Wi-Fi WMP300N à la place de la carte Ethernet) : OK.
- `POWER=false` : OK sur PC/routeur. **Un 2960 éteint ne se rallume pas** (aucun
  interrupteur, comme en vrai ; « Power Cycle Devices » ne le rallume pas).
  → panne « appareil mort » possible seulement en scénario de remplacement.
- 3650 : alimentation modulaire (AC-POWER-SUPPLY) → panne « alimentation retirée » réparable.
- Câble supprimé, interface en shutdown, pool DHCP modifié : OK.
- Configuration faite à la main puis sauvegardée par PT : relue correctement
  (fixture `tests/fixtures/mission_vlsm_damien_4sur7.pkt`).
- SVI Vlan1 + `ip default-gateway` d'un switch : stockés seulement dans la running-config.

## 3. Bugs rencontrés et corrigés
| Symptôme | Cause | Correction |
|---|---|---|
| « Physical Workspace corrupted » | arbre physique incohérent (1re version écrite de zéro) | reprise du moteur du fork |
| Étiquettes de ports fantômes | fichier de base 8.2 contenant d'anciens câbles | base vide 9.0 du fork |
| Liens mal interprétés | PT 9 référence les câbles par numéro d'ordre, pas `save-ref-id` | méthode du fork |
| PC sans IP | type de port cherché « HostCopper » au lieu de `eCopperFastEthernet` | recherche « copper » |
| Port de routeur éteint malgré `no shutdown` | le fork ignorait shutdown/no shutdown | `[pkt_lab]` dans `core.py` |
| Fichier illisible ~1 fois sur 128 | `is_legacy_format` devine sur 2 octets | décodage moderne d'abord (tag EAX) |
| Installation Windows impossible | paquet `twofish` = source C uniquement | `twofish_pure.py`, validé vs lib C |
| 28 % gratuits dans le .pka du fork | critères générés pour des lignes par défaut | principe « zéro point gratuit » |
| Points gratuits en mission | interface sans config vue comme active ; « pas de doublon » vrai sans IP | checks corrigés |
| Câble manquant compté 2 fois | check A↔B vs B↔A | normalisation (`_key`) |
| Faux « config non sauvegardée » | PT ajoute ses lignes à la running-config | comparer seulement la panne dans la startup |

## 4. Décisions
- Deux modes visés : .pkt (dépannage pur, vérif par le programme) et .pka (guidé, indices).
- Niveau 3 = 2 pannes sur 2 appareils différents = 2 tickets de 2 utilisateurs.
- Mission VLSM : si le plan de l'apprenant est valide, c'est **son** plan qui est déployé.
- Modèles par défaut proches de NetAcad : routeur 2911, switch 2960.
- LAN en 10.x, réseau d'administration en 192.168.x (jamais de chevauchement).
- Réutilisation de labs GitHub tiers : pour usage personnel, pas de redistribution.
