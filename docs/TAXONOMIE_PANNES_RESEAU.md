# Taxonomie des pannes réseau réelles — au-delà des labs décodés

Objectif : lister les catégories de pannes qu'un **vrai technicien réseau**
rencontre (pas seulement ce qu'on a trouvé dans des labs NetAcad/GitHub),
en s'appuyant sur des référentiels reconnus plutôt que sur des suppositions :
le programme officiel CompTIA Network+ (domaine 5.0 "Network
Troubleshooting") et des retours de terrain publiés (Fluke Networks,
éditeurs d'outils réseau). Sert de complément à `docs/BACKLOG_EXERCICES.md`
(qui liste ce qui est confirmé par un vrai lab décodé) — ici, on part plutôt
du métier pour voir ce qu'il manque dans notre catalogue.

Chaque entrée précise si c'est **simulable dans Packet Tracer** (condition
nécessaire pour en faire un lab pkt_lab) et son statut dans notre catalogue.

## Sources

- CompTIA Network+ N10-009, domaine 5.0 (24 % de l'examen) : méthodologie de
  dépannage (5.1), câblage/interface physique (5.2), services réseau (5.3),
  performance (5.4), outils (5.5).
- Fluke Networks, "The top 10 problems network technicians encounter"
  (retour terrain, pas un référentiel d'examen).
- Recherches complémentaires ciblées (sans-fil, sécurité/ACL/VPN) pour
  couvrir les domaines pas assez détaillés par les deux sources précédentes.

## 1. Couche physique / câblage (CompTIA 5.2, Fluke #1, #8)

| Panne réelle | Simulable en PT ? | Statut chez nous |
|---|---|---|
| Câble débranché / port mort ("dead drop", #1 Fluke) | ✅ | ✅ Fait (`cable_missing`) |
| Mauvaise terminaison de câble | ❌ (PT ne modélise pas le câblage physique à ce niveau) | — |
| TX/RX inversés (câble croisé vs droit au mauvais endroit) | ✅ (PT distingue type de câble et ports) | Partiellement — mentionné dans les patterns critiques du projet (auto-MDIX), pas encore une panne dédiée |
| **Duplex mismatch** (chaque bout négocie un duplex différent → erreurs CRC, lenteur) | ✅ (réglage `duplex`/`speed` par interface) | ❌ Pas dans le catalogue — **bon candidat simple, nouveau** |
| Force du signal / atténuation | ❌ (pas de notion d'affaiblissement physique dans PT) | — |

## 2. Commutation / VLAN / STP (CompTIA 5.3 "switching issues", Fluke #4)

| Panne réelle | Simulable en PT ? | Statut |
|---|---|---|
| **Mauvaise affectation de VLAN** sur un port d'accès (#4 du top 10 Fluke, cité explicitement par CompTIA) | ✅ | ❌ Pas encore codé — déjà noté comme piste dans le backlog, **confirmé officiellement maintenant, priorité à remonter** |
| Boucle réseau / mauvaise élection de root bridge STP / rôles-états de port incohérents | ✅ (PT simule STP) | ❌ Le seul lab STP qu'on a décodé était un exercice d'observation sans panne — **à construire nous-mêmes** en s'appuyant sur les conventions CompTIA (priorité de bridge erronée, port en blocking qui ne devrait pas l'être) |
| EtherChannel (trunk/access incohérent, négociation PAgP/LACP, channel-group différent) | ✅ (déjà confirmé par un vrai avant/après étudiant) | ❌ Pas encore codé (voir `BACKLOG_EXERCICES.md`) |
| ACL mal appliquée sur un port/VLAN | ✅ | ❌ |

## 3. Adressage / Routage (CompTIA 5.3, Fluke #2)

| Panne réelle | Simulable en PT ? | Statut |
|---|---|---|
| Mauvais masque de sous-réseau | ✅ | ✅ Fait (`pc_wrong_mask`) |
| Mauvaise passerelle par défaut | ✅ | ✅ Fait (`pc_wrong_gateway`, `dhcp_wrong_default_router`) |
| **Adresse IP dupliquée** (conflit entre 2 appareils) | ✅ (PT détecte et affiche un conflit d'IP) | ❌ Pas dans le catalogue — **nouveau, simple à injecter (donner la même IP qu'un autre poste), symptôme réaliste ("mon PC perd la connexion par intermittence")** |
| **Épuisement du pool DHCP** (plus d'adresse disponible, différent de "mauvais pool" déjà fait) | ✅ (réduire la plage `ip dhcp pool`/`network`) | ❌ Nouveau, variante de ce qu'on a déjà sur le DHCP |
| Mauvaise sélection de route / route manquante | ✅ | Règles posées (`RULES_TOPOLOGIES.md` §9), pas codé |
| Table de routage incorrecte (OSPF) | ✅ | ✅ Fait (`ospf_network_missing`) |

## 4. Services réseau (Fluke #3, #9)

| Panne réelle | Simulable en PT ? | Statut |
|---|---|---|
| **Problème DNS** ("Can't connect to the server" #3, "DNS problems" #9 — 2 des 10 pannes les plus citées) | ✅ (PT a un vrai serveur DNS simulable, déjà présent dans notre topologie multi-sites via le service DNS) | ❌ **Absent de notre catalogue alors que c'est un des symptômes les plus fréquents en vrai** — mauvaise entrée DNS sur un poste, ou enregistrement DNS incorrect côté serveur |
| NTP (désynchronisation d'horloge → échecs d'authentification, certificats "expirés") | ✅ (IOS supporte `ntp server`) | ❌ Pas prioritaire pour l'instant (notion plus avancée, peu enseignée en CCNA niveau 1) |

## 5. Performance (CompTIA 5.4)

Bande passante, latence, gigue, congestion, perte de paquets : ce sont des
**mesures continues**, pas des lignes de config à retirer — difficiles à
injecter comme "panne discrète" détectable par diff de config. Le seul
candidat concret et simulable de cette catégorie est le **duplex mismatch**
(déjà listé en §1), qui cause justement ce genre de symptôme de performance
en vrai. Le reste (latence/gigue/congestion) reste hors de portée du modèle
actuel de pkt_lab (pas de simulation de trafic réel/charge dans PT au niveau
où on travaille) — à ne pas essayer de forcer dans ce format.

## 6. Sans-fil (hors périmètre actuel)

SSID mal configuré, interférence de canal, échec d'authentification WPA :
PT simule le Wi-Fi (routeurs/points d'accès/cartes sans fil), donc
techniquement faisable. **Mais hors du périmètre actuel du projet** (centré
LAN filaire/routage/NAT pour l'instant, jamais évoqué par Damien comme
priorité) — à garder en tête seulement si le projet s'oriente vers le
Wi-Fi plus tard.

## 7. Sécurité (ACL/pare-feu/VPN)

| Panne réelle | Simulable en PT ? | Statut |
|---|---|---|
| ACL : règle "permit any" trop large, mauvais ordre des règles, deny implicite oublié, mauvais port/protocole visé | ✅ (ACL standard/étendues supportées) | ❌ Déjà dans les "pistes non vérifiées" du backlog, confirmé maintenant par un référentiel officiel |
| Port security (violation, sticky MAC) | ✅ | ❌ Déjà identifié comme piste |
| VPN/IPsec (échec phase 1/2, clé pré-partagée, règle de pare-feu qui bloque le trafic VPN) | ⚠️ à vérifier — PT simule du site-à-site IPsec mais c'est avancé et peu robuste à configurer même pour un humain ; risque élevé de reproduire le genre de problème qu'on a eu avec le format `.pka` (fonctionnalité PT mal documentée) | Pas prioritaire, à tester prudemment avant de s'engager dessus |

## Priorités recommandées (candidats simples, confirmés, non encore codés)

Dans l'ordre où je les coderais, du plus simple/sûr au plus gros morceau :
1. **Duplex mismatch** — une ligne de config (`duplex half`/`full`), symptôme réaliste (lenteur/erreurs), très simulable.
2. **IP dupliquée** — déjà notre mécanisme `f_pc_wrong_ip` à adapter (au lieu de sortir du réseau, donner l'IP d'un autre poste existant).
3. **Mauvaise affectation de VLAN** — confirmé comme un des problèmes les plus fréquents en vrai (#4 Fluke), nécessite d'abord un gabarit avec VLANs (déjà en projet, voir `RULES_TOPOLOGIES.md` §10 router-on-a-stick).
4. **Panne DNS** — un des symptômes les plus fréquents cités, et on a déjà un serveur DNS dans `multisite_ospf_nat` (actuellement un simple serveur web, à réutiliser/étendre).
5. **STP** (boucle/root bridge) — demande de construire nous-mêmes un scénario (aucun vrai exemple de panne trouvé jusqu'ici), donc plus de risque, à faire après les précédents.
6. EtherChannel, ACL, épuisement DHCP — déjà identifiés, à la suite.
