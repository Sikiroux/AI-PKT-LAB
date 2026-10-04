# Moteur de partages de fichiers simulés (`web/sim_files.py`)

Implémentation du brief `docs/BRIEF-IA-PARTAGES-FICHIERS.md` (base : branche
`codex/procedural-service-desk-prototype`, commit `344716d6e60c2fd0acb4116604b756144b1091a3`,
v0.19). Document à lire avec ce brief : il en reprend le contrat, précise les
choix faits et liste ce qui reste à faire par l'IA intégratrice.

**Ce module ne fait ni IO, ni réseau, ni accès disque réel.** Bibliothèque
standard Python uniquement (`copy`, `hashlib`, `math`, `secrets`). Aucune
dépendance à `sim_ad.py` ni à aucun autre fichier de `web/` : il peut être
relu et testé isolément. Ce n'est **pas** un serveur SMB — c'est une
simulation pédagogique d'un sous-ensemble volontairement restreint de son
comportement observable (voir §3).

## 1. Ce qui est livré

- `web/sim_files.py` — le moteur (± 820 lignes avec docstrings).
- `web/test_sim_files.py` — 68 tests `unittest`, couvrant les 26 critères
  d'acceptation de la section 9 du brief (voir tableau §6 ci-dessous).
- Ce document.

Aucun autre fichier n'a été modifié. Le bureau, les routes HTTP, le
contrôleur, `sim_ad.py`, le pont Packet Tracer et les anciens tests restent
exactement comme sur la branche de base. `git diff --stat` contre
`344716d` ne montre que l'ajout de ces trois fichiers.

## 2. Contrat de données (schema_version 1)

```python
{
  "schema_version": 1,
  "environment_id": "env-...",
  "server": {"id": "env-...", "name": "SRV-FILES", "ip": "10.0.0.5", "dns_name": "files.corp.local"},
  "principal_catalog": {"user_ids": ["alice", "bob"], "group_ids": ["grp-staff"]},
  "service_status": "running",            # running | stopped
  "firewall_tcp445_allowed": True,
  "volume": {"capacity_bytes": 123456, "background_used_bytes": 2048},
  "shares": {
    "shr-...": {
      "id": "shr-...", "name": "Documents", "enabled": True, "hidden": False,
      "share_acl": {
        "list":   {"user_ids": [...], "group_ids": [...]},
        "read":   {"user_ids": [...], "group_ids": [...]},
        "write":  {"user_ids": [...], "group_ids": [...]},
        "delete": {"user_ids": [...], "group_ids": [...]},
      },
      "folder_acl": { ... même forme que share_acl ... },
      "quota": {"mode": "off|hard|soft", "limit_bytes": None_ou_positif},
    }
  },
  "files": {
    "file-...": {"id": "file-...", "share_id": "shr-...", "name": "Notes.txt",
                "content": "...", "read_only": False, "updated_at": 1700000000.0}
  },
  "revision": 0,
  "audit": [{"at": 1700000000.0, "operation": "generate_file_service", "actor_id": None, "code": "OK"}],
}
```

Points de contrat explicites (repris du brief, tous validés par
`validate_file_service`) :

- `server['id'] == environment_id` (convention v1, voir §3).
- Aucun droit implicite : pas d'admin/Everyone caché. `read` n'implique pas
  `list`, `write` n'implique pas `delete` — un accès complet se représente
  par 4 octrois explicites (voir génération, qui le fait pour le premier
  utilisateur sur le premier partage).
- `quota.mode == 'off'` exige `limit_bytes = None` ; `hard`/`soft` exigent un
  entier strictement positif.
- Pas de sous-dossiers en v1. Nom de fichier unique insensible à la casse
  *dans un même partage* (deux partages peuvent avoir chacun un
  `Notes.txt`).
- Taille dérivée de `len(content.encode('utf-8'))`, jamais acceptée telle
  quelle d'un appelant — recalculée à chaque validation/évaluation.
