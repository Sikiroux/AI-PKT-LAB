# Moteur d'annuaire AD simulé (`web/sim_ad.py`)

Implémentation du brief `docs/BRIEF-IA-MOTEUR-AD.md` (branche
`codex/procedural-service-desk-prototype`, commit `914d689`). Document à lire
avec ce brief : il en reprend le contrat, précise les choix faits et liste ce
qui reste à faire par l'IA intégratrice.

**Ce module ne fait ni IO, ni réseau, ni appel système.** Bibliothèque
standard Python uniquement (`copy`, `hashlib`, `hmac`, `secrets`, `random`).
Aucune dépendance aux autres fichiers de `web/` : il peut être testé et relu
isolément.

## 1. Ce qui est livré

- `web/sim_ad.py` — le moteur (± 800 lignes avec docstrings).
- `web/test_sim_ad.py` — 53 tests `unittest`, un par critère de la section 8
  du brief (voir tableau §6 ci-dessous).
- Ce document.

Aucun autre fichier n'a été modifié. Le bureau, les routes HTTP, le
contrôleur (`workspace_model.py`), le générateur, le pont PT et les anciens
tests restent exactement comme sur la branche de base.

## 2. Contrat de données (schema_version 1)

Identique à la section 4 du brief, avec deux champs ajoutés à `policy`
(documentés comme extension, pas comme divergence) :

```python
{
  "schema_version": 1,
  "environment_id": "env-...",
  "domain": {"id": "dom-...", "dns_name": "xxx.lab", "netbios_name": "XXX"},
  "ous": {
    "ou-...": {"id": "ou-...", "name": "...", "parent_id": None}  # racine
  },
  "users": {
    "usr-...": {
      "id": "usr-...", "username": "...", "display_name": "...", "ou_id": "ou-...",
      "enabled": True, "locked_until": None, "password_expires_at": 1234567890.0,
      "must_change_password": False, "failed_attempts": 0,
      "credential": {"algo": "pbkdf2_sha256", "iterations": 200000, "salt": "...", "hash": "..."},
    }
  },
  "groups": {"grp-...": {"id": "grp-...", "name": "...", "ou_id": "ou-...", "member_user_ids": []}},
  "computers": {"cmp-...": {"id": "cmp-...", "name": "...", "ou_id": "ou-...",
                            "device_id": "dev-...", "domain_joined": True}},
  "policy": {
    "lockout_threshold": 3, "lockout_seconds": 300,
    "password_max_age_seconds": 7776000  # AJOUT : 90 jours, section 3 ci-dessous
  },
  "revision": 0,
  "audit": [{"at": 1234567890.0, "operation": "generate_directory", "actor_id": None, "code": "OK"}],
}
```

`credential` n'existe que dans cette structure interne : `public_directory()`
le retire systématiquement (voir §4).

## 3. Simplifications et ambiguïtés résolues

Le brief demandait de documenter explicitement ces choix plutôt que de les
faire silencieusement :

- **`password_max_age_seconds` ajouté à `policy`** (90 jours par défaut). Le
  brief ne fixe que `lockout_threshold`/`lockout_seconds` dans son exemple ;
  il fallait bien une durée pour calculer `password_expires_at` à la
  génération et après `reset_password`. Valeur arbitraire mais documentée et
  centralisée (pas de constante magique éparpillée).
