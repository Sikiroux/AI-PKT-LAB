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
- Tous clonés temporairement en dehors de ce dépôt, jamais committés (contenu
  sous droits) — seuls ce constat et nos propres règles entrent ici.

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
| Routage statique | Route manquante / mauvais next-hop (chaîne de routeurs) | **Confirmé** : Practice-Labs (ipv4-static-routes), règles déjà dans RULES_TOPOLOGIES.md §9 | 2 (plus simple qu'OSPF : pas d'adjacence à rétablir) | À faire |
| VLAN | Port d'accès sur le mauvais VLAN / port oublié en trunk | Pattern générique CCNA, pas encore vu de panne précise dans un vrai lab (seulement des exercices de construction) | 1-2 | À vérifier avant de coder |
| STP | Rôle/priorité incohérent | ⚠️ Le lab "analyzing-STP" trouvé n'a **aucune** différence de config start/solution — c'est un exercice d'observation (`show spanning-tree`), pas une panne corrigeable. Ne pas l'ajouter ici tant qu'un vrai exemple de panne STP n'est pas trouvé. | — | À rechercher, pas encore un bon candidat |

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
