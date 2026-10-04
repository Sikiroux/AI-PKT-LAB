# Moteur DNS pédagogique simulé (`web/sim_dns.py`)

Implémentation du brief `docs/BRIEF-IA-MOTEUR-DNS.md` (base : branche
`codex/procedural-service-desk-prototype`, commit
`5af1132e364b3e555cb2ef8fdee9e19392b36a2b`, v0.21). Document à lire avec ce
brief : il en reprend le contrat, précise les choix faits et liste ce qui
reste à faire par l'IA intégratrice.

**Ce module ne fait ni IO, ni réseau, ni socket, ni résolution DNS réelle.**
Bibliothèque standard Python uniquement (`copy`, `hashlib`, `ipaddress`,
`math`, `re`, `secrets`). Aucune dépendance à `sim_ad.py` ni `sim_files.py` :
il peut être relu et testé isolément. Ce n'est **pas** un serveur DNS
complet ni une implémentation des RFC — c'est la simulation pédagogique
d'un sous-ensemble volontairement restreint, pour une zone interne unique
(voir §3).

**Particularité par rapport à `sim_ad`/`sim_files`** : la résolution DNS ne
vérifie **aucune identité ni authentification** — le contexte fourni par le
serveur (section 5 du brief) ne contient pas de bloc `identity`, à la
différence de `sim_files`. C'est volontaire et réaliste : une requête DNS
n'est normalement pas authentifiée dans ce modèle de petite entreprise. Les
comptes/groupes restent entièrement gérés par `sim_ad`, les droits sur les
fichiers par `sim_files` ; ce moteur ne duplique ni l'un ni l'autre.

## 1. Ce qui est livré

- `web/sim_dns.py` — le moteur (± 620 lignes avec docstrings).
- `web/test_sim_dns.py` — 85 tests `unittest`, couvrant les 23 critères
  d'acceptation de la section 7 du brief (voir tableau §7 ci-dessous).
- Ce document.

Aucun autre fichier n'a été modifié. Le bureau, les routes HTTP, le
contrôleur, `sim_ad.py`, `sim_files.py`, le pont Packet Tracer et les
anciens tests restent exactement comme sur la branche de base. `git diff
--stat` contre `5af1132` ne montre que l'ajout de ces trois fichiers.

## 2. Contrat de données (schema_version 1)

```python
{
  "schema_version": 1,
  "environment_id": "env-...",
  "server": {"id": "server", "name": "SRV-DNS", "ip": "10.0.0.5", "zone": "agence.test"},
  "clients": {
    "client": {"id": "client", "name": "PC-ALICE", "dns_server_ip": "10.0.0.5" | None,
               "search_suffix": "agence.test" | ""}
  },
  "records": {
    "rec-...": {"id": "rec-...", "name": "srv-fichiers.agence.test", "type": "A|AAAA|CNAME",
               "value": "10.0.0.5", "ttl": 300, "enabled": True}
  },
  "service_status": "running",            # running | stopped
  "transport_allowed": True,              # politique de transport simulée
  "negative_ttl": 120,                    # secondes, utilisé pour NXDOMAIN/NODATA
  "cache": {
    "client": {
      "srv-fichiers.agence.test|A": {
        "response": {"code": "OK", "canonical_name": "...", "answers": [...], "addresses": [...], "cname_chain": [...]},
        "cached_at": 1700000000.0, "expires_at": 1700000300.0,
        "provenance": {"evidence": "simulated_dns", "transport_evidence": "dns_proxy"},
      }
    }
  },
  "revision": 0,
  "audit": [{"at": 1700000000.0, "operation": "generate_dns", "actor_id": None, "code": "OK"}],
}
```

Points de contrat explicites (repris du brief, tous validés par
`validate_dns`) :

- `server.id` (identité de l'appareil) et `environment_id` (identité de
  session) sont **deux identités distinctes** — aucune égalité exigée (voir
  §3).
