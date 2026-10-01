# Règles de construction de topologies — extraites de vrais labs

Objectif : servir de garde-fou au générateur procédural (futur) et de référence pour les
gabarits écrits à la main. Chaque règle est marquée :

- **[vérifié]** : observé directement dans un vrai fichier Packet Tracer (donc une
  configuration que PT accepte et qu'un cursus officiel utilise réellement).
- **[connaissance générale, à vérifier]** : pratique standard Cisco/CCNA, mais pas
  observée dans un fichier qu'on a décodé — à confirmer avant de s'appuyer dessus pour
  une panne/un check.

Sources directes :
- Les 2 fichiers `.pka` fournis par Damien (« Troubleshooting Challenge — Document the
  Network » / « — Use Documentation to Solve Issues »), décodés avec `ptexplorer.py`.
- 3 dépôts GitHub de labs CCNA suggérés par Damien, clonés temporairement (hors de ce
  dépôt, jamais committés) et plusieurs `.pkt` décodés avec `ptexplorer.py` pour
  comparaison start/solution : `CyberSphinxxx/PacketTracer-LabActivity`,
  `PPechmann/Packet-Tracer-Practice-Labs` (paires start/solution très directement
  exploitables : NAT statique/dynamique/overload, routage statique, VLAN trunking, VTP,
  STP, IPv6, EtherChannel), `learn-skillnuggets/CCNA-Packet-Tracer` (34 labs couvrant les
  6 modules du programme CCNA 200-301, exploré au niveau README seulement).

**Aucun fichier source tiers n'est committé dans ce dépôt** (contenu sous droits) — seules
ces règles et nos propres templates réécrits à partir des patterns observés.

## 1. Adressage IP

- **[vérifié]** Liens WAN point-à-point (série) toujours en `/30` (2 hôtes utiles) :
  ex. `192.168.0.0/30`, `192.168.0.4/30`, `192.168.0.8/30`, `192.168.0.12/30` — un
  sous-réseau par liaison série entre deux routeurs.
- **[vérifié]** LAN internes en `192.168.x.0/mask` avec masques variables selon le besoin
  réel (VLSM) : `/24` (standard), `/25` (128 hôtes, ex. `192.168.5.0/25` et
  `192.168.5.128/25` pour deux VLAN voisins), `/27` (32 hôtes, ex. `192.168.2.0/27` et
  `192.168.2.32/27`). Pas de gaspillage : la taille du sous-réseau correspond au nombre
  d'hôtes réellement prévu sur ce LAN.
- **[vérifié]** Adresse de la gateway = **première adresse utile** du sous-réseau LAN
  (`.1`, `.33`, `.65`, `.129`...), jamais une adresse arbitraire.
- **[vérifié]** Adressage publique (Internet/ISP) en adresses de documentation
  TEST-NET/benchmarking réservées pour les labs : `192.0.2.0/30` (lien Hub↔ISP),
  `203.0.113.0/24` (réseau "public" de l'ISP), `209.165.201.128/27` (pool NAT) — jamais de
  vraies IP publiques dans un lab.
- **[vérifié]** SVI de gestion d'un switch (`interface Vlan1`) : adresse dans le même LAN
  que les postes qu'il dessert, typiquement `.252` ou `.2` du réseau (proche de la fin ou
  du début de la plage, jamais en plein milieu).

## 2. Nommage des interfaces (routeur ISR4321 + module NIM-2T)

- **[vérifié]** `GigabitEthernet0/0/0` et `GigabitEthernet0/0/1` : interfaces LAN
  intégrées (une par LAN local direct).
- **[vérifié]** `Serial0/1/0` et `Serial0/1/1` (et `0/2/0`/`0/2/1` si le routeur a 2
  modules NIM-2T comme le routeur central "Hub") : liaisons WAN, une par lien point-à-
  point vers un autre routeur.
- **[vérifié]** Routeur-sur-un-bâton (router-on-a-stick) : l'interface physique
  (`GigabitEthernet0/0/0`) reste `no ip address`, chaque VLAN a sa propre
  sous-interface (`GigabitEthernet0/0/0.1`, `.5`, `.10`...) avec
  `encapsulation dot1Q <vlan_id> [native]` (le mot-clé `native` uniquement sur le VLAN
  natif, VLAN 1 dans l'exemple observé) puis son `ip address`.
- **[vérifié]** Les interfaces série non utilisées restent `no ip address`,
  `clock rate 2000000`, `shutdown` — jamais supprimées, juste coupées.

## 3. Switchs

- **[vérifié]** Ports vers un routeur ou un autre switch en `switchport mode trunk`
  (plusieurs trunks observés sur un même switch d'accès pour relier plusieurs
  switchs/VLANs). Ports vers un PC en `switchport mode access`.
- **[vérifié]** SVI Vlan1 + `ip default-gateway` systématiquement présents sur chaque
  switch administrable (déjà implémenté dans `builder.py::switch_mgmt_config`).

## 4. OSPF

- **[vérifié]** Un seul process OSPF par routeur, même ID sur tous les routeurs du domaine
  (`router ospf 10` dans l'exemple — l'ID est local au routeur, mais rester cohérent dans
  tout un gabarit donné).
- **[vérifié]** Une seule `area 0` dans tous les labs observés (pas de multi-area ABR) —
  cohérent avec le niveau CCNA/CCST visé par Damien. Ne pas introduire de multi-area sans
  demande explicite.
- **[vérifié]** Une ligne `network <adresse_réseau> <wildcard> area 0` **par réseau
  directement connecté** à annoncer (LAN ET liens WAN), wildcard = inverse du masque
  (`/30` → `0.0.0.3`, `/24` → `0.0.0.255`, `/25` → `0.0.0.127`, `/27` → `0.0.0.31`).
  → Panne "réseau non annoncé" = simplement une de ces lignes absente (déjà confirmé
  comme panne réelle dans le fichier "Use Documentation to Solve Issues" : LAN Factory
  192.168.4.0/24 non annoncé).
- **[vérifié]** `log-adjacency-changes` présent par défaut sur au moins un routeur
  (cosmétique, sans impact fonctionnel).
- **[connaissance générale, à vérifier]** Pas de `passive-interface` dans les fichiers
  observés — toutes les interfaces participant à OSPF annoncent aussi des hellos. Donc ne
  pas supposer que les LAN sont passifs par défaut dans nos gabarits, sauf si on choisit
  de l'ajouter nous-mêmes comme variante.
- **[vérifié]** Le routeur en bordure Internet (ISP) n'est **pas** dans le domaine OSPF :
  la jonction se fait par **route statique** (`ip route <pool_NAT> <masque>
  <next-hop-Hub>` côté ISP) + `default-information originate` côté routeur NAT (Hub) pour
  injecter une route par défaut dans OSPF vers les autres sites. Pattern classique
  "routeur de bordure hors IGP".

## 5. NAT

- **[vérifié]** `ip nat inside` sur **chaque** interface LAN/WAN interne du routeur de
  bordure (une ligne par interface interne — donc autant de pannes possibles que
  d'interfaces : en retirer une seule casse le NAT uniquement pour ce réseau-là, pas pour
  les autres), `ip nat outside` sur l'interface qui mène vers l'ISP. Commun aux 3 variantes
  ci-dessous.
- **[vérifié]** 3 variantes de traduction observées (confirmé en comparant les labs
  `Packet-Tracer-Practice-Labs/complete NAT lab-*`, un même réseau de départ avec 3
  solutions distinctes) :
  1. **NAT statique** (1 serveur exposé) :
     `ip nat inside source static <ip_locale> <ip_publique>` — une ligne par hôte exposé,
     aucun pool, aucune ACL.
  2. **NAT dynamique** (pool sans PAT, une IP publique par hôte interne, pool fini) :
     `ip nat pool <nom> <début> <fin> netmask <masque>` +
     `ip nat inside source list <n> pool <nom>` (sans `overload`) +
     `access-list <n> permit <réseau_source> <wildcard>`.
  3. **NAT overload (PAT)**, elle-même en 2 formes possibles selon le nombre d'IP
     publiques disponibles :
     - **sur l'interface de sortie** (une seule IP publique, cas le plus courant) :
       `ip nat inside source list <n> interface <interface_wan> overload` + la même ACL
       que ci-dessus. Pas de pool du tout.
     - **sur un pool** (bloc d'IP publiques à partager, cf. le lab Hub/NAT multi-sites
       §1) : `ip nat pool <nom> <début> <fin> netmask <masque>` +
       `ip nat inside source list <n> pool <nom> overload`.
  - → Panne "NAT cassé" = retirer un `ip nat inside`/`ip nat outside` précis (confirmé
    réel), vider/retirer la pool ou l'ACL, ou retirer `overload` (cohérent avec la
    logique, transforme implicitement un overload en dynamique épuisable).
- **[vérifié]** Le routeur ISP/en amont a besoin d'une route statique vers le(s) bloc(s)
  d'IP publiques utilisés côté NAT (`ip route <bloc_public> <masque> <next-hop>`) pour que
  le trafic de retour revienne — sans ça, le NAT traduit à l'aller mais rien ne revient.
  Panne possible côté ISP, pas seulement côté routeur NAT.

## 6. Mots de passe / accès (déjà géré par le mécanisme actuel de `builder.py`)

- **[vérifié]** `enable secret <niveau> <hash>` (ne jamais mettre `enable password` en
  clair dans nos gabarits si on veut rester réaliste — mais rien n'empêche un gabarit
  "débutant" avec un mot de passe simple en clair comme panne de sécurité volontaire).
- **[vérifié]** `line con 0` (parfois avec `password cisco` + `login`, parfois vide selon
  le routeur), `line vty 0 4` avec `password cisco` + `login` systématiquement.
- Rien de neuf à construire ici : ce sont de simples lignes de texte dans la liste
  `config=[...]` déjà passée à `lab.add(...)`.

## 7. Bloc Instructions natif PT (nouveau pour le projet)

- **[vérifié]** Structure exacte à produire :
  ```xml
  <ACTIVITY ELAPSED="0" ENABLED="no" VALUE="" PASS="">
   <INSTRUCTIONS>
    <PAGE translate="true"><![CDATA[<html>...</html>]]></PAGE>
   </INSTRUCTIONS>
  </ACTIVITY>
  ```
  à insérer dans l'arbre XML (absent du template vide actuel
  `templates/packettracer/emptysavefile.xml`).