- **Mot de passe de formation unique** : tous les comptes générés par
  `generate_directory()` partagent le même mot de passe fictif
  `sim_ad.TRAINING_PASSWORD` (`"Formation!2026"`). Ce n'est jamais un vrai
  secret, et ça permet à un futur générateur de tickets de savoir quel mot de
  passe annoncer dans l'énoncé pour l'état sain, avant d'injecter une panne
  précise via `apply_operation`. Le sel reste aléatoire (`secrets.token_bytes`),
  donc deux générations produisent deux vérificateurs différents même avec le
  même mot de passe — conforme à la section 4 du brief ("la reproductibilité
  du monde concerne les objets et règles, pas les sels").
- **Génération vs opérations : deux sources d'aléatoire séparées.**
  `generate_directory()` utilise un `random.Random` dérivé par SHA-256
  (`seed + ':directory:v1'`), reproductible. `apply_operation()` (création
  d'utilisateur/groupe/OU/ordinateur, réinitialisation de mot de passe) utilise
  `secrets` pour ses identifiants et mots de passe temporaires : ce sont des
  actions « en direct », la reproductibilité n'a pas de sens pour elles et le
  brief ne la demande que pour la génération initiale.
- **Codes d'erreur : classe dédiée.** `DirectoryError(ValueError)` porte un
  attribut `.code` (token stable, ex. `"UNKNOWN_USER"`) en plus du message.
  `isinstance(e, ValueError)` reste vrai (conforme au brief), mais le code est
  directement accessible sans parser le message. Tous les codes sont des
  constantes de module (`sim_ad.UNKNOWN_USER`, etc.), listées exhaustivement
  au §5.
- **`evaluate_user`/`evaluate_access` avec `user_id` inconnu : exception, pas
  un résultat « refusé ».** Contrairement à `authenticate` (qui reçoit un
  `username` saisi par un utilisateur potentiellement inexistant — refus
  normal, pas d'exception), `evaluate_user`/`evaluate_access` reçoivent un
  `user_id` déjà résolu par l'appelant (session valide). Un `user_id` qui
  n'existe pas dans l'annuaire est une violation de contrat côté adaptateur,
  pas un scénario de formation — `DirectoryError(UNKNOWN_USER, ...)`.
- **Vérification défensive supplémentaire dans `evaluate_access`** : en plus
  de ce que fait déjà l'adaptateur (vérifier la provenance source/cible avant
  d'appeler le moteur, section 6 du brief), le moteur vérifie lui-même que
  `context['target_device_id'] == resource['server_device_id']` et dégrade le
  réseau en `unknown` sinon. Coûte rien, évite qu'un bug d'adaptateur se
  traduise par un accès accordé à la mauvaise ressource.
- **`move_object` et les capacités** : le brief liste les capacités par type
  d'objet mais `move_object` est une seule opération générique pour
  utilisateur/groupe/ordinateur. La capacité requise est donc résolue depuis
  `payload['object_type']` (`user` → `directory.users.manage`, `group` →
  `directory.groups.manage`, `computer` → `directory.computers.manage`), pas
  une capacité fixe pour toute l'opération.
- **`join_computer` accepte deux formes de payload** : soit
  `{"computer_id": ...}` pour rejoindre un ordinateur déjà existant mais
  sorti du domaine (`leave_computer` ne supprime jamais l'objet, juste
  `domain_joined = False` — comportement réaliste d'un vrai AD), soit
  `{"name", "ou_id", "device_id"}` pour en créer un nouveau. Documenté ici
  faute d'avoir un identifiant explicite dans le brief pour distinguer les
  deux cas.
- **Arbre `evaluate_user`** : le brief ne détaille pas sa forme précise (juste
  « réutiliser cette forme de résultat »). Choisi : même chaîne que
  `authenticate` jusqu'à `account` (réseau → service d'annuaire → état du
  compte), sans étape `credential` ni `authentication` puisque cette fonction
  ne vérifie pas de mot de passe. Le champ `account` du résultat donne le
  détail (`enabled`, `locked`, `locked_until`, `password_expired`,
  `must_change_password`) pour une console de support.
- **OU racine incluse dans `ous`**, pas implicite. Le brief ne précise pas si
  la racine du domaine doit apparaître comme une OU ; choisi de la matérialiser
  (nommée comme le `netbios_name`) pour que toute OU ait un `parent_id` cohérent
  (`None` seulement pour elle) et que la contrainte d'unicité « entre sœurs »
  s'applique uniformément.

## 4. Fonctions (contrat exact)

### `generate_directory(seed, environment_id, devices, requester, now) -> dict`

- `devices` : liste de `{"id", "name", "role"}`. Jamais modifiée (copiée avant
  toute lecture). Un objet `computers` est créé pour **chaque** device, sans
  en inventer : `role == "server"` place l'ordinateur dans l'OU « Serveurs »,
  sinon dans « Ordinateurs ». `device_id` = l'`id` fourni par l'appelant.
- `requester` : `{"id", "username", "display_name", "device_id"}`. Devient un
  utilisateur réel de l'annuaire (OU « Utilisateurs »), actif, mot de passe de
  formation, `must_change_password=False`. Son identité (`id`, `username`) est
  conservée telle quelle, jamais régénérée.
- Génère aussi 2 à 4 « collègues » fictifs (prénom/nom tirés d'un petit pool),
  avec des noms de connexion uniques, et deux groupes de sécurité standards :
  « Tous les employés » (tout le monde) et « Support Informatique » (un
  collègue tiré au hasard). Pas de groupe imbriqué (hors v1, conforme au brief).
- Reproductible : même `seed` + mêmes `devices`/`requester`/`environment_id`/
  `now` ⇒ mêmes domaine/OU/utilisateurs/groupes/ordinateurs/règles, aux sels
  de mot de passe près (voir §3).
- **Aucune panne cachée.** L'état retourné est entièrement sain (tous les
  comptes actifs, non verrouillés, mot de passe non expiré). Pour créer une
  variante de scénario, le futur générateur de tickets appelle
  `apply_operation()` par-dessus (voir §7) — jamais une panne aléatoire
  intégrée à la génération elle-même.
- Appelle `validate_directory()` avant de retourner : un bug de génération ne
  peut pas produire un annuaire incohérent silencieusement.

### `public_directory(directory) -> dict`

Projection sans `credential` (donc sans sel ni hash ni dérivé). Ne mute
jamais l'entrée. L'engine ne décide pas qui a le droit d'appeler cette
fonction — c'est à l'adaptateur de gater l'accès à la console qui l'utilise.

### `validate_directory(directory) -> None`

Lève `DirectoryError` au premier problème (ne corrige rien) :

| Code | Condition |
|---|---|
| `INVALID_SCHEMA` | version de schéma inattendue, clé racine manquante, id incohérent avec sa clé de dictionnaire, champ vide |
| `UNKNOWN_OU` | `ou_id` référencé introuvable (utilisateur, groupe, ordinateur, ou parent d'OU) |
| `DUPLICATE_OU_NAME` | deux OU de même nom (insensible à la casse) **sous le même parent** — autorisé sous des parents différents |
| `DUPLICATE_USERNAME` | deux utilisateurs avec le même nom de connexion (insensible à la casse), portée globale |
| `DUPLICATE_GROUP_NAME` | deux groupes de même nom (insensible à la casse), portée globale |
| `UNKNOWN_USER` | membre de groupe référencé introuvable |
| `OU_CYCLE` | un parent_id d'OU referme une boucle |

### `apply_operation(directory, operation, payload, actor, now) -> dict`

Retourne toujours `{"directory": <copie>, "result": {...}}` en cas de succès.
**Ne modifie jamais `directory`** : une copie (`copy.deepcopy`) est créée
avant la moindre validation, et c'est elle qui est mutée puis retournée.

Vérifications communes à toute opération, dans cet ordre :
1. `operation` dans la liste connue, sinon `DirectoryError(UNKNOWN_OPERATION)`.
2. `actor["environment_id"] == directory["environment_id"]`, sinon
   `DirectoryError(UNKNOWN_ENVIRONMENT)`.
3. Capacité requise présente dans `actor["permissions"]`, sinon
   `DirectoryError(PERMISSION_DENIED)`.
4. Validation spécifique à l'opération (références, doublons...).

En cas d'erreur à n'importe quelle étape : **aucune mutation, aucune entrée
d'audit, `revision` inchangée** (la copie de travail est simplement
abandonnée, l'original n'a jamais été touché).

En cas de succès : `revision += 1`, une entrée est ajoutée à `audit`
(`{"at", "operation", "actor_id", "code", ...identifiants concernés}` —
jamais de mot de passe, même temporaire), et `validate_directory()` est
appelée sur le résultat avant de le retourner (garde-fou final).

| Opération | Capacité | Payload | Remarques |
|---|---|---|---|
| `create_user` | `directory.users.manage` | `username, display_name, ou_id, [enabled, must_change_password, initial_password, password_expires_at]` | mot de passe de formation par défaut si `initial_password` omis |
| `update_user` | `directory.users.manage` | `user_id, [display_name, username, password_expires_at, must_change_password]` | tout autre champ (`credential`, `failed_attempts`, `revision`, `audit`...) ⇒ `IMMUTABLE_FIELD` |
| `reset_password` | `directory.passwords.reset` | `user_id, [temporary_password]` | retourne `temporary_password` **une seule fois** dans `result`, jamais dans `audit` ; pose `must_change_password=True`, remet compteurs/verrou à zéro |
| `unlock_user` | `directory.passwords.reset` | `user_id` | remet `locked_until=None`, `failed_attempts=0` |
| `set_user_enabled` | `directory.users.manage` | `user_id, enabled` | |
| `create_group` | `directory.groups.manage` | `name, ou_id` | |
| `add_group_member` / `remove_group_member` | `directory.groups.manage` | `group_id, user_id` | idempotent |
| `create_ou` | `directory.ous.manage` | `name, [parent_id]` | |
| `move_object` | selon `object_type` | `object_type (user\|group\|computer), object_id, new_ou_id` | ne déplace pas les OU elles-mêmes (hors v1) |
| `join_computer` | `directory.computers.manage` | `{computer_id, [device_id, ou_id]}` **ou** `{name, ou_id, device_id}` | voir §3 |
| `leave_computer` | `directory.computers.manage` | `computer_id` | ne supprime pas l'objet |

### `authenticate(directory, username, password, context, now) -> dict`

Retourne `{"directory": <copie, compteurs/verrou à jour>, "result": {...}}`.
Jamais d'exception pour un refus normal.

Ordre d'évaluation (chaque étape bloque les suivantes si elle échoue) :

1. **Réseau + service d'annuaire** (`context`) — si l'un des deux n'est pas
   `passed`/`running` avec une preuve fraîche et dans le bon environnement :
   `status="blocked"`, `code=NETWORK_UNAVAILABLE` ou `SERVICE_UNAVAILABLE`,
   **aucun compteur touché**.
2. Utilisateur introuvable (nom de connexion insensible à la casse) → `code=
   INVALID_CREDENTIALS`. **Même code et même forme d'arbre** qu'un mauvais mot
   de passe (voir §3/test dédié) : impossible de distinguer les deux de
   l'extérieur.
3. Compte désactivé → `ACCOUNT_DISABLED`.
4. Compte verrouillé (`locked_until` futur) → `ACCOUNT_LOCKED`. Si
   `locked_until` est dépassé, le verrou est levé automatiquement avant de
   continuer (comportement standard AD, pas besoin d'un `unlock_user` explicite
   une fois le délai passé).
5. Mot de passe incorrect → `failed_attempts += 1` ; si le seuil
   (`policy.lockout_threshold`) est atteint, pose `locked_until = now +
   lockout_seconds`. `code=INVALID_CREDENTIALS`.
6. Mot de passe correct → remet `failed_attempts=0`, lève le verrou.
7. `must_change_password` → `code=MUST_CHANGE_PASSWORD`, `allowed=False` (pas
   de connexion normale annoncée, conforme au brief).
8. Mot de passe expiré (`password_expires_at <= now`) → `code=PASSWORD_EXPIRED`,
   `allowed=False`.
9. Sinon → succès : `allowed=True`, `status="passed"`, `code=OK`,
   `result["user_id"]` renseigné.

### `evaluate_user(directory, user_id, context, now) -> dict`

Diagnostic support **sans mot de passe** : même chaîne réseau/service
d'annuaire que `authenticate`, puis expose l'état du compte
(`result["account"] = {"enabled", "locked", "locked_until", "password_expired",
"must_change_password"}`). `allowed` signifie « le compte peut tenter une
authentification » (actif et non verrouillé) ; expiration et changement
obligatoire restent des indicateurs secondaires, pas des blocages de ce champ.
`user_id` inconnu lève `DirectoryError(UNKNOWN_USER)` (voir §3). Fonction pure,
ne retourne pas de copie de l'annuaire (rien n'est muté).

### `evaluate_access(directory, user_id, resource, action, context, now) -> dict`

Chaîne complète : réseau → service de ressource → service d'annuaire → état
du compte → authentification (preuve fournie dans `context["authentication"]`,
jamais revérifiée par mot de passe) → droit sur la ressource. `action` doit
être `"read"` ou `"write"` (sinon `DirectoryError`). `resource` doit contenir
`id, server_device_id, allowed_user_ids, allowed_group_ids` (sinon
`DirectoryError(INVALID_PAYLOAD)`). Accès accordé si `user_id` est dans
`allowed_user_ids[action]` **ou** membre d'un groupe listé dans
`allowed_group_ids[action]`. Lecture et écriture sont deux listes
indépendantes (être dans `read` ne donne jamais `write`). Fonction pure.

## 5. Codes stables (référence complète)

Contrat/validation (toujours `DirectoryError`, jamais un résultat) :
`UNKNOWN_ENVIRONMENT`, `PERMISSION_DENIED`, `UNKNOWN_OPERATION`,
`INVALID_PAYLOAD`, `DUPLICATE_USERNAME`, `DUPLICATE_GROUP_NAME`,
`DUPLICATE_OU_NAME`, `UNKNOWN_USER`, `UNKNOWN_GROUP`, `UNKNOWN_OU`,
`UNKNOWN_COMPUTER`, `OU_CYCLE`, `IMMUTABLE_FIELD`, `INVALID_SCHEMA`.

Résultats d'authentification/accès (jamais d'exception) : `OK`,
`INVALID_CREDENTIALS`, `ACCOUNT_DISABLED`, `ACCOUNT_LOCKED`,
`PASSWORD_EXPIRED`, `MUST_CHANGE_PASSWORD`, `NETWORK_UNAVAILABLE`,
`SERVICE_UNAVAILABLE`, `NOT_AUTHENTICATED`, `ACCESS_DENIED`.

Toutes ces constantes sont exportées directement sur le module
(`sim_ad.UNKNOWN_USER`, etc.) — ne pas comparer de chaînes en dur côté
intégration.

## 6. Tests — commandes et résultat

```bash
python -m unittest discover -s web -p "test_sim_ad.py"   # 53 tests, ce module seul
python -m unittest discover -s web -p "test_*.py"         # suite web existante + ce module
python tests/test_all.py                                  # suite racine (moteur Packet Tracer), sans rapport avec ce module
```

Résultat au moment de la livraison : **53/53** pour `test_sim_ad.py`, suite
web existante inchangée (ce module n'importe ni ne modifie aucun fichier
existant), `tests/test_all.py` toujours vert. Aucune validation Packet Tracer
n'est pertinente ici : ce moteur ne touche ni le bureau, ni le bridge, ni un
seul fichier `.pkt`.

Correspondance avec la section 8 du brief (un ou plusieurs tests par ligne) :

| Critère du brief | Test(s) |
|---|---|
| Reproductibilité seed/entrées | `GenerationTests.test_reproducible_with_same_seed` |
| Pas d'effet sur le flux aléatoire global / devices | `test_does_not_touch_global_random_stream`, `test_does_not_mutate_devices_input` |
| Isolation de deux environnements | `EnvironmentIsolationTests.test_two_environments_independent`, `ApplyOperationContractTests.test_cross_environment_actor_rejected` |
| Compte actif ≠ accès sans authentification/droit | `EvaluateAccessTests.test_active_account_without_authentication_denied` |
| Mauvais mot de passe / seuil / expiration verrou / déverrouillage / désactivation / expiration mot de passe / changement obligatoire | `AuthenticationTests.*` (9 tests dédiés) |
| Échec réseau/service : branches bloquées, pas de compteur | `test_network_or_service_failure_blocks_without_counting_attempt` |
| Réseau inconnu/périmé/futur : jamais de succès | `test_stale_future_and_missing_network_never_succeed` |
| Groupes : ajout/retrait change l'accès ; lecture ≠ écriture | `EvaluateAccessTests.test_group_membership_grants_and_removal_revokes`, `test_read_does_not_grant_write` |
| Permissions d'administration absentes : opération refusée | `ApplyOperationContractTests.test_missing_capability_rejected`, `DirectoryOperationsTests.test_move_object_requires_matching_capability` |
| Doublons/références invalides/cycles/opérations inconnues refusés | `ValidationTests.*`, `test_unknown_operation_rejected` |
| Copie sans mutation ; erreur sans changement revision/audit ; succès journalisé sans secret | `test_input_never_mutated_even_on_success`, `test_input_never_mutated_on_error`, `test_failed_operation_leaves_no_trace`, `test_successful_operation_bumps_revision_and_audits_without_secret` |
| Projection publique sans secret, sans mutation | `PublicProjectionTests.*` |
| Aller/retour JSON | `test_json_roundtrip_preserves_model` |

## 7. Créer une variation de scénario (sans créer de ticket)

Le générateur de tickets (à venir) construit un état sain avec
`generate_directory()`, puis applique **une** opération précise pour simuler
la panne — jamais une panne cachée dans l'état sain lui-même. Exemple minimal
runnable (compte verrouillé pour un exercice « compte verrouillé ») :

```python
import time
import sim_ad

now = time.time()
devices = [{'id': 'dev-srv', 'name': 'SRV-FILES', 'role': 'server'},
          {'id': 'dev-pc1', 'name': 'PC-ALICE', 'role': 'client'}]
requester = {'id': 'usr-alice', 'username': 'alice.martin', 'display_name': 'Alice Martin',
            'device_id': 'dev-pc1'}

directory = sim_ad.generate_directory(seed='ticket-123', environment_id='env-abc',
                                      devices=devices, requester=requester, now=now)

# Acteur de confiance construit par le FUTUR serveur (jamais par le navigateur).
admin_actor = {'id': 'svc-ticket-generator', 'environment_id': 'env-abc',
              'permissions': [sim_ad.CAPABILITY_PASSWORDS]}

# Variation : verrouiller le compte de l'apprenant en simulant 3 mauvais
# mots de passe (pas d'opération dédiée « verrouiller » : on réutilise
# authenticate(), qui est la façon dont un vrai verrou se produit).
context = {'environment_id': 'env-abc', 'source_device_id': 'dev-pc1', 'target_device_id': 'dev-srv',
          'network': {'status': 'passed', 'observed_at': now - 1, 'valid_until': now + 30,
                      'evidence': 'icmp_proxy'},
          'directory_service': 'running', 'resource_service': 'running'}
for _ in range(directory['policy']['lockout_threshold']):
    outcome = sim_ad.authenticate(directory, requester['username'], 'mauvais-mot-de-passe', context, now)
    directory = outcome['directory']

# `directory` est maintenant la variation « compte verrouillé » à stocker
# sous workspace.state['directory'] par l'adaptateur. Le ticket annoncé au
# joueur peut dire « Alice n'arrive plus à se connecter » ; la correction
# consiste à appeler apply_operation(directory, 'unlock_user', ...).
assert directory['users'][requester['id']]['locked_until'] is not None
```

Pour les autres variations (`désactivé`, `mot de passe expiré`, `mauvais
groupe`, `accès refusé`), il suffit d'appeler l'opération correspondante
(`set_user_enabled`, `update_user` avec `password_expires_at` dans le passé,
`remove_group_member`...) avec un acteur qui a la capacité requise, exactement
comme le ferait un administrateur.

## 8. Intégration restante (hors périmètre de cette mission)

Tout ce qui suit est décrit section 7 du brief et **n'a pas été codé ici** :

- Routes HTTP sous `/workspace/directory/...`, vérification du jeton local et
  de l'environnement, construction de `actor`/`context` à partir d'une vraie
  session.
- Stockage de `directory` dans `session.json` (ce moteur ne lit/n'écrit aucun
  fichier).
- Migration de `account_enabled`/`read_allowed`/`write_allowed` vers
  l'annuaire — **non touchée** dans cette mission, comme demandé.
- Icône ADUC sur le portable du technicien, fenêtres ADUC, lien entre groupes
  et permissions de `Documents`.
- VPN simulé (profils, authentification, passerelle, ressources autorisées) :
  le moteur traite déjà `context["vpn"]` comme réservé et n'accorde jamais de
  succès sur le seul état « connecté », mais aucune logique VPN n'existe ici.
- Invalidation de session après changement de groupe/mot de passe (le moteur
  note juste que ce n'est pas automatique, à l'adaptateur de la gérer).
- Réplication multi-DC, Kerberos/LDAP complets, GPO, liens d'approbation,
  groupes imbriqués, FTP, terminal IOS, migration des anciennes sessions :
  explicitement hors périmètre v1 (section 3 du brief).

## 9. Fichiers créés

- `web/sim_ad.py`
- `web/test_sim_ad.py`
- `docs/SIM-AD-IMPLEMENTATION.md` (ce fichier)

Aucun fichier existant modifié.


## Addendum d'intégration v0.19

La version intégrée corrige trois points de cette livraison initiale :
`reset_password` renouvelle l'expiration depuis `password_max_age_seconds` ;
`authenticate` incrémente la révision et écrit un audit sans secret pour les
connexions réellement tentées (hors échecs réseau/service) ; la nouvelle fonction
`change_password(directory, username, old_password, new_password, context, now)`
autorise un changement après preuve du mot de passe actuel, y compris expiration
ou changement obligatoire, mais jamais après refus d'identifiants/verrouillage.
Elle retourne `{directory, result}` et ne mute pas l'entrée. Le futur parcours
décrit plus haut est désormais partiellement livré : voir `V019-ANNUAIRE-INTEGRE.md`.