- Tous les entiers (`revision`, `capacity_bytes`, `limit_bytes`, ...) sont
  stricts : un `bool` (sous-classe d'`int` en Python) est explicitement
  rejeté par `_is_strict_int`.

## 3. Simplifications et ambiguïtés résolues

| Point | Décision |
|---|---|
| `server.id` vs `environment_id` | Exigés strictement égaux, partout (génération, validation, contexte). Cohérent avec l'usage réel de `web/directory_adapter.py` pour `sim_ad`, qui identifie toujours le serveur par l'ID d'environnement. |
| Requête mal formée vs contexte incomplet | `request` mal formé → `FileServiceError` (exception) : l'adaptateur construit toujours une requête bien formée, une erreur ici est un bug d'intégration. `context` incomplet/périmé → résultat souple `INVALID_CONTEXT`/`OBSERVATION_UNKNOWN` : un contexte réel peut légitimement être incomplet (latence, projection non encore rafraîchie), donc jamais d'exception, toujours fail-closed. |
| `expected_revision` : étage pédagogique ou garde séparée ? | **Séparée.** La section 6 du brief énumère 10 étages, et la concurrence optimiste n'en fait pas partie : c'est une question de coordination serveur, pas de droit utilisateur. Vérifiée uniquement dans `perform_file_action`, après que `evaluate_access` a confirmé `allowed=True`. Un fichier en lecture seule bloque donc *avant* qu'on atteigne la vérification de revision (voir test `test_read_only_blocks_write_and_delete_not_read`, et le comportement observé : une requête avec une `expected_revision` fausse sur un fichier *aussi* en lecture seule renvoie `FILE_READ_ONLY`, pas `REVISION_CONFLICT` — la chaîne pédagogique passe en premier). |
| Omission du nom de domaine comme seule exception à « toujours montrer l'étage » | `name_resolution` est omis de l'arbre (pas montré en `blocked`) uniquement quand `address_mode` ne peut pas être déterminé (échec de `scope`, qui garantit la présence/forme de `address_mode`). Dans tous les autres cas (y compris `address_mode == 'ip'`), l'absence du nœud est le signal attendu que la résolution de nom n'est simplement pas pertinente pour cette requête — pas un étage bloqué. Tous les autres étages (réseau, pare-feu, service, partage, compte, authentification, droits, fichier, lecture seule, capacité, quota) sont **toujours** présents dans l'arbre dès lors qu'ils s'appliquent à l'action demandée, y compris en `blocked`. |
| `QUOTA_WARNING` | Code ajouté en plus de la liste minimale du brief (qui ne l'énumère pas explicitement mais décrit le comportement : « quota doux avertit sans bloquer »). Renvoyé à la place de `OK` quand `allowed=True` mais qu'un quota `soft` est dépassé par l'écriture. Jamais renvoyé en dehors de `write`, jamais si `allowed=False`. |
| Ordre capacité/quota | Capacité volume (`DISK_FULL`) vérifiée avant quota par partage (`QUOTA_EXCEEDED`/`QUOTA_WARNING`), conforme à la formulation du brief (« Capacité et quota dur pour les écritures qui augmentent l'occupation »). Les deux ne sont évalués que si l'écriture **augmente** la taille (delta > 0) : une réduction ou un remplacement par un contenu plus court ne déclenche jamais ces étages, même service plein ou quota dépassé (overage administratif valide, voir ligne suivante). |
| Dépassement administratif | Un changement de capacité/quota peut rendre un état existant en dépassement (ex. capacité réduite sous l'occupation actuelle). `validate_file_service` l'accepte explicitement comme état valide — ce n'est testé/bloqué qu'au moment d'une **nouvelle** écriture qui *augmenterait* encore l'occupation. Lecture, suppression et réduction restent toujours possibles. |
| `hidden` | Masque uniquement la *découverte* dans une future UI d'administration/navigation (non implémentée ici). N'affecte jamais `evaluate_access` : un accès direct par `share_id` à un partage `hidden=True` suit exactement la même chaîne que s'il ne l'était pas. |
| `directory_resource` (ancien, v0.19) | Jamais lu ni écrit par ce module. Le brief est explicite : ne pas l'utiliser comme troisième restriction concurrente aux nouvelles ACL ; la migration/rattachement est le travail de l'intégrateur (section 10). |
| Identité/groupes/compte | Jamais recalculés ici. `context['identity']` est reçu déjà évalué (`account_allowed`, `authentication_valid` proviennent de `sim_ad.evaluate_user`/session côté adaptateur). Ce module ne prouve aucune appartenance : il fait confiance à la projection fournie, et refuse fail-closed si elle est absente ou mal typée. |

## 4. Erreurs de contrat vs résultats d'évaluation

Deux familles strictement séparées, comme dans `sim_ad.py` :

### Exceptions (`FileServiceError`, toujours `.code` stable)

| Code | Levé par |
|---|---|
| `INVALID_SCHEMA` | `validate_file_service` sur un état structurellement invalide |
| `INVALID_REQUEST` | `generate_file_service`/`_validate_request_shape`/opérations admin sur une entrée mal formée (type, champ manquant, nom invalide, bool au lieu d'entier, ...) |
| `UNKNOWN_ENVIRONMENT` | `public_file_service`/`apply_operation` quand l'acteur n'appartient pas à l'environnement du service |
| `PERMISSION_DENIED` | `public_file_service`/`apply_operation` quand `files.manage` manque dans `actor['permissions']` |
| `UNKNOWN_OPERATION` | `apply_operation` sur un nom d'opération non reconnu |
| `UNKNOWN_SHARE` / `UNKNOWN_FILE` | opérations admin référençant un `share_id`/`file_id` inexistant |
| `UNKNOWN_PRINCIPAL` | ACL (génération, validation ou `set_acl`) référençant un `user_id`/`group_id` absent de `principal_catalog` |

### Résultats (`evaluate_access`/`perform_file_action`, jamais levés)

`OK, INVALID_CONTEXT, NAME_UNRESOLVED, NETWORK_DOWN, OBSERVATION_UNKNOWN,
TCP445_BLOCKED, SERVICE_STOPPED, SHARE_NOT_FOUND, SHARE_DISABLED,
ACCOUNT_UNAVAILABLE, NOT_AUTHENTICATED, SHARE_ACCESS_DENIED,
FILESYSTEM_ACCESS_DENIED, FILE_NOT_FOUND, NAME_CONFLICT, FILE_READ_ONLY,
DISK_FULL, QUOTA_EXCEEDED, QUOTA_WARNING, REVISION_CONFLICT` — tous repris
tels quels du brief, plus `QUOTA_WARNING` (voir §3). Ces codes n'apparaissent
jamais comme attribut `.code` d'une exception : un refus d'accès normal
(réseau indisponible, partage désactivé, droit manquant, quota...) est
*toujours* un résultat `{allowed, status, code, tree, evidence}`, jamais un
crash. L'intégrateur est libre de filtrer ces codes détaillés avant de les
exposer dans un ticket, pour ne pas donner la réponse (le brief le demande
explicitement — ce module ne fait aucun filtrage lui-même).

## 5. Les 10 étages pédagogiques (section 6 du brief)

Ordre de `evaluate_access`, chaque étage toujours présent dans l'arbre dès
qu'il s'applique à l'action demandée (sauf `name_resolution`, voir §3) :

1. `scope` — forme du contexte (environnement, cible, source, address_mode,
  identité). `unknown` si absent/mal formé (jamais `failed` : on ne sait
  simplement rien).
2. `name_resolution` — uniquement si `address_mode == 'name'`.
3. `network` — fraîcheur de l'observation (`observed_at <= now <= valid_until`),
  cohérence source/cible avec le contexte, puis `status`.
4. `firewall` — simulation du port TCP 445.
5. `service` — `service_status == 'running'`.
6. `share_found` puis `share_enabled`.
7. `account` (`identity.account_allowed`) puis `authentication`
  (`identity.authentication_valid`).
8. `share_permission` (`share_acl`) **et** `filesystem_permission`
  (`folder_acl`) — un octroi direct (`user_id`) OU via un groupe
  (`group_ids ∩ grant.group_ids`) dans **chacune** des deux couches.
9. `file_lookup` — fichier existant (read/delete/write-remplacement) ou nom
  disponible (write-création) — puis `read_only` (write-remplacement et
  delete uniquement, jamais en lecture ni en création).
10. `capacity` (volume entier) puis `quota` (partage) — uniquement pour une
   écriture qui augmente la taille occupée (`delta > 0`).

Dès le premier étage qui n'est pas `passed`, **tous les suivants
apparaissent dans l'arbre avec `status: "blocked"`** (jamais absents, jamais
réévalués avec leur propre verdict) : implémenté par `_chain()`, qui reçoit
la liste complète des étages applicables — calculés avec des valeurs sûres
par défaut même quand les données amont manquent — et impose `blocked` à
tout étage situé après le premier non-`passed`, quelle que soit sa valeur
calculée naïvement.

`evidence` (`tcp445` ou `icmp_proxy`) est recopié tel quel depuis
`context['network']['evidence']`. Un succès avec `icmp_proxy` signifie
uniquement « accessible dans le modèle pédagogique sous hypothèse de
transport » — jamais « SMB réellement testé » ; ce module ne fabrique aucun
faux ping ni faux résultat TCP.

## 6. Correspondance critères d'acceptation ↔ tests

| # | Critère (résumé) | Test(s) |
|---|---|---|
| 1 | Reproductibilité seed/environment_id/server/principals/now | `GenerationTests.test_reproducible_with_same_inputs`, `test_does_not_touch_global_random_stream` |
| 2 | Identité stable après renommage | `ApplyOperationTests.test_set_acl_replaces_entire_layer_not_partial_merge` (id de partage inchangé après `rename_share`/`set_acl`), `ApplyOperationTests.test_repairing_one_share_does_not_touch_others` |
| 3 | Premier utilisateur fait les 4 actions sur le premier partage | `GenerationTests.test_first_user_can_perform_all_four_actions_on_first_share` |
| 4 | Isolation par environnement | `GenerationTests.test_requires_server_id_equal_environment_id`, `AccessEvaluationTests.test_wrong_environment_in_context_refused`, `ApplyOperationTests.test_wrong_environment_actor_refused_without_mutation`, `PublicProjectionTests.test_wrong_environment_actor_refused` |
| 5 | Classes de fraîcheur réseau | `AccessEvaluationTests.test_stale_network_observation_is_unknown_not_failure`, `test_network_down_is_failure_not_unknown` |
| 6 | Comportement ip/name | `AccessEvaluationTests.test_name_mode_resolved_ok`, `test_name_mode_wrong_ip_refused`, `test_ip_mode_does_not_require_name_resolution`, `test_name_resolution_stage_omitted_in_ip_mode` |
| 7 | Pannes TCP445/service/partage indépendantes + réparation | `AccessEvaluationTests.test_tcp445_blocked_refuses_independently_and_repair_restores`, `test_service_stopped_refuses_independently_and_repair_restores`, `test_share_disabled_refuses_independently_and_repair_restores` |
| 8 | Refus compte/authentification sans fuite | `AccessEvaluationTests.test_account_unavailable_refused_without_leaking_state`, `test_not_authenticated_refused` |
| 9 | Octroi groupe vs direct, deux couches requises | `AccessEvaluationTests.test_group_grant_satisfies_permission_like_direct_grant`, `test_both_layers_required_share_only_is_not_enough`, `test_both_layers_required_folder_only_is_not_enough` |
| 10 | Indépendance list/read/write/delete, `hidden` non bloquant | `AccessEvaluationTests.test_read_right_does_not_imply_list_or_write_or_delete`, `test_hidden_share_does_not_block_direct_access` |
| 11 | Pas de fuite de contenu via list/projection | `AccessEvaluationTests.test_list_result_never_contains_file_content`, `PublicProjectionTests.test_projection_has_no_file_content_or_auth_context` |
| 12 | Noms dupliqués/invalides/traversée refusés | `ValidationTests.test_rejects_duplicate_name_case_insensitive_within_share`, `test_rejects_traversal_and_separators_in_filename`, `PerformActionTests.test_create_rejects_name_conflict_case_insensitive` |
| 13 | Taille UTF-8 correcte, deltas création/remplacement/suppression | `PerformActionTests.test_write_create_then_replace_then_delete_size_deltas` |
| 14 | Frontière exacte capacité/quota (+1 octet refusé) | `QuotaTests.test_hard_quota_exact_boundary_allowed_one_byte_over_refused` |
| 15 | Disque plein : lecture/suppression/réduction OK, croissance refusée | `QuotaTests.test_disk_full_blocks_growth_but_allows_read_delete_and_shrink` |
| 16 | hard bloque / soft avertit (`QUOTA_WARNING`) / off ne vérifie jamais | `QuotaTests.test_hard_quota_exact_boundary_allowed_one_byte_over_refused`, `test_soft_quota_warns_without_blocking`, `test_quota_off_never_checked` |
| 17 | Volume partagé vs quota par partage | `QuotaTests.test_capacity_is_volume_wide_quota_is_per_share` |
| 18 | `read_only` bloque modif/suppression, pas la lecture | `ReadOnlyTests.test_read_only_blocks_write_and_delete_not_read` |
| 19 | Admin sans `files.manage`/mauvais environnement/opération ou champ inconnu refusés | `ApplyOperationTests.test_missing_capability_refused_without_mutation`, `test_wrong_environment_actor_refused_without_mutation`, `test_unknown_operation_refused_without_mutation`, `test_unknown_field_in_payload_refused` |
| 20 | Entrée inchangée après succès/refus, copie indépendante | `PerformActionTests.test_input_service_never_mutated_on_success`, `test_input_service_never_mutated_on_refusal`, `test_returned_service_is_independent_copy`, `ApplyOperationTests.test_input_service_never_mutated` |
| 21 | Mutations réussies incrémentent revision/audit sans contenu ; lectures/refus laissent revision inchangée | `PerformActionTests.test_successful_write_bumps_revision_and_audit`, `test_successful_delete_bumps_revision_and_audit`, `test_list_and_read_do_not_bump_revision`, `test_refusal_does_not_bump_revision`, `ApplyOperationTests.test_successful_operation_bumps_revision_and_audit` |
| 22 | Revision périmée = `REVISION_CONFLICT` sans mutation | `PerformActionTests.test_stale_revision_refused_without_mutation` |
| 23 | Validation refs/types/timestamps/caps, dépassement admin valide | `ValidationTests.test_rejects_bool_as_integer`, `test_rejects_cross_environment_server`, `test_administrative_overage_is_a_valid_state`, `GenerationTests.test_generation_respects_caps` |
| 24 | Réparer une ACL/un partage ne touche aucun autre partage/fichier/service | `ApplyOperationTests.test_repairing_one_share_does_not_touch_others` |
| 25 | Round-trip JSON préservant le comportement, exemple de doc exécuté | `JSONRoundtripTests.test_service_survives_json_roundtrip_and_still_behaves`, `test_documentation_example_runs` |
| 26 | Succès `icmp_proxy` distinct de `tcp445`, jamais présenté comme observation SMB réelle | `AccessEvaluationTests.test_icmp_proxy_evidence_is_distinct_from_tcp445` |

## 7. Exemple minimal exécutable

Rejoué tel quel par `test_sim_files.JSONRoundtripTests.test_documentation_example_runs` —
si ce test passe, l'exemple ci-dessous est garanti à jour et exécutable :

```python
import sim_files as sf

server = {'id': 'env-doc', 'name': 'SRV-FILES', 'ip': '10.1.1.10', 'dns_name': 'files.exemple.local'}
principals = {'user_ids': ['alice'], 'group_ids': []}
service = sf.generate_file_service('exemple-doc', 'env-doc', server, principals, 1_000_000)

share_id = next(iter(service['shares']))
context = {
    'environment_id': 'env-doc', 'source_device_id': 'pc-alice', 'target_device_id': 'env-doc',
    'network': {'status': 'up', 'observed_at': 999_990, 'valid_until': 1_000_100,
               'source_device_id': 'pc-alice', 'target_device_id': 'env-doc', 'evidence': 'tcp445'},
    'address_mode': 'ip',
    'identity': {'user_id': 'alice', 'group_ids': [], 'account_allowed': True, 'authentication_valid': True},
}

result = sf.evaluate_access(service, {'action': 'list', 'share_id': share_id}, context, 1_000_000)
assert result == {
    'allowed': True, 'status': 'passed', 'code': 'OK',
    'tree': result['tree'],  # arbre complet des 9 étages applicables (pas de name_resolution en mode ip)
    'evidence': 'tcp445',
}
```

## 8. Catalogue pédagogique de pannes (section 8 du brief — documenté, pas implémenté ici)

Ce module ne génère aucun ticket et n'injecte aucune panne aléatoire dans
`evaluate_access` : le générateur produit un état **sain**, et c'est une
mutation ultérieure (via `apply_operation`, ou en modifiant directement
l'état côté intégrateur/générateur de scénario) qui introduit chacune de ces
pannes. Table reproduite du brief pour référence :

| Famille | Symptôme observable | Réparation |
|---|---|---|
| Coupure réseau | `NETWORK_DOWN`/`OBSERVATION_UNKNOWN` dès l'étage `network` | Rétablir la liaison ; l'observation redevient fraîche |
| DNS erroné | `NAME_UNRESOLVED` en mode `name` uniquement | Corriger la résolution (`resolved_ip` == `server.ip`) |
| TCP 445 bloqué | `TCP445_BLOCKED` | `apply_operation('set_firewall', {'allowed': True})` |
| Service arrêté | `SERVICE_STOPPED` | `apply_operation('set_service_status', {'status': 'running'})` |
| Partage désactivé | `SHARE_DISABLED` | `apply_operation('set_share_enabled', {'enabled': True})` |
| Droit incomplet (une seule couche) | `SHARE_ACCESS_DENIED` ou `FILESYSTEM_ACCESS_DENIED` | `apply_operation('set_acl', ...)` sur la couche manquante |
| Quota dur atteint | `QUOTA_EXCEEDED` | `apply_operation('set_quota', ...)` avec une limite plus haute, ou libérer de l'espace (suppression/réduction, toujours permises) |
| Disque plein / fichier lecture seule | `DISK_FULL` / `FILE_READ_ONLY` | `apply_operation('set_volume_capacity', ...)` / `apply_operation('set_file_read_only', {'read_only': False})` |

Comptes verrouillés/désactivés et mots de passe restent entièrement gérés
par `sim_ad` — ce module ne les duplique jamais (`ACCOUNT_UNAVAILABLE`/
`NOT_AUTHENTICATED` reflètent simplement ce que `context['identity']`
rapporte). Le quota par partage simulé ici (racine du partage uniquement)
est explicitement distinct du quota disque par utilisateur Windows — non
simulé en v1.

## 9. Limites explicites de v1

Pas de sous-dossiers, pas d'ACE de refus (deny), pas d'héritage, pas de
propriétaire de fichier, pas de groupes imbriqués, pas de verrouillage de
fichier, pas de DFS, pas de cache hors connexion, pas de Kerberos, pas de
négociation de dialecte SMB, aucun accès disque serveur réel. `evidence:
icmp_proxy` ne prouve jamais un SMB réellement testé. Aucune de ces
limitations n'est contournée par une astuce côté intégrateur : le brief
demande explicitement de ne jamais présenter un succès pédagogique comme une
validation SMB réelle.

## 10. Ce qui reste à faire par l'IA intégratrice (section 10 du brief)

Non traité ici, volontairement :

- Migration des droits `Documents-Lecture`/`Documents-Ecriture` (v0.19,
  `docs/V019-ANNUAIRE-INTEGRE.md`) vers les nouvelles ACL à deux couches —
  et décision sur le sort de `directory_resource` (ne jamais le garder comme
  restriction concurrente, le brief est explicite).
  mapping groupes existants → `share_acl`/`folder_acl`.
- Résolution de chemin UNC / lecteur mappé → `share_id` + `context`
  (`address_mode`, `name_resolution`) : ce module reçoit ces informations
  déjà résolues, il ne fait aucune analyse DNS ni de chemin UNC complet.
- Construction de `context['identity']` à partir de `sim_ad.evaluate_user`
  et de la session technicien/serveur-contrôlée (jamais une déclaration du
  navigateur).
- Routes HTTP, fenêtres OS.js, dialogues client, stockage dans
  `state['file_service']` et persistance de `session.json`.
- Verrouillage concurrentiel réel à l'écriture (`perform_file_action`
  vérifie `expected_revision` mais ne gère ni verrou ni sauvegarde
  atomique — l'intégrateur l'exécute sous verrou puis persiste).
- Génération de tickets utilisant le catalogue de pannes (§8 ci-dessus) et
  validation de réparation par ré-exécution d'opérations dans l'état
  réparé, avec contrôle des effets collatéraux (pas un simple bouton
  booléen, conformément au brief).
- Intégration DNS/VPN/impression : explicitement hors scope, à ne pas
  démarrer sans nouvelle mission.

## 11. Résultats des tests

```
$ python -m unittest discover -s web -p "test_sim_files.py"
Ran 68 tests in 0.03s
OK

$ python -m unittest discover -s web -p "test_*.py"
Ran 248 tests in ~77s
OK

$ python tests/test_all.py
(voir rapport de session — exécuté avant commit)
```

Aucun test préexistant n'a été modifié pour faire passer ce module.

## 12. Référence rapide des fonctions publiques

```python
generate_file_service(seed, environment_id, server, principals, now) -> dict
validate_file_service(service) -> None                       # lève FileServiceError
public_file_service(service, actor) -> dict                  # lève FileServiceError
evaluate_access(service, request, context, now) -> dict       # jamais d'exception pour un refus normal
perform_file_action(service, request, context, now) -> dict
apply_operation(service, operation, payload, actor, now) -> dict
```

Opérations reconnues par `apply_operation` : `set_service_status`,
`set_firewall`, `set_share_enabled`, `rename_share`, `set_acl`, `set_quota`,
`set_volume_capacity`, `set_background_usage`, `set_file_read_only`. Chacune
exige explicitement ses propres champs de payload (voir `_op_*` dans
`sim_files.py`) — aucune n'accepte jamais d'écrire `revision`, `audit` ou
`principal_catalog`.