- **[vérifié]** `ENABLED="no"` désactive la notation automatique native de PT (Activity
  Wizard/réseau-réponse caché) — on garde notre propre `checker.py` comme seul juge,
  cohérent avec l'architecture actuelle du projet.
- **[vérifié]** Contenu HTML observé : titre, tableau d'adressage à remplir par
  l'étudiant (colonnes Device/Interface/Type/IP/Masque/Gateway, cellules vides en
  `blank`), section "Objectives" (liste à puces), section "Background / Scenario"
  (texte libre). Gabarit réutilisable pour nos propres générations (bilingue FR/EN).

## 8. Zones verrouillées / masquées (`LOCKINGTREE`)

- Mentionné dans `docs/JOURNAL.md` (§1) pour les labs de type "découverte réseau" : des
  appareils sont regroupés dans un cluster verrouillé, invisibles/non ouvrables tant que
  l'étudiant n'a pas fait la découverte réseau attendue. Pas encore vérifié en détail dans
  nos 2 fichiers (ils ne semblent pas l'utiliser — tous les appareils y sont ouvrables).
  **À creuser séparément** avant de l'implémenter comme option de génération : trouver un
  exemple réel qui l'utilise et décoder sa structure XML exacte.

## 9. Routage statique (alternative à OSPF pour les topologies plus simples)

- **[vérifié]** Topologie en chaîne (R1—R2—R3) observée dans
  `Packet-Tracer-Practice-Labs/ipv4-static-routes` : chaque routeur a son propre LAN
  (`/24`) + des liens inter-routeurs en `/24` également ici (pas systématiquement `/30`
  comme pour OSPF — le choix dépend du lab, les deux sont valides).
- **[vérifié]** Une ligne `ip route <réseau_distant> <masque> <next-hop>` **par réseau non
  directement connecté**, next-hop = l'IP de l'interface du routeur voisin sur le lien
  partagé. Un routeur du milieu de chaîne (R2) a autant de routes statiques que de réseaux
  non-adjacents (ici 2 : vers R1 et vers R3), un routeur en bout de chaîne n'en a qu'une.
- → Pannes possibles, plus simples qu'OSPF (pas de notion de voisinage/adjacence à
  rétablir, juste une ligne de config) : route manquante, mauvais next-hop, mauvais
  réseau/masque de destination. Bon palier de difficulté intermédiaire avant d'introduire
  OSPF dans une progression pédagogique.

