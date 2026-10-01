# Règles de construction de topologies — extraites de vrais labs

Objectif : servir de garde-fou au générateur procédural (futur) et de référence pour les
gabarits écrits à la main. Chaque règle est marquée :

- **[vérifié]** : observé directement dans un vrai fichier Packet Tracer (donc une
  configuration que PT accepte et qu'un cursus officiel utilise réellement).
- **[connaissance générale, à vérifier]** : pratique standard Cisco/CCNA, mais pas
  observée dans un fichier qu'on a décodé — à confirmer avant de s'appuyer dessus pour
  une panne/un check.

Source directe : les 2 fichiers `.pka` fournis par Damien (« Troubleshooting Challenge —
Document the Network » / « — Use Documentation to Solve Issues »), décodés avec
`ptexplorer.py` et analysés (topologie, running-configs, bloc Instructions). **Aucun
fichier source tiers n'est committé dans ce dépôt** (contenu Cisco/NetAcad sous droits) —
seules ces règles et nos propres templates réécrits à partir des patterns observés.

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

- **[vérifié]** NAT overload (PAT), pas de NAT statique dans ces labs :
  - `ip nat inside` sur **chaque** interface LAN/WAN interne du routeur de bordure (une
    ligne par interface interne — donc autant de pannes possibles que d'interfaces : en
    retirer une seule casse le NAT uniquement pour ce réseau-là, pas pour les autres).
  - `ip nat outside` sur l'interface qui mène vers l'ISP.
  - `ip nat pool <nom> <début> <fin> netmask <masque>` : plage d'adresses publiques
    dédiée (pas de `ip nat inside source ... interface`, toujours un pool nommé observé
    ici).
  - `access-list <n> permit <réseau_source> <wildcard>` associée via
    `ip nat inside source list <n> pool <nom> overload`.
  - → Panne "NAT cassé" = retirer un `ip nat inside` précis (déjà confirmé comme panne
    réelle), ou vider la pool, ou retirer `overload` (non observé mais cohérent avec la
    logique).

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
