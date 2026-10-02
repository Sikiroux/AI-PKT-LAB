# Backlog des exercices à créer — tiré de vrais labs

Objectif : lister concrètement quoi construire ensuite, avec une source réelle à
l'appui de chaque entrée (pas de pattern inventé), un niveau de confiance, et une
proposition de difficulté. Trois catégories, pas une seule — suite à la remarque
de Damien que "pannes à réparer" n'est qu'un des types d'exercices utiles :

1. **Pannes / dépannage** — topologie saine donnée, une ou plusieurs pannes
   injectées à trouver et réparer. Modèle `faults.py`/`checker.py` (existant).
2. **Construction** — topologie câblée mais non configurée, à configurer depuis
   zéro. Modèle `missions.py` (existant, pour l'instant limité au VLSM).
3. **Extension / évolution** — réseau sain existant, nouvelle exigence à ajouter
   par-dessus (ex. IPv6 sur un réseau IPv4 qui tourne déjà). **Aucun modèle
   n'existe encore pour ça** — correspond à l'item "demandes de service" déjà
   présent dans la feuille de route du README, mais jamais concrétisé.

## Méthode / sources

- Les 2 fichiers `.pka` NetAcad fournis par Damien au début (Document the
  Network / Use Documentation to Solve Issues) — déjà à l'origine de
  `docs/RULES_TOPOLOGIES.md` et du gabarit `multisite_ospf_nat`.
- `PPechmann/Packet-Tracer-Practice-Labs` — paires start/solution (VTP, STP,
  IPv4 de base, IPv6, routage statique, VLAN, NAT) : la plupart sont des
  exercices de **construction**, pas de dépannage (le fichier "start" est
  juste non configuré, pas fautif).
- `CyberSphinxxx/PacketTracer-LabActivity` — contient un lab "Troubleshoot
  EtherChannel" avec **2 fichiers** : l'activité vierge ET la version
  soumise par un vrai étudiant (`JohnLemarGonzales - ...pka`), donc un vrai
  avant/après de dépannage EtherChannel, pas une supposition.
- **`GibJaf/CCNAv7`** — dépôt contenant l'intégralité des activités Packet
  Tracer officielles des 3 cours CCNAv7 (ITN, SRWE, ENSA) avec la numérotation
  NetAcad d'origine. Utilisé pour retrouver les **10 activités officiellement
  nommées "Troubleshoot..."** (voir liste et diffs ci-dessous) — c'est la
  source la plus fiable possible : c'est le programme d'examen lui-même, pas
  une inspiration tierce.
- Tous clonés temporairement en dehors de ce dépôt, jamais committés (contenu
  sous droits) — seuls ce constat et nos propres règles entrent ici.

## Les 10 activités "Troubleshoot" officielles CCNAv7 (via `GibJaf/CCNAv7`)

Décodées (`ptexplorer.ptfile_decode`) puis diffées instantané 0 ("initial",
l'état fautif livré à l'étudiant) vs instantané 2 ("answer", la solution
cachée dans le fichier) — même méthode que pour les 2 fichiers NetAcad du
début. 6 des 10 ont été diffées pour cette session ; les 4 restantes
(`17.8.3`, `12.6.1`, `12.6.2` déjà analysées au tout début, et `13.4.5`
sans-fil hors périmètre) ne sont pas reprises ici.

| # | Activité officielle | Panne(s) réelle(s) trouvée(s) par diff | Déjà au catalogue ? |
|---|---|---|---|
| ITN 10.3.5 | Troubleshoot Default Gateway Issues | Switch : `ip default-gateway` absent sur le SVI de management | ✅ Oui (pattern switch gateway) |
| ITN 17.7.7 | Troubleshoot Connectivity Issues | Interface routeur en `shutdown`. (Le reste du diff — `ip cef`/`no ip cef`, `license udi ... sn ...`, mot de passe type 7, formulation du banner — est du bruit : numéro de série et hash de mot de passe diffèrent naturellement entre 2 exports du même device, pas une vraie panne à reproduire.) | ✅ Oui (`interface_shutdown`) |
| SRWE 4.4.8 | Troubleshoot Inter-VLAN Routing | Routeur bâton (router-on-a-stick) : **VLAN ID d'encapsulation dot1Q interverti entre 2 sous-interfaces** (10↔30) + une sous-interface en `shutdown` | ❌ **Nouveau, confirmé officiel** — nécessite un gabarit avec sous-interfaces VLAN (pas encore dans `builder.py`) |
| SRWE 6.3.4 | Troubleshoot EtherChannel | Port membre du bundle en `shutdown` (variante plus simple que le mode PAgP/LACP déjà identifié via la soumission étudiante) | ❌ À faire (gabarit EtherChannel, voir aussi variante mode/channel-group) |
| SRWE 16.3.1 | Troubleshoot Static and Default Routes | R1 : route par défaut IPv4 manquante. R3 : route statique IPv6 avec **mauvais next-hop** (adresse du voisin au lieu d'une interface de sortie point-à-point valide) | ❌ À faire — confirme `RULES_TOPOLOGIES.md` §9, suffisant pour coder |
| ENSA 12.5.13 | Troubleshoot Enterprise Networks | Challenge final multi-pannes (voir détail ci-dessous) — **8 pannes indépendantes réparties sur 6 devices**, exactement le type de gros "examen blanc" visé par le projet | Mélange de nouveau et déjà fait, voir détail |

### Détail du challenge final 12.5.13 (le plus riche — à utiliser comme modèle de "gros lab")

| Device | Panne réelle |
|---|---|
| Internet-Router / R2 (lien d'interco) | **Masque de sous-réseau incompatible entre les 2 bouts d'un même lien** (`/30` d'un côté, `/27` de l'autre) — nouvelle variante du `wan_wrong_ip` déjà fait, mais sur le masque plutôt que l'IP |
| R1 | `ip ospf cost` erroné sur une interface — manipulation du choix de chemin OSPF, pas juste une adjacence cassée. **Nouveau** |
| R2 | Idem coût OSPF + `passive-interface` posée sur la mauvaise interface |
| R3 | `passive-interface` posée sur l'interface physique au lieu de la bonne sous-interface — **nouveau, variante OSPF/VLAN combinée** |
| S1 | `switchport port-security` + `mac-address sticky` absents sur un port d'accès — **nouveau, confirme la piste "port security" déjà notée comme non vérifiée** |
| S2 | `switchport nonegotiate` absent — négociation DTP non désactivée sur un trunk. **Nouveau** |
| S4 | **`spanning-tree vlan 1-1005 priority 28672` absent** — élection de root bridge non maîtrisée. **Confirme enfin un vrai cas STP officiel** (jusqu'ici aucun exemple de panne STP n'avait été trouvé, seulement un lab d'observation sans panne — voir `docs/TAXONOMIE_PANNES_RESEAU.md` §2) |

### Mise à jour de priorité suite à ces découvertes

Ces 10 fichiers officiels étant la source la plus fiable possible (le
programme d'examen CCNA lui-même, pas une inspiration tierce), ils
remplacent/renforcent les priorités du §Priorités de
`docs/TAXONOMIE_PANNES_RESEAU.md`. Nouvel ordre recommandé :

1. ✅ **Fait** — **Route par défaut : mauvais next-hop** (`default_route_wrong_nexthop`, sur `multisite_ospf_nat`/R-EDGE) — variante simplifiée de 16.3.1 (sur la route par défaut existante vers l'ISP plutôt qu'une nouvelle chaîne de routeurs statiques, pour éviter un gabarit de plus).
2. ✅ **Fait** — **STP root bridge priority manquante** (`stp_root_priority_missing`) — a nécessité un nouveau gabarit dédié `switched_redundant` (3 switchs en triangle S1/S2/S3, boucle L2, pas de routeur) puisqu'aucune topologie existante n'avait de lien redondant entre switchs.
3. **VLAN ID interverti sur routeur bâton** (4.4.8) — nécessite d'abord le gabarit router-on-a-stick (déjà prévu dans `RULES_TOPOLOGIES.md` §10), mais c'est maintenant confirmé officiellement, pas juste un pattern générique.
4. **Masque incompatible sur un lien d'interco** (12.5.13) — variante simple à ajouter à côté de `wan_wrong_ip` existant, réutilise le gabarit multi-sites tel quel.
5. **OSPF cost / passive-interface mal posé** (12.5.13) — pannes de manipulation de chemin, plus subtiles (le réseau reste joignable mais pas par le bon chemin), bon niveau 3.
6. **Port security absent** / **DTP nonegotiate absent** (12.5.13) — les deux confirment des pistes déjà notées "non vérifiées", maintenant confirmées par une source officielle.
7. EtherChannel (port shutdown dans le bundle, ou mode/channel-group incompatible côté soumission étudiante), NAT statique/dynamique, VLAN access port générique — inchangé par rapport à la liste précédente.

---

## 1. Pannes / dépannage (`faults.py` / `checker.py`)

| Thème | Panne | Source | Niveau proposé | Statut |
|---|---|---|---|---|
| Adressage | Mauvaise IP/masque/passerelle PC | Pattern générique CCNA | 1-2 | ✅ Fait |
| Câblage | Câble débranché | Pattern générique | 1 | ✅ Fait |
| Matériel | PC/équipement éteint | Pattern générique | 1 | ✅ Fait |
| Routeur | Interface en shutdown | Pattern générique | 1 | ✅ Fait |
| Routeur | Mauvaise IP sur une interface | Pattern générique | 2 | ✅ Fait |
| DHCP | Mauvais pool/passerelle distribuée | Pattern générique | 2 | ✅ Fait |
| Switch | SVI/passerelle de management absente | Pattern générique | 1-2 | ✅ Fait |
| OSPF | Ligne `network` manquante | **Confirmé** : solve_issues.xml (LAN Factory non annoncé) | **1** (correctif trivial une fois localisé — revu à la baisse suite à retour de Damien) | ✅ Fait |
| Routeur (multi-site) | IP erronée sur un lien WAN, décalée au `/30` voisin | **Confirmé** : solve_issues.xml (Branch-2) | 2 | ✅ Fait |
| NAT | `ip nat inside` absent sur une interface | **Confirmé** : solve_issues.xml (Hub) + Practice-Labs (3 variantes) | 2 | ✅ Fait |
| NAT | Variante statique : mauvaise correspondance `ip nat inside source static` | **Confirmé** : Practice-Labs (NAT static) | 2 | À faire |
| NAT | Variante dynamique : pool épuisé/mauvaise ACL | **Confirmé** : Practice-Labs (NAT dynamic) | 2 | À faire |
| **EtherChannel** | Un port du bundle resté en `switchport mode access` au lieu de `trunk` | **Confirmé** : vraie soumission étudiante (EtherChannel) | 2 | À faire |
| **EtherChannel** | Mode de négociation incompatible (`desirable`/PAgP vs `active`/LACP) | **Confirmé** : vraie soumission étudiante | 2 | À faire |
| **EtherChannel** | `channel-group` différent entre les 2 extrémités du bundle | **Confirmé** : vraie soumission étudiante | 2 | À faire |
| Routage statique | Route par défaut : mauvais next-hop | **Confirmé officiel** : CCNAv7 SRWE 16.3.1 (voir ci-dessous) | 2 | ✅ Fait (`default_route_wrong_nexthop`) |
| VLAN | Port d'accès sur le mauvais VLAN / port oublié en trunk | Pattern générique CCNA, pas encore vu de panne précise dans un vrai lab (seulement des exercices de construction) | 1-2 | À vérifier avant de coder |
| STP | Priorité root bridge absente | **Confirmé officiel** : CCNAv7 ENSA 12.5.13 (voir ci-dessous) — le lab "analyzing-STP" trouvé plus tôt n'avait aucune différence de config (exercice d'observation, pas une panne), mais 12.5.13 en a une vraie | 2 | ✅ Fait (`stp_root_priority_missing`, nouveau gabarit `switched_redundant`) |

## 2. Construction (`missions.py`, modèle à étendre au-delà du VLSM)

| Exercice | Source | Statut |
|---|---|---|
| Plan VLSM puis déploiement | Pattern générique, déjà testé en vrai PT | ✅ Fait |
| Adressage IPv4 de base sur un routeur (interfaces + descriptions, à partir d'un routeur totalement vierge) | **Confirmé** : Practice-Labs (basic-IPv4-Configuration) | À faire |
| Mise en place de trunks + VTP entre plusieurs switchs (depuis des ports tous en access) | **Confirmé** : Practice-Labs (VTP-configuration) | À faire |
| Monter un EtherChannel (LACP ou PAgP) depuis zéro entre 2 switchs | Variante "construction" du même sujet qu'EtherChannel ci-dessus | À faire |

## 3. Extension / évolution (nouveau modèle à créer)

| Exercice | Source | Remarque |
|---|---|---|
| Ajouter IPv6 par-dessus un réseau IPv4 déjà fonctionnel (`ipv6 unicast-routing`, adresses `/64`, route IPv6 statique) | **Confirmé** : Practice-Labs (ipv6-configuration) — le routeur a déjà tout son IPv4 opérationnel dans le fichier "start", seul l'IPv6 est à ajouter | Premier cas d'usage concret et déjà vérifié pour ce modèle encore inexistant — bon point de départ |
| Ajouter un nouveau site/VLAN à une topologie multi-sites existante | Pas encore de source réelle précise | Correspond à l'item déjà présent dans la feuille de route ("demandes de service") |

## Pistes non vérifiées (citées dans les dépôts explorés, jamais décodées)

ACL, port security, QoS, FHRP, SNMP, NTP/syslog, CDP/LLDP. À traiter avec la
même méthode (trouver un vrai avant/après, pas deviner) avant d'ajouter une
ligne au tableau ci-dessus.

## Recalibrage de niveau déjà appliqué

Suite à la remarque de Damien (le correctif OSPF d'une ligne lui a semblé plus
simple dans le vrai lab NetAcad qu'il ne l'a vécu dans notre version) :
`ospf_network_missing` passe de niveau 2 à **niveau 1** dans `faults.py`. Les
2 autres pannes multi-sites (`wan_wrong_ip`, `nat_inside_missing`) restent au
niveau 2 (diagnostic plus impliqué : comparer des sous-réseaux entre 2
routeurs, ou comprendre le NAT).