## 10. VLAN / router-on-a-stick — complément

- **[vérifié]** Variante plus simple que celle du §2 : sous-interfaces uniquement pour les
  VLAN réellement routés (`.10`, `.20`...), **sans** sous-interface pour le VLAN natif (1)
  quand ce VLAN n'a besoin d'aucun routage — contrairement à l'exemple du lab multi-sites
  où VLAN 1 avait sa propre sous-interface `dot1Q 1 native`. Les deux formes sont valides
  selon le besoin réel du lab.
- **[vérifié]** Port trunk vers le routeur sans restriction de VLAN
  (`switchport trunk allowed vlan ...` absent) = tous les VLAN passent par défaut.
  Ports d'accès : `switchport access vlan <id>` + `switchport mode access`.

## 11. Pistes futures identifiées (non étudiées en détail)

D'après les sommaires des 3 dépôts GitHub suggérés par Damien (lus au niveau README/liste
de fichiers, pas décodés en détail), d'autres thèmes CCNA reviennent souvent et pourraient
devenir de nouveaux types de pannes/topologies plus tard : RIP, EIGRP, STP (spanning-tree,
ex. `analyzing-STP` dans Practice-Labs), VTP, EtherChannel/LACP, port security, SSH vs
Telnet, ACL, CDP/LLDP. Aucun de ces thèmes n'a été décodé/vérifié à ce stade — à traiter au
cas par cas, avec la même méthode (décoder un vrai lab, comparer start/solution, en tirer
des règles) avant de les implémenter.

## Implications pour le générateur

- Un **gabarit multi-site (OSPF+NAT+VLAN)** peut être écrit à la main en respectant ces
  règles avec un bon niveau de confiance : la structure, le nommage et la syntaxe sont
  déjà validés par Cisco/NetAcad eux-mêmes (ce ne sont pas nos propres suppositions).
- Ce qui reste **non garanti** et devra être testé en vrai dans PT 9 avant d'être marqué
  "validé" : le fait que **notre générateur** (`core.Lab`/`ptexplorer.py`) produise un
  fichier que PT recharge correctement à cette échelle (plusieurs routeurs, sous-
  interfaces dot1Q, pool NAT, plusieurs process OSPF simultanés). Les bugs déjà rencontrés
  par le passé (cf. `JOURNAL.md`) concernaient tous l'encodage du fichier, pas la
  plausibilité de la topologie — donc le risque principal est là, pas dans le choix des
  règles ci-dessus.