- `clients`/`records` sont indexés par ID ; les ID sont stables après mise à
  jour (`upsert_record` avec `record_id` conserve l'ID existant).
- Un seul enregistrement **actif** par `(nom, type)` ; un CNAME actif exclut
  tout A/AAAA actif au même nom ; A et AAAA peuvent coexister. Des
  enregistrements **désactivés** en doublon ne violent pas cette règle
  (utile pour désactiver puis réactiver un ancien enregistrement erroné
  comme panne/réparation).
- TTL entier strict, `0 <= ttl <= 86400` (borne du modèle, voir brief).
  `negative_ttl` suit la même borne, par cohérence (extension documentée,
  non explicitement bornée par le brief).
- Tous les noms de la zone et les cibles CNAME sont *dans* la zone gérée ;
  un alias externe est rejeté à la mutation (`RECORD_OUT_OF_ZONE`), jamais
  silencieusement accepté.
- `clients[*].dns_server_ip` peut être `None` (poste non configuré,
  `DNS_NOT_CONFIGURED`) ou n'importe quelle adresse IP valide — y compris
  une adresse différente de `server.ip` (poste mal configuré,
  `DNS_SERVER_UNMODELED`), un état volontairement atteignable par
  `set_client_dns` pour l'exercice.

## 3. Simplifications et ambiguïtés résolues

| Point | Décision |
|---|---|
| `server.id` vs `environment_id` | **Jamais égaux de force**, cohérent avec le correctif déjà appliqué à `sim_files` (voir `docs/SIM-FILES-IMPLEMENTATION.md` §13) et avec l'usage réel observé dans `web/files_adapter.py` (`server.id == 'server'`, un ID d'appareil fixe, alors que `environment_id` vient de `state['environment_id']`). Chacun est vérifié séparément dans `_scope_ok` : `context.environment_id == service.environment_id` et `context.target_device_id == service.server.id`. |
| `query` mal formé vs `context`/réponse incomplets | `client_id`/`query` mal formés (mauvais type Python, `type` hors de `A/AAAA/CNAME`, `now` non fini) → `DNSServiceError` (exception) : l'adaptateur construit toujours un appel bien formé. `context` incomplet/périmé, `client_id` inconnu, environnement/cible erronés → résultat souple `INVALID_CONTEXT`/`OBSERVATION_UNKNOWN` : jamais d'exception pour ce qui peut légitimement varier côté adaptateur (latence, projection pas encore rafraîchie). |
| Grammaire de nom (`INVALID_NAME`) : résultat ou exception ? | **Résultat souple**, pas une exception — contrairement à `sim_files` où un nom de fichier invalide à la création est une erreur de contrat (le nom y est un paramètre d'administration). Ici, `query.name` est ce qu'un utilisateur/une app a demandé à résoudre (équivalent d'un `nslookup`/`ping <nom>` tapé par un utilisateur simulé) — une faute de frappe est un usage normal, pas un bug d'intégration. `query.type`, en revanche, reste un paramètre structurel choisi par l'adaptateur (liste fermée A/AAAA/CNAME) : un type hors de cette liste est une exception (`INVALID_REQUEST`), par symétrie avec `action not in ACTIONS` dans `sim_files`. |
| `status` global par code | Pas donné explicitement pour tous les codes dans le brief (seul `REFUSED` → `status=failed` est écrit noir sur blanc). Déduit et fixé ainsi : **resolved** = la couche DNS a produit une réponse protocolaire définitive, y compris négative (`OK`, `NXDOMAIN`, `NODATA`) ; **failed** = la résolution n'a pas pu aboutir pour une raison confirmée (`REFUSED`, `CNAME_LOOP`, `CNAME_DEPTH`, `INVALID_NAME`, `NETWORK_DOWN`, `DNS_TRANSPORT_BLOCKED`, `DNS_SERVICE_STOPPED`, `DNS_NOT_CONFIGURED`) ; **unknown** = preuve absente/incohérente, on ne sait rien (`INVALID_CONTEXT`, `OBSERVATION_UNKNOWN`, `DNS_SERVER_UNMODELED`). `CNAME_LOOP`/`CNAME_DEPTH` sont classés *failed* et non *resolved* malgré un `dns_rcode=SERVFAIL` bien défini : un SERVFAIL représente un échec du *processus* de résolution (serveur incapable de traiter la requête), pas une réponse négative légitime comme NXDOMAIN. |
| `dns_rcode` | Mapping fixe : `OK/NODATA → NOERROR`, `NXDOMAIN → NXDOMAIN`, `CNAME_LOOP/CNAME_DEPTH → SERVFAIL`, `REFUSED → REFUSED`, tout le reste → `None` (aucun échange DNS protocolaire n'a eu lieu : pas de pseudo-rcode inventé pour une panne de transport/réseau/service). |
| Ordre `resolver_config` avant `network` | Le brief l'exige explicitement (« configuration du résolveur si cache absent, réseau »). Conséquence : si `client.dns_server_ip != server.ip`, l'étage `network` est forcé `blocked` par la propagation de `_chain()`, quelle que soit la preuve réseau fournie — on ne peut jamais réclamer une preuve réseau valide vers un serveur que le client n'interroge pas. |
| Preuve réseau vs couple source/cible | `network.target_ip` doit être strictement égal à `client.dns_server_ip` **et** à `server.ip` (les deux, pas l'un ou l'autre) — si le client est mal configuré vers une autre adresse, la preuve réseau ne peut de toute façon jamais correspondre à ce que ce moteur modélise, d'où `OBSERVATION_UNKNOWN` et non une fausse confirmation. |
| `cache` : étage qui ne bloque jamais | Contrairement aux autres étages, `cache` est toujours `'passed'`, que ce soit un succès (hit) ou une absence/expiration (miss) : un cache absent n'est pas une panne, c'est l'état normal avant la première résolution. La branche **hit** est construite à part (`_forced_tree`), hors de `_chain()` : `resolver_config`/`network`/`transport`/`service`/`records` y sont explicitement forcés à `'blocked'` avec le libellé exact `« non nécessaire : réponse en cache »` (texte du brief repris mot pour mot), même si certains de ces stages seraient individuellement `'passed'` dans l'état courant du service (c'est précisément le point pédagogique : le cache a répondu sans even interroger le serveur, donc ces étages ne sont **pas évalués**, pas simplement verts par coïncidence). `status` global reste `'resolved'` sur un hit, car le brief l'exige explicitement (« La réponse globale peut néanmoins être resolved »). |
| `observed_at`/`valid_until` dans le résultat | Repurposés selon la branche : sur une résolution **en direct**, ce sont les bornes de fraîcheur de la preuve réseau utilisée (`context['network']['observed_at']/['valid_until']`) ; sur un **hit**, ce sont `cached_at`/`expires_at` de l'entrée rejouée — dans les deux cas, « la fenêtre de validité qui justifie ce résultat précis ». Sur un refus survenu *avant* le stage `network` (scope, query, resolver_config), ces deux champs restent `None` : il n'y a alors aucune fenêtre de fraîcheur pertinente à rapporter. |
| `answers` sur un échec | Toujours vide (`[]`) dès que le code n'est pas un succès, y compris `CNAME_LOOP`/`CNAME_DEPTH`/NXDOMAIN atteint à mi-chaîne — même si des alias intermédiaires ont été traversés avant l'échec. `cname_chain`, lui, reste informatif : il liste les alias effectivement suivis avant l'échec (utile pour diagnostiquer où la chaîne casse), mais `answers` ne décrit jamais une réponse qui n'a pas abouti. |
| `flush_cache` : fonction séparée | Le brief décrit `flush_cache(client_id)` avec sa propre règle d'autorisation à deux voies (`dns.manage` **ou** `dns.flush_own` + `device_id==client_id` + même environnement) — un modèle d'autorisation incompatible avec le capability-check unique et uniforme d'`apply_operation`. Exposée comme 6ᵉ fonction publique : `flush_cache(service, actor, client_id, now)`. L'acteur y porte un champ `device_id` optionnel, absent du contrat d'acteur générique `{id, environment_id, permissions}` de la section 6 — extension documentée ici, nécessaire uniquement pour la voie libre-service. |
| `flush_cache` sur un cache déjà vide | Toujours un succès qui incrémente `revision`/`audit` (c'est l'autorisation et la tentative qui comptent, pas qu'il y ait eu quelque chose à vider) — cohérent avec le principe général « une mutation autorisée bouge toujours la revision, qu'elle change ou non le contenu observable ». |
| Alias générés (`generate_dns`) | Un petit pool fixe de préfixes usuels (`www`, `intranet`, `portail`, `acces`) peut produire 0 à 2 CNAME supplémentaires, mais **toujours** vers une ressource réellement fournie (jamais un nom/une adresse inventés) — respecte « une zone et les mêmes ressources ne doivent pas conduire à des noms fixes sans rapport avec l'environnement » : les noms A/AAAA eux-mêmes ne sont *jamais* générés, seuls des alias *vers* eux le sont, et seulement vers des ressources authentiques. |
| `generate_dns` et configurations clients | « Exige des configurations saines » est lu comme une **validation** du contrat d'entrée (lever si `dns_server_ip != server.ip` ou `search_suffix` ∉ {``, zone}), jamais une correction silencieuse : les valeurs fournies par l'appelant ne sont jamais réécrites, exactement comme les noms/adresses des ressources sont toujours conservés tels quels. |

## 4. Erreurs de contrat vs résultats de résolution

### Exceptions (`DNSServiceError`, toujours `.code` stable)

| Code | Levé par |
|---|---|
| `INVALID_SCHEMA` | `validate_dns` sur un état structurellement invalide |
| `INVALID_REQUEST` | `resolve`/`generate_dns`/opérations admin sur une entrée mal formée (type, champ manquant, borne dépassée, `now` non fini, `query.type` inconnu...) |
| `UNKNOWN_ENVIRONMENT` | `apply_operation`/`flush_cache`/`public_dns` quand l'acteur n'appartient pas à l'environnement du service |
| `PERMISSION_DENIED` | idem, capacité manquante (`dns.manage` ou, pour `flush_cache`, ni `dns.manage` ni `dns.flush_own`+poste correspondant) |
| `UNKNOWN_OPERATION` | `apply_operation` sur un nom d'opération non reconnu |
| `UNKNOWN_CLIENT` | opération/`flush_cache` référençant un `client_id` inexistant |
| `UNKNOWN_RECORD` | opération référençant un `record_id` inexistant |
| `RECORD_CONFLICT` | activation d'un enregistrement en doublon actif, ou CNAME actif coexistant avec A/AAAA actif au même nom |
| `RECORD_OUT_OF_ZONE` | nom ou cible CNAME hors de la zone gérée |

### Résultats (`resolve`, jamais levés)

`OK, NODATA, NXDOMAIN, CNAME_LOOP, CNAME_DEPTH, REFUSED, INVALID_NAME,
INVALID_CONTEXT, DNS_NOT_CONFIGURED, DNS_SERVER_UNMODELED, NETWORK_DOWN,
OBSERVATION_UNKNOWN, DNS_TRANSPORT_BLOCKED, DNS_SERVICE_STOPPED` — tous
repris du brief. Un refus/une réponse négative normale est *toujours* un
résultat `{status, code, dns_rcode, tree, ...}`, jamais un crash.

## 5. Les 8 étages pédagogiques (section 5-6 du brief)

Ordre de `resolve` (branche sans cache valide) :

1. `scope` — environnement, client connu, source/cible cohérentes avec
   `context`. `unknown` si absent/mal formé.
2. `query` — normalisation (suffixe si pas de point, casse, point final),
   grammaire hostname (`INVALID_NAME`), appartenance à la zone (`REFUSED`).
3. `cache` — toujours `passed` ; bifurque vers la branche *hit* dédiée si
   une entrée valide existe (voir §3).
4. `resolver_config` — `dns_server_ip` non nul (`DNS_NOT_CONFIGURED`) et
   égal à `server.ip` (`DNS_SERVER_UNMODELED`, `status=unknown`).
5. `network` — fraîcheur de la preuve, couple source/cible, `target_ip`
   cohérent.
6. `transport` — simulation du transport DNS (`transport_allowed`).
7. `service` — `service_status == 'running'`.
8. `records` — recherche et suivi de chaîne CNAME (voir §6).

Dès le premier étage non `passed`, tous les suivants apparaissent `blocked`
(jamais absents, jamais réévalués) — implémenté par le même `_chain()` que
`sim_files.py`, renvoyant en plus un `label` humain par étage (champ exigé
par ce brief, absent du schéma d'arbre de `sim_files`).

## 6. Résolution d'enregistrements et chaîne CNAME

- `type == CNAME` demandé directement : une seule recherche au nom exact,
  jamais de suivi. `OK` si une CNAME active existe, `NODATA` si le nom
  existe sans CNAME, `NXDOMAIN` si rien n'existe à ce nom.
- `type` ∈ `{A, AAAA}` : suit les CNAME actives rencontrées jusqu'à trouver
  un enregistrement du type demandé, une absence totale (`NXDOMAIN`,
  y compris une cible CNAME cassée/absente), ou un nom présent sans ce type
  (`NODATA`).
- Boucle : un nom déjà visité dans la chaîne → `CNAME_LOOP` (`SERVFAIL`).
- Profondeur : au plus 8 sauts CNAME suivis ; un 9ᵉ saut nécessaire →
  `CNAME_DEPTH` (`SERVFAIL`). 8 sauts suivis d'un enregistrement final est
  donc permis, pas 9.
- `canonical_name` = le dernier nom examiné (succès, NXDOMAIN ou NODATA).
- `cname_chain` = la liste des noms d'alias effectivement suivis, dans
  l'ordre, qu'il y ait succès ou échec en aval.

## 7. Correspondance critères d'acceptation ↔ tests

| # | Critère (résumé) | Test(s) |
|---|---|---|
| 1 | Reproductibilité, seed dédiée, RNG global préservé, ressources/adresses conservées, génération saine | `GenerationTests.test_reproducible_with_same_inputs`, `test_does_not_touch_global_random_stream`, `test_given_names_and_addresses_preserved`, `test_healthy_state_has_no_hidden_fault` |
| 2 | server.id indépendant de environment_id ; mauvais environnement/client/target refusé AVANT cache | `ScopeTests.test_server_id_independent_of_environment_id`, `test_wrong_environment_refused_before_cache`, `test_unknown_client_refused`, `test_wrong_target_device_refused`, `ValidationTests.test_server_id_distinct_from_environment_id_is_valid` |
| 3 | Noms casse/point final équivalents, suffixe déterministe, noms invalides, type inconnu, hors zone | `NameNormalizationTests` (toutes les méthodes) |
| 4 | A IPv4, AAAA IPv6, mauvaise famille refusée, pas de AAAA inventé | `AddressFamilyTests` (toutes les méthodes) |
| 5 | NXDOMAIN vs NODATA, record désactivé, A+AAAA coexistent, conflit CNAME/A refusé | `ExistenceTests`, `ValidationTests.test_a_and_aaaa_coexist_at_same_name`, `test_rejects_active_cname_coexisting_with_active_a` |
| 6 | CNAME direct, chaîne A/AAAA, cible absente, boucle, profondeur 8/9 | `CnameChainTests` (toutes les méthodes) |
| 7 | Résolution vers adresse incorrecte reste un succès, sans mutation d'adresse | `WrongAddressTests.test_resolution_to_deliberately_wrong_ip_is_still_a_success` |
| 8 | DNS absent, serveur non modélisé (unknown), preuve vers mauvaise adresse, paire erronée | `ResolverConfigTests` (toutes les méthodes) |
| 9 | Network down vs unknown, preuve expirée/future/absente, bornes exactes | `NetworkFreshnessTests` (toutes les méthodes) |
| 10 | Blocage politique/service arrêtés sans faux NXDOMAIN ni cache négatif | `PolicyTests` (toutes les méthodes) |
| 11 | Hit sans réseau, DNS/service cassés après coup ne détruisent pas un hit déjà valide | `CacheHitTests.test_hit_works_without_any_network_proof`, `test_hit_survives_service_stopped_and_dns_misconfigured` |
| 12 | Cache isolé entre clients/environnements, A et AAAA séparés | `CacheIsolationTests` (toutes les méthodes) |
| 13 | TTL=0 non caché, expiration exacte, hit ne prolonge pas, minimum TTL CNAME | `TtlCacheTests` (toutes les méthodes) |
| 14 | Record corrigé mais cache ancien conservé jusqu'à TTL/flush, réduire TTL ne raccourcit pas | `RepairAndStaleCacheTests.test_fixed_record_not_reflected_until_expiry`, `test_reducing_ttl_does_not_shorten_existing_cache` |
| 15 | Cache négatif NXDOMAIN/NODATA, nouveau record pas immédiatement visible, expiration/flush répare | `RepairAndStaleCacheTests.test_negative_cache_nxdomain_and_nodata`, `test_new_record_not_immediately_visible_after_negative_cache`, `test_flush_repairs_immediately` |
| 16 | Erreurs réseau/SERVFAIL non cachées, refus n'efface pas un ancien cache | `RepairAndStaleCacheTests.test_servfail_and_network_errors_not_cached_and_do_not_erase_existing_entry`, `PolicyTests.test_policy_and_service_failures_not_cached` |
| 17 | Capacités admin, flush_own limité à son poste, mauvais environnement refusé, champs non autorisés | `AdminCapabilityTests` (toutes les méthodes) |
| 18 | IDs stables sur update, validation types/références/horodatages, JSON aller-retour | `IdsAndRoundtripTests` (toutes les méthodes) |
| 19 | Revision exacte et audit, éviction bornée déterministe, aucun IO/réseau/horloge cachée | `RevisionAuditTests` (toutes les méthodes) |
| 20 | Arbre complet et blocked après échec, branche cache n'affirme pas une consultation serveur | `TreeTests` (toutes les méthodes) |
| 21 | Projection admin protégée, résultat client sans catalogue complet, provenance simulation explicite | `PublicProjectionTests` (toutes les méthodes) |
| 22 | Réparer une entrée ne modifie ni autres records ni clients ni caches étrangers | `RepairIsolationTests.test_repairing_one_record_does_not_touch_others` |
| 23 | Exemple minimal de doc réellement exécuté, tableau erreurs/limites/critère→test | `DocumentationExampleTests.test_minimal_example_runs`, ce document |

## 8. Exemple minimal exécutable

Rejoué tel quel par `test_sim_dns.DocumentationExampleTests.test_minimal_example_runs` —
si ce test passe, l'exemple ci-dessous est garanti à jour et exécutable :

```python
import sim_dns as sd

server = {'id': 'srv-dns-01', 'name': 'SRV-DNS', 'ip': '10.1.1.10', 'zone': 'exemple.test'}
clients = [{'id': 'pc-doc', 'name': 'PC-DOC', 'dns_server_ip': '10.1.1.10', 'search_suffix': 'exemple.test'}]
resources = [{'id': 'r1', 'dns_name': 'intranet.exemple.test', 'ipv4': '10.1.1.20'}]
service = sd.generate_dns('exemple-doc', 'env-doc', server, clients, resources, 1_000_000)

context = {
    'environment_id': 'env-doc', 'source_device_id': 'pc-doc', 'target_device_id': 'srv-dns-01',
    'network': {'status': 'up', 'source_device_id': 'pc-doc', 'target_device_id': 'srv-dns-01',
               'target_ip': '10.1.1.10', 'observed_at': 999_990, 'valid_until': 1_000_100, 'evidence': 'dns_proxy'},
}

out = sd.resolve(service, 'pc-doc', {'name': 'intranet', 'type': 'A'}, context, 1_000_000)
assert out['result']['status'] == 'resolved'
assert out['result']['code'] == sd.OK
assert out['result']['addresses'] == ['10.1.1.20']
```

## 9. Catalogue pédagogique de pannes (section 8 du brief — documenté, pas implémenté ici)

Ce module ne génère aucun ticket et n'injecte aucune panne aléatoire dans
`resolve` : le générateur produit un état **sain**, et c'est une mutation
ultérieure (via `apply_operation`, ou en modifiant directement l'état côté
intégrateur/générateur de scénario) qui introduit chacune de ces pannes.
Table reproduite du brief pour référence :

| Famille | Symptôme observable | Réparation |
|---|---|---|
| Record supprimé | `NXDOMAIN` (ou `NODATA` si un autre type subsiste au même nom) | `apply_operation('upsert_record', ...)` recréant l'enregistrement, ou `set_record_enabled` s'il existe encore désactivé |
| Adresse A erronée | Résolution réussie (`OK`) mais vers la mauvaise IP — ce moteur ne le détecte jamais lui-même (voir §3) | `apply_operation('upsert_record', ...)` avec la bonne adresse |
| Alias cassé | `NXDOMAIN` en suivant la chaîne jusqu'à la cible absente | Corriger la cible CNAME, ou recréer l'enregistrement cible manquant |
| Cache ancien | Une réponse valide mais périmée par rapport à l'état réel du serveur (`cache_hit=True`) | Attendre l'expiration du TTL, ou `flush_cache` |
| Mauvaise configuration DNS du client | `DNS_NOT_CONFIGURED` (IP nulle) ou `DNS_SERVER_UNMODELED` (mauvaise IP) | `apply_operation('set_client_dns', ...)` avec `server.ip` |
| Service DNS arrêté | `DNS_SERVICE_STOPPED`, jamais de faux `NXDOMAIN` | `apply_operation('set_service_status', {'status':'running'})` |

Comptes verrouillés/désactivés et mots de passe restent entièrement gérés
par `sim_ad` ; droits sur les fichiers entièrement gérés par `sim_files`. Le
quota disque par partage (`sim_files`) est sans rapport avec ce moteur.

## 10. Limites explicites de v1

Pas de récursion Internet, de délégation, de DNSSEC, de DoH/DoT, de SOA sur
le fil, de DHCP automatique, de SRV/MX/PTR, de découverte AD, de
round-robin, ni de transport binaire réel. Le cache est strictement local
au client simulé, pas un cache récursif serveur. `evidence: icmp_proxy`
(hérité des autres moteurs) et `dns_proxy` ne prouvent jamais qu'UDP 53 ou
TCP 53 ont réellement été testés — uniquement une approximation
pédagogique de connectivité. Une résolution DNS réussie ne valide jamais
SMB : l'intégrateur doit encore vérifier l'adresse attendue, le réseau vers
la cible, et les permissions via `sim_files` séparément.

## 11. Ce qui reste à faire par l'IA intégratrice (section 8 du brief)

Non traité ici, volontairement :

- Migration sauvegardée, création du contexte PT, routes HTTP, console DNS
  OS.js, diagnostic type `nslookup` simulé.
- Raccordement de la résolution aux chemins UNC ; conserver l'accès par IP
  sans dépendance DNS (ne jamais rendre le DNS obligatoire pour l'accès aux
  partages).
- Construction de `context` à partir des preuves PT réelles (le contrôleur
  web, jamais le navigateur).
- Génération de tickets utilisant le catalogue de pannes (§9 ci-dessus) et
  validation de réparation par ré-exécution d'opérations dans l'état
  réparé, avec contrôle des effets collatéraux (pas un simple bouton
  booléen).
- Verrouillage concurrentiel réel et sauvegarde atomique (`resolve`/
  `apply_operation`/`flush_cache` ne gèrent ni l'un ni l'autre eux-mêmes).

## 12. Résultats des tests

```
$ python -m unittest discover -s web -p "test_sim_dns.py"
Ran 85 tests in 1.2s
OK

$ python -m unittest discover -s web -p "test_*.py"
Ran 362 tests in ~79s
OK

$ python tests/test_all.py
(voir rapport de session — exécuté avant commit)
```

Aucun test préexistant n'a été modifié pour faire passer ce module.

## 13. Référence rapide des fonctions publiques

```python
generate_dns(seed, environment_id, server, clients, resources, now) -> dict
validate_dns(service) -> None                                  # lève DNSServiceError
resolve(service, client_id, query, context, now) -> dict        # jamais d'exception pour un refus/réponse normal
apply_operation(service, operation, payload, actor, now) -> dict
public_dns(service, actor) -> dict                              # lève DNSServiceError
flush_cache(service, actor, client_id, now) -> dict             # 6ᵉ fonction, voir §3 ; lève DNSServiceError
```

Opérations reconnues par `apply_operation` : `upsert_record`,
`delete_record`, `set_record_enabled`, `set_service_status`,
`set_transport_allowed`, `set_negative_ttl`, `set_client_dns`. Chacune
exige explicitement ses propres champs de payload (voir `_op_*` dans
`sim_dns.py`) — aucune n'accepte jamais d'écrire `revision`, `audit` ou
`cache` directement.
