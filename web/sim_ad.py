"""Moteur d'annuaire AD simulé — bibliothèque pure, sans IO ni interface.

Contrat complet dans docs/SIM-AD-IMPLEMENTATION.md (à lire avant toute
intégration). Résumé des règles qui structurent tout ce fichier :

- Aucune lecture/écriture de fichier ici : l'adaptateur (futur) garde la
  copie renvoyée sous workspace.state['directory'] et la sauvegarde lui-même.
- generate_directory() est seule à devoir être reproductible (seed dédiée,
  jamais hash()/random global). apply_operation()/authenticate() simulent des
  actions « en direct » : leurs identifiants et sels utilisent `secrets`.
- Toute fonction qui mute un état opère sur une COPIE (copy.deepcopy) prise
  avant la moindre validation ; l'objet reçu en paramètre n'est jamais touché,
  y compris quand une erreur est levée.
- Erreurs de contrat (référence invalide, opération inconnue, capacité
  manquante...) : exception DirectoryError (sous-classe de ValueError) avec
  un code stable (.code). Refus « normaux » d'authentification/accès
  (mauvais mot de passe, compte désactivé, ACL...) : pas d'exception, un
  résultat avec status/code/tree, exactement comme le reste du prototype
  (voir web/workspace_model.py::result()).
- Authentification et autorisation sont strictement séparées : evaluate_access
  ne revérifie pas de mot de passe, elle exige une preuve d'authentification
  déjà établie par l'appelant (jamais déclarée par le navigateur).
"""

import copy
import hashlib
import hmac
import secrets

SCHEMA_VERSION = 1

# ─── Politique par défaut (le générateur peut la faire varier plus tard) ─────
DEFAULT_LOCKOUT_THRESHOLD = 3
DEFAULT_LOCKOUT_SECONDS = 300
DEFAULT_PASSWORD_MAX_AGE_SECONDS = 90 * 86400

# Identifiant de formation utilisé pour TOUS les comptes générés par
# generate_directory() (jamais un vrai secret). Documenté dans le markdown :
# le ticket qui s'appuie sur ce moteur peut donc toujours supposer ce mot de
# passe pour l'état sain, avant qu'une opération n'en change un en particulier.
TRAINING_PASSWORD = 'Formation!2026'

_PBKDF2_ITERATIONS = 200_000

# ─── Codes stables (voir docs/SIM-AD-IMPLEMENTATION.md pour le sens exact) ───
UNKNOWN_ENVIRONMENT = 'UNKNOWN_ENVIRONMENT'
PERMISSION_DENIED = 'PERMISSION_DENIED'
UNKNOWN_OPERATION = 'UNKNOWN_OPERATION'
INVALID_PAYLOAD = 'INVALID_PAYLOAD'
DUPLICATE_USERNAME = 'DUPLICATE_USERNAME'
DUPLICATE_GROUP_NAME = 'DUPLICATE_GROUP_NAME'
DUPLICATE_OU_NAME = 'DUPLICATE_OU_NAME'
UNKNOWN_USER = 'UNKNOWN_USER'
UNKNOWN_GROUP = 'UNKNOWN_GROUP'
UNKNOWN_OU = 'UNKNOWN_OU'
UNKNOWN_COMPUTER = 'UNKNOWN_COMPUTER'
OU_CYCLE = 'OU_CYCLE'
IMMUTABLE_FIELD = 'IMMUTABLE_FIELD'
INVALID_SCHEMA = 'INVALID_SCHEMA'

OK = 'OK'
INVALID_CREDENTIALS = 'INVALID_CREDENTIALS'
ACCOUNT_DISABLED = 'ACCOUNT_DISABLED'
ACCOUNT_LOCKED = 'ACCOUNT_LOCKED'
PASSWORD_EXPIRED = 'PASSWORD_EXPIRED'
MUST_CHANGE_PASSWORD = 'MUST_CHANGE_PASSWORD'
NETWORK_UNAVAILABLE = 'NETWORK_UNAVAILABLE'
SERVICE_UNAVAILABLE = 'SERVICE_UNAVAILABLE'
NOT_AUTHENTICATED = 'NOT_AUTHENTICATED'
ACCESS_DENIED = 'ACCESS_DENIED'

CAPABILITY_USERS = 'directory.users.manage'
CAPABILITY_PASSWORDS = 'directory.passwords.reset'
CAPABILITY_GROUPS = 'directory.groups.manage'
CAPABILITY_OUS = 'directory.ous.manage'
CAPABILITY_COMPUTERS = 'directory.computers.manage'


class DirectoryError(ValueError):
    """Erreur de contrat : référence invalide, capacité manquante, opération
    inconnue... Jamais utilisée pour un refus d'authentification/accès normal
    (ceux-là retournent un résultat, voir authenticate()/evaluate_access())."""

    def __init__(self, code, message):
        self.code = code
        super().__init__(f'{code}: {message}')


# ─── Mots de passe : PBKDF2-HMAC-SHA256, sel aléatoire, comparaison constante ─

def _hash_password(password, iterations=_PBKDF2_ITERATIONS):
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, iterations)
    return {'algo': 'pbkdf2_sha256', 'iterations': iterations, 'salt': salt.hex(), 'hash': digest.hex()}


def _verify_password(password, credential):
    try:
        salt = bytes.fromhex(credential['salt'])
        iterations = int(credential['iterations'])
        expected = credential['hash']
    except (KeyError, TypeError, ValueError):
        return False
    digest = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, iterations)
    return hmac.compare_digest(digest.hex(), expected)


# ─── Génération d'identifiants ───────────────────────────────────────────────

def _seeded_rng(seed):
    """RNG dédié à generate_directory() : dérivation SHA-256 documentée par le
    brief, jamais random global ni hash() Python. N'affecte aucun autre flux
    aléatoire du projet (vérifié par test_regression du module de tests)."""
    import random
    digest = hashlib.sha256((str(seed) + ':directory:v1').encode('utf-8')).hexdigest()
    return random.Random(digest)


def _seeded_id(rng, prefix, existing):
    while True:
        candidate = f'{prefix}-{rng.getrandbits(32):08x}'
        if candidate not in existing:
            return candidate


def _live_id(prefix, existing):
    """Identifiants créés par apply_operation (action « en direct », pas de
    reproductibilité demandée ni souhaitée — voir section 4 du brief)."""
    while True:
        candidate = f'{prefix}-{secrets.token_hex(4)}'
        if candidate not in existing:
            return candidate


_FIRST_NAMES = ('Camille', 'Nora', 'Samir', 'Hugo', 'Mina', 'Lucas', 'Chloé', 'Yanis', 'Inès', 'Paul')
_LAST_NAMES = ('Martin', 'Bernard', 'Dubois', 'Rousseau', 'Lefevre', 'Moreau', 'Girard', 'Andre')


def _username(first, last, existing):
    base = f'{first}.{last}'.lower()
    candidate = base
    n = 1
    lowered = {u.lower() for u in existing}
    while candidate.lower() in lowered:
        n += 1
        candidate = f'{base}{n}'
    return candidate


# ─── Arbre de résultat (même forme que web/workspace_model.py::result) ───────

def _node(node_id, label, status, children=()):
    return {'id': node_id, 'label': label, 'status': status, 'children': list(children)}


def _chain(steps):
    """steps : liste de (id, label, status) déjà évaluée dans l'ordre
    réseau -> ... -> droit sur la ressource. Une étape qui suit un statut
    différent de 'passed' devient 'blocked' (non exécutée), jamais réévaluée
    comme si elle avait réussi par défaut. Retourne (tree_racine, statuses)."""
    statuses = []
    parent_ok = True
    for node_id, label, status in steps:
        effective = status if parent_ok else 'blocked'
        statuses.append((node_id, label, effective))
        parent_ok = parent_ok and effective == 'passed'
    children = []
    for node_id, label, status in reversed(statuses):
        children = [_node(node_id, label, status, children)]
    return children[0], statuses


def _check_network(context, environment_id, now):
    """passed/failed uniquement si la preuve est fraîche, dans la bonne
    fenêtre temporelle et dans le bon environnement ; sinon 'unknown' —
    jamais de succès par défaut (section 6 du brief)."""
    if not isinstance(context, dict) or context.get('environment_id') != environment_id:
        return 'unknown'
    network = context.get('network')
    if not isinstance(network, dict):
        return 'unknown'
    status = network.get('status')
    if status not in ('passed', 'failed'):
        return 'unknown'
    observed_at = network.get('observed_at')
    valid_until = network.get('valid_until')
    if not isinstance(observed_at, (int, float)) or not isinstance(valid_until, (int, float)):
        return 'unknown'
    if not (observed_at <= now <= valid_until):
        return 'unknown'
    return status


def _service_status(value):
    return 'passed' if value == 'running' else ('unknown' if value is None else 'failed')


# ─── validate_directory ──────────────────────────────────────────────────────

def validate_directory(directory):
    """Lève DirectoryError au premier problème ; ne modifie rien. Appelée par
    generate_directory() et par apply_operation() avant de rendre une copie."""
    if not isinstance(directory, dict):
        raise DirectoryError(INVALID_SCHEMA, 'annuaire absent ou mal formé')
    if directory.get('schema_version') != SCHEMA_VERSION:
        raise DirectoryError(INVALID_SCHEMA, f'schema_version attendu {SCHEMA_VERSION}')
    for key in ('environment_id', 'domain', 'ous', 'users', 'groups', 'computers', 'policy', 'revision', 'audit'):
        if key not in directory:
            raise DirectoryError(INVALID_SCHEMA, f'clé manquante : {key}')

    ous = directory['ous']
    users = directory['users']
    groups = directory['groups']
    computers = directory['computers']

    # Unicité des noms d'OU : seulement entre sœurs (même parent_id).
    siblings = {}
    for ou_id, ou in ous.items():
        if ou.get('id') != ou_id:
            raise DirectoryError(INVALID_SCHEMA, f'OU {ou_id} : id incohérent')
        parent_id = ou.get('parent_id')
        if parent_id is not None and parent_id not in ous:
            raise DirectoryError(UNKNOWN_OU, f'OU {ou_id} : parent {parent_id} introuvable')
        key = (parent_id, (ou.get('name') or '').lower())
        if key in siblings:
            raise DirectoryError(DUPLICATE_OU_NAME, f'OU en double sous le même parent : {ou.get("name")}')
        siblings[key] = ou_id

    # Cycles d'OU.
    for ou_id in ous:
        seen = set()
        current = ou_id
        while current is not None:
            if current in seen:
                raise DirectoryError(OU_CYCLE, f'cycle détecté à partir de {ou_id}')
            seen.add(current)
            current = ous[current].get('parent_id')

    # Utilisateurs : id cohérent, OU valide, nom de connexion unique (globale).
    seen_usernames = {}
    for user_id, user in users.items():
        if user.get('id') != user_id:
            raise DirectoryError(INVALID_SCHEMA, f'utilisateur {user_id} : id incohérent')
        if user.get('ou_id') not in ous:
            raise DirectoryError(UNKNOWN_OU, f'utilisateur {user_id} : OU introuvable')
        username = (user.get('username') or '').lower()
        if not username:
            raise DirectoryError(INVALID_SCHEMA, f'utilisateur {user_id} : username vide')
        if username in seen_usernames:
            raise DirectoryError(DUPLICATE_USERNAME, f'nom de connexion en double : {user.get("username")}')
        seen_usernames[username] = user_id

    # Groupes : id cohérent, OU valide, nom unique (globale), membres existants.
    seen_group_names = {}
    for group_id, group in groups.items():
        if group.get('id') != group_id:
            raise DirectoryError(INVALID_SCHEMA, f'groupe {group_id} : id incohérent')
        if group.get('ou_id') not in ous:
            raise DirectoryError(UNKNOWN_OU, f'groupe {group_id} : OU introuvable')
        name = (group.get('name') or '').lower()
        if not name:
            raise DirectoryError(INVALID_SCHEMA, f'groupe {group_id} : nom vide')
        if name in seen_group_names:
            raise DirectoryError(DUPLICATE_GROUP_NAME, f'nom de groupe en double : {group.get("name")}')
        seen_group_names[name] = group_id
        for member_id in group.get('member_user_ids', []):
            if member_id not in users:
                raise DirectoryError(UNKNOWN_USER, f'groupe {group_id} : membre {member_id} introuvable')

    # Ordinateurs : id cohérent, OU valide.
    for computer_id, computer in computers.items():
        if computer.get('id') != computer_id:
            raise DirectoryError(INVALID_SCHEMA, f'ordinateur {computer_id} : id incohérent')
        if computer.get('ou_id') not in ous:
            raise DirectoryError(UNKNOWN_OU, f'ordinateur {computer_id} : OU introuvable')


# ─── generate_directory ──────────────────────────────────────────────────────

def generate_directory(seed, environment_id, devices, requester, now):
    """Construit un annuaire sain et reproductible (même seed -> mêmes
    identités/noms/groupes/règles, hors sels privés). Ne modifie ni `devices`
    ni le flux aléatoire global : tout passe par un rng dédié dérivé de seed.
    Aucune panne n'est injectée ici (voir docs pour la variation par
    opération, utilisée par le futur générateur de tickets)."""
    if not isinstance(devices, list):
        raise DirectoryError(INVALID_PAYLOAD, 'devices doit être une liste')
    for device in devices:
        for key in ('id', 'name', 'role'):
            if key not in device:
                raise DirectoryError(INVALID_PAYLOAD, f'device incomplet (clé {key} manquante)')
    for key in ('id', 'username', 'display_name', 'device_id'):
        if key not in requester:
            raise DirectoryError(INVALID_PAYLOAD, f'requester incomplet (clé {key} manquante)')

    rng = _seeded_rng(seed)
    devices = copy.deepcopy(devices)  # jamais muté, mais on isole aussi la sortie de toute alias involontaire

    domain_id = _seeded_id(rng, 'dom', set())
    site_token = rng.choice(('ALB', 'TLS', 'MPL', 'BOR', 'NCY')) + str(rng.randint(10, 99))
    domain = {'id': domain_id, 'dns_name': f'{site_token.lower()}.lab', 'netbios_name': site_token.upper()}

    ous = {}
    root_id = _seeded_id(rng, 'ou', set(ous))
    ous[root_id] = {'id': root_id, 'name': domain['netbios_name'], 'parent_id': None}
    users_ou_id = _seeded_id(rng, 'ou', set(ous))
    ous[users_ou_id] = {'id': users_ou_id, 'name': 'Utilisateurs', 'parent_id': root_id}
    computers_ou_id = _seeded_id(rng, 'ou', set(ous))
    ous[computers_ou_id] = {'id': computers_ou_id, 'name': 'Ordinateurs', 'parent_id': root_id}
    servers_ou_id = _seeded_id(rng, 'ou', set(ous))
    ous[servers_ou_id] = {'id': servers_ou_id, 'name': 'Serveurs', 'parent_id': root_id}

    users = {}
    requester_id = requester['id']
    requester_credential = _hash_password(TRAINING_PASSWORD)
    users[requester_id] = {
        'id': requester_id, 'username': requester['username'], 'display_name': requester['display_name'],
        'ou_id': users_ou_id, 'enabled': True, 'locked_until': None,
        'password_expires_at': now + DEFAULT_PASSWORD_MAX_AGE_SECONDS, 'must_change_password': False,
        'failed_attempts': 0, 'credential': requester_credential,
    }

    colleague_count = rng.randint(2, 4)
    colleague_ids = []
    used_names = {requester['username']}
    for _ in range(colleague_count):
        first = rng.choice(_FIRST_NAMES)
        last = rng.choice(_LAST_NAMES)
        username = _username(first, last, used_names)
        used_names.add(username)
        user_id = _seeded_id(rng, 'usr', set(users))
        users[user_id] = {
            'id': user_id, 'username': username, 'display_name': f'{first} {last}',
            'ou_id': users_ou_id, 'enabled': True, 'locked_until': None,
            'password_expires_at': now + DEFAULT_PASSWORD_MAX_AGE_SECONDS, 'must_change_password': False,
            'failed_attempts': 0, 'credential': _hash_password(TRAINING_PASSWORD),
        }
        colleague_ids.append(user_id)

    groups = {}
    everyone_id = _seeded_id(rng, 'grp', set(groups))
    groups[everyone_id] = {'id': everyone_id, 'name': 'Tous les employés', 'ou_id': users_ou_id,
                           'member_user_ids': [requester_id] + colleague_ids}
    support_id = _seeded_id(rng, 'grp', set(groups))
    support_members = [rng.choice(colleague_ids)] if colleague_ids else []
    groups[support_id] = {'id': support_id, 'name': 'Support Informatique', 'ou_id': users_ou_id,
                          'member_user_ids': support_members}

    computers = {}
    for device in devices:
        ou_id = servers_ou_id if device.get('role') == 'server' else computers_ou_id
        computer_id = _seeded_id(rng, 'cmp', set(computers))
        computers[computer_id] = {'id': computer_id, 'name': device['name'], 'ou_id': ou_id,
                                  'device_id': device['id'], 'domain_joined': True}

    directory = {
        'schema_version': SCHEMA_VERSION,
        'environment_id': environment_id,
        'domain': domain,
        'ous': ous,
        'users': users,
        'groups': groups,
        'computers': computers,
        'policy': {
            'lockout_threshold': DEFAULT_LOCKOUT_THRESHOLD,
            'lockout_seconds': DEFAULT_LOCKOUT_SECONDS,
            'password_max_age_seconds': DEFAULT_PASSWORD_MAX_AGE_SECONDS,
        },
        'revision': 0,
        'audit': [{'at': now, 'operation': 'generate_directory', 'actor_id': None, 'code': OK}],
    }
    validate_directory(directory)
    return directory


# ─── public_directory ────────────────────────────────────────────────────────

def public_directory(directory):
    """Projection sans secret (credential, sels, digests). Ne mute jamais
    `directory` : construit une copie propre champ par champ. L'adaptateur
    décide qui a le droit d'appeler cette fonction (pas ce module)."""
    users = {}
    for user_id, user in directory['users'].items():
        users[user_id] = {k: v for k, v in user.items() if k != 'credential'}
    return {
        'schema_version': directory['schema_version'],
        'environment_id': directory['environment_id'],
        'domain': copy.deepcopy(directory['domain']),
        'ous': copy.deepcopy(directory['ous']),
        'users': users,
        'groups': copy.deepcopy(directory['groups']),
        'computers': copy.deepcopy(directory['computers']),
        'policy': copy.deepcopy(directory['policy']),
        'revision': directory['revision'],
        'audit': copy.deepcopy(directory['audit']),
    }


# ─── apply_operation ─────────────────────────────────────────────────────────

_OPERATION_CAPABILITY = {
    'create_user': CAPABILITY_USERS, 'update_user': CAPABILITY_USERS, 'set_user_enabled': CAPABILITY_USERS,
    'reset_password': CAPABILITY_PASSWORDS, 'unlock_user': CAPABILITY_PASSWORDS,
    'create_group': CAPABILITY_GROUPS, 'add_group_member': CAPABILITY_GROUPS, 'remove_group_member': CAPABILITY_GROUPS,
    'create_ou': CAPABILITY_OUS,
    'join_computer': CAPABILITY_COMPUTERS, 'leave_computer': CAPABILITY_COMPUTERS,
    'move_object': None,  # dépend de object_type, résolu dans _op_move_object
}

_UPDATE_USER_FIELDS = {'display_name', 'username', 'password_expires_at', 'must_change_password'}


def _require(payload, *keys):
    for key in keys:
        if key not in payload:
            raise DirectoryError(INVALID_PAYLOAD, f'champ manquant : {key}')


def _require_capability(actor, capability):
    if capability is not None and capability not in (actor.get('permissions') or ()):
        raise DirectoryError(PERMISSION_DENIED, f'capacité manquante : {capability}')


def _op_create_user(directory, payload, now):
    _require(payload, 'username', 'display_name', 'ou_id')
    if payload['ou_id'] not in directory['ous']:
        raise DirectoryError(UNKNOWN_OU, payload['ou_id'])
    lowered = {u['username'].lower() for u in directory['users'].values()}
    if payload['username'].lower() in lowered:
        raise DirectoryError(DUPLICATE_USERNAME, payload['username'])
    user_id = _live_id('usr', set(directory['users']))
    password_expires_at = payload.get('password_expires_at', now + DEFAULT_PASSWORD_MAX_AGE_SECONDS)
    directory['users'][user_id] = {
        'id': user_id, 'username': payload['username'], 'display_name': payload['display_name'],
        'ou_id': payload['ou_id'], 'enabled': bool(payload.get('enabled', True)), 'locked_until': None,
        'password_expires_at': password_expires_at, 'must_change_password': bool(payload.get('must_change_password', True)),
        'failed_attempts': 0, 'credential': _hash_password(payload.get('initial_password', TRAINING_PASSWORD)),
    }
    return {'status': 'ok', 'code': OK, 'user_id': user_id}


def _op_update_user(directory, payload, now):
    _require(payload, 'user_id')
    user = directory['users'].get(payload['user_id'])
    if user is None:
        raise DirectoryError(UNKNOWN_USER, payload['user_id'])
    unknown_fields = set(payload) - {'user_id'} - _UPDATE_USER_FIELDS
    if unknown_fields:
        raise DirectoryError(IMMUTABLE_FIELD, f'champ non modifiable via update_user : {sorted(unknown_fields)}')
    if 'username' in payload:
        lowered = {u['username'].lower() for uid, u in directory['users'].items() if uid != user['id']}
        if payload['username'].lower() in lowered:
            raise DirectoryError(DUPLICATE_USERNAME, payload['username'])
        user['username'] = payload['username']
    if 'display_name' in payload:
        user['display_name'] = payload['display_name']
    if 'password_expires_at' in payload:
        user['password_expires_at'] = payload['password_expires_at']
    if 'must_change_password' in payload:
        user['must_change_password'] = bool(payload['must_change_password'])
    return {'status': 'ok', 'code': OK, 'user_id': user['id']}


def _op_reset_password(directory, payload, now):
    _require(payload, 'user_id')
    user = directory['users'].get(payload['user_id'])
    if user is None:
        raise DirectoryError(UNKNOWN_USER, payload['user_id'])
    temporary_password = payload.get('temporary_password') or ('Tmp-' + secrets.token_hex(4) + '!')
    user['credential'] = _hash_password(temporary_password)
    user['must_change_password'] = True
    user['failed_attempts'] = 0
    user['locked_until'] = None
    return {'status': 'ok', 'code': OK, 'user_id': user['id'], 'temporary_password': temporary_password}


def _op_unlock_user(directory, payload, now):
    _require(payload, 'user_id')
    user = directory['users'].get(payload['user_id'])
    if user is None:
        raise DirectoryError(UNKNOWN_USER, payload['user_id'])
    user['locked_until'] = None
    user['failed_attempts'] = 0
    return {'status': 'ok', 'code': OK, 'user_id': user['id']}


def _op_set_user_enabled(directory, payload, now):
    _require(payload, 'user_id', 'enabled')
    user = directory['users'].get(payload['user_id'])
    if user is None:
        raise DirectoryError(UNKNOWN_USER, payload['user_id'])
    user['enabled'] = bool(payload['enabled'])
    return {'status': 'ok', 'code': OK, 'user_id': user['id']}


def _op_create_group(directory, payload, now):
    _require(payload, 'name', 'ou_id')
    if payload['ou_id'] not in directory['ous']:
        raise DirectoryError(UNKNOWN_OU, payload['ou_id'])
    lowered = {g['name'].lower() for g in directory['groups'].values()}
    if payload['name'].lower() in lowered:
        raise DirectoryError(DUPLICATE_GROUP_NAME, payload['name'])
    group_id = _live_id('grp', set(directory['groups']))
    directory['groups'][group_id] = {'id': group_id, 'name': payload['name'], 'ou_id': payload['ou_id'],
                                     'member_user_ids': []}
    return {'status': 'ok', 'code': OK, 'group_id': group_id}


def _op_add_group_member(directory, payload, now):
    _require(payload, 'group_id', 'user_id')
    group = directory['groups'].get(payload['group_id'])
    if group is None:
        raise DirectoryError(UNKNOWN_GROUP, payload['group_id'])
    if payload['user_id'] not in directory['users']:
        raise DirectoryError(UNKNOWN_USER, payload['user_id'])
    if payload['user_id'] not in group['member_user_ids']:
        group['member_user_ids'].append(payload['user_id'])
    return {'status': 'ok', 'code': OK, 'group_id': group['id']}


def _op_remove_group_member(directory, payload, now):
    _require(payload, 'group_id', 'user_id')
    group = directory['groups'].get(payload['group_id'])
    if group is None:
        raise DirectoryError(UNKNOWN_GROUP, payload['group_id'])
    if payload['user_id'] in group['member_user_ids']:
        group['member_user_ids'].remove(payload['user_id'])
    return {'status': 'ok', 'code': OK, 'group_id': group['id']}


def _op_create_ou(directory, payload, now):
    _require(payload, 'name')
    parent_id = payload.get('parent_id')
    if parent_id is not None and parent_id not in directory['ous']:
        raise DirectoryError(UNKNOWN_OU, parent_id)
    lowered = {(ou.get('parent_id'), ou['name'].lower()) for ou in directory['ous'].values()}
    if (parent_id, payload['name'].lower()) in lowered:
        raise DirectoryError(DUPLICATE_OU_NAME, payload['name'])
    ou_id = _live_id('ou', set(directory['ous']))
    directory['ous'][ou_id] = {'id': ou_id, 'name': payload['name'], 'parent_id': parent_id}
    return {'status': 'ok', 'code': OK, 'ou_id': ou_id}


def _op_move_object(directory, payload, now, actor):
    _require(payload, 'object_type', 'object_id', 'new_ou_id')
    object_type = payload['object_type']
    capability = {'user': CAPABILITY_USERS, 'group': CAPABILITY_GROUPS, 'computer': CAPABILITY_COMPUTERS}.get(object_type)
    if capability is None:
        raise DirectoryError(INVALID_PAYLOAD, f'object_type inconnu : {object_type}')
    _require_capability(actor, capability)
    if payload['new_ou_id'] not in directory['ous']:
        raise DirectoryError(UNKNOWN_OU, payload['new_ou_id'])
    bucket = {'user': ('users', UNKNOWN_USER), 'group': ('groups', UNKNOWN_GROUP),
             'computer': ('computers', UNKNOWN_COMPUTER)}[object_type]
    collection = directory[bucket[0]]
    obj = collection.get(payload['object_id'])
    if obj is None:
        raise DirectoryError(bucket[1], payload['object_id'])
    obj['ou_id'] = payload['new_ou_id']
    return {'status': 'ok', 'code': OK, 'object_id': obj['id']}


def _op_join_computer(directory, payload, now):
    computer_id = payload.get('computer_id')
    if computer_id is not None:
        computer = directory['computers'].get(computer_id)
        if computer is None:
            raise DirectoryError(UNKNOWN_COMPUTER, computer_id)
        if 'device_id' in payload:
            computer['device_id'] = payload['device_id']
        if 'ou_id' in payload:
            if payload['ou_id'] not in directory['ous']:
                raise DirectoryError(UNKNOWN_OU, payload['ou_id'])
            computer['ou_id'] = payload['ou_id']
        computer['domain_joined'] = True
        return {'status': 'ok', 'code': OK, 'computer_id': computer['id']}
    _require(payload, 'name', 'ou_id', 'device_id')
    if payload['ou_id'] not in directory['ous']:
        raise DirectoryError(UNKNOWN_OU, payload['ou_id'])
    computer_id = _live_id('cmp', set(directory['computers']))
    directory['computers'][computer_id] = {'id': computer_id, 'name': payload['name'], 'ou_id': payload['ou_id'],
                                           'device_id': payload['device_id'], 'domain_joined': True}
    return {'status': 'ok', 'code': OK, 'computer_id': computer_id}


def _op_leave_computer(directory, payload, now):
    _require(payload, 'computer_id')
    computer = directory['computers'].get(payload['computer_id'])
    if computer is None:
        raise DirectoryError(UNKNOWN_COMPUTER, payload['computer_id'])
    computer['domain_joined'] = False
    return {'status': 'ok', 'code': OK, 'computer_id': computer['id']}


_HANDLERS = {
    'create_user': _op_create_user, 'update_user': _op_update_user, 'reset_password': _op_reset_password,
    'unlock_user': _op_unlock_user, 'set_user_enabled': _op_set_user_enabled, 'create_group': _op_create_group,
    'add_group_member': _op_add_group_member, 'remove_group_member': _op_remove_group_member,
    'create_ou': _op_create_ou, 'join_computer': _op_join_computer, 'leave_computer': _op_leave_computer,
}


def apply_operation(directory, operation, payload, actor, now):
    """Retourne {'directory': copie, 'result': résultat}. N'écrit jamais dans
    `directory` : la copie de travail est créée avant toute validation. Une
    opération invalide lève DirectoryError sans aucune mutation ni audit."""
    if operation not in _OPERATION_CAPABILITY:
        raise DirectoryError(UNKNOWN_OPERATION, operation)
    if actor.get('environment_id') != directory.get('environment_id'):
        raise DirectoryError(UNKNOWN_ENVIRONMENT, 'acteur hors environnement')

    new_directory = copy.deepcopy(directory)
    payload = payload or {}

    if operation == 'move_object':
        result = _op_move_object(new_directory, payload, now, actor)
    else:
        _require_capability(actor, _OPERATION_CAPABILITY[operation])
        result = _HANDLERS[operation](new_directory, payload, now)

    new_directory['revision'] = directory['revision'] + 1
    audit_entry = {'at': now, 'operation': operation, 'actor_id': actor.get('id'), 'code': result['code']}
    for key, value in result.items():
        if key not in ('status', 'code', 'temporary_password'):
            audit_entry[key] = value
    new_directory['audit'].append(audit_entry)
    validate_directory(new_directory)
    return {'directory': new_directory, 'result': result}


# ─── authenticate ────────────────────────────────────────────────────────────

def authenticate(directory, username, password, context, now):
    """Retourne {'directory': copie (compteurs/verrou éventuellement à jour),
    'result': {...}}. Un login inconnu ou un mauvais mot de passe renvoient le
    même code générique (INVALID_CREDENTIALS) : jamais de distinction
    observable entre « compte inexistant » et « mauvais mot de passe »."""
    new_directory = copy.deepcopy(directory)
    environment_id = directory['environment_id']

    network_status = _check_network(context, environment_id, now)
    directory_service = _service_status((context or {}).get('directory_service'))
    steps = [('network', 'Connectivité observée', network_status),
            ('directory_service', 'Service d\'annuaire', directory_service)]
    tree, statuses = _chain(steps)
    if statuses[-1][2] != 'passed':
        code = NETWORK_UNAVAILABLE if statuses[0][2] != 'passed' else SERVICE_UNAVAILABLE
        return {'directory': new_directory,
                'result': {'allowed': False, 'status': 'blocked', 'code': code, 'tree': tree}}

    user = next((u for u in new_directory['users'].values() if u['username'].lower() == (username or '').lower()), None)

    def _fail(code, account_status='failed'):
        full_tree, _ = _chain(steps + [('account', 'État du compte', account_status),
                                       ('credential', 'Identifiants', 'failed')])
        return {'directory': new_directory, 'result': {'allowed': False, 'status': 'failed', 'code': code, 'tree': full_tree}}

    if user is None:
        return _fail(INVALID_CREDENTIALS)

    if not user['enabled']:
        return _fail(ACCOUNT_DISABLED)

    if user['locked_until'] is not None:
        if now < user['locked_until']:
            return _fail(ACCOUNT_LOCKED)
        user['locked_until'] = None
        user['failed_attempts'] = 0

    if not _verify_password(password or '', user['credential']):
        user['failed_attempts'] += 1
        policy = new_directory['policy']
        if user['failed_attempts'] >= policy['lockout_threshold']:
            user['locked_until'] = now + policy['lockout_seconds']
        return _fail(INVALID_CREDENTIALS)

    user['failed_attempts'] = 0
    user['locked_until'] = None

    if user['must_change_password']:
        full_tree, _ = _chain(steps + [('account', 'État du compte', 'passed'),
                                       ('credential', 'Identifiants', 'passed'),
                                       ('password_policy', 'Changement de mot de passe requis', 'failed')])
        return {'directory': new_directory,
                'result': {'allowed': False, 'status': 'failed', 'code': MUST_CHANGE_PASSWORD, 'tree': full_tree}}

    if user['password_expires_at'] is not None and now >= user['password_expires_at']:
        full_tree, _ = _chain(steps + [('account', 'État du compte', 'passed'),
                                       ('credential', 'Identifiants', 'passed'),
                                       ('password_policy', 'Mot de passe expiré', 'failed')])
        return {'directory': new_directory,
                'result': {'allowed': False, 'status': 'failed', 'code': PASSWORD_EXPIRED, 'tree': full_tree}}

    full_tree, _ = _chain(steps + [('account', 'État du compte', 'passed'), ('credential', 'Identifiants', 'passed'),
                                   ('authenticated', 'Authentifié', 'passed')])
    return {'directory': new_directory,
            'result': {'allowed': True, 'status': 'passed', 'code': OK, 'tree': full_tree, 'user_id': user['id']}}


# ─── evaluate_user (diagnostic support, sans mot de passe) ──────────────────

def evaluate_user(directory, user_id, context, now):
    """Lecture seule : ne mute jamais `directory`, ne retourne pas de copie
    (rien à copier). user_id inconnu = erreur de contrat (DirectoryError),
    pas un refus normal : c'est l'appelant qui a résolu cette identité."""
    user = directory['users'].get(user_id)
    if user is None:
        raise DirectoryError(UNKNOWN_USER, user_id)

    environment_id = directory['environment_id']
    network_status = _check_network(context, environment_id, now)
    directory_service = _service_status((context or {}).get('directory_service'))
    steps = [('network', 'Connectivité observée', network_status),
            ('directory_service', 'Service d\'annuaire', directory_service)]
    tree, statuses = _chain(steps)
    if statuses[-1][2] != 'passed':
        code = NETWORK_UNAVAILABLE if statuses[0][2] != 'passed' else SERVICE_UNAVAILABLE
        return {'allowed': False, 'status': 'blocked', 'code': code, 'tree': tree, 'account': None}

    locked = user['locked_until'] is not None and now < user['locked_until']
    password_expired = user['password_expires_at'] is not None and now >= user['password_expires_at']
    account = {'enabled': user['enabled'], 'locked': locked, 'locked_until': user['locked_until'],
              'password_expired': password_expired, 'must_change_password': user['must_change_password']}
    allowed = user['enabled'] and not locked
    if not user['enabled']:
        code = ACCOUNT_DISABLED
    elif locked:
        code = ACCOUNT_LOCKED
    elif user['must_change_password']:
        code = MUST_CHANGE_PASSWORD
    elif password_expired:
        code = PASSWORD_EXPIRED
    else:
        code = OK
    account_status = 'passed' if allowed else 'failed'
    full_tree, _ = _chain(steps + [('account', 'État du compte', account_status)])
    return {'allowed': allowed, 'status': account_status if allowed else 'failed', 'code': code,
           'tree': full_tree, 'account': account}


# ─── evaluate_access ─────────────────────────────────────────────────────────

def evaluate_access(directory, user_id, resource, action, context, now):
    """Lecture seule. N'authentifie jamais : exige une preuve d'authentification
    déjà établie (context['authentication']) pour CE user_id et CET
    environnement — jamais une déclaration brute du navigateur."""
    if action not in ('read', 'write'):
        raise DirectoryError(INVALID_PAYLOAD, f'action inconnue : {action}')
    for key in ('id', 'server_device_id', 'allowed_user_ids', 'allowed_group_ids'):
        if key not in resource:
            raise DirectoryError(INVALID_PAYLOAD, f'resource incomplète (clé {key} manquante)')
    user = directory['users'].get(user_id)
    if user is None:
        raise DirectoryError(UNKNOWN_USER, user_id)

    environment_id = directory['environment_id']
    network_status = _check_network(context, environment_id, now)
    # Vérification défensive supplémentaire (l'adaptateur vérifie déjà la
    # provenance source/cible avant d'appeler le moteur, section 6 du brief) :
    # une cible qui ne correspond pas à la ressource ne peut jamais réussir.
    if (context or {}).get('target_device_id') != resource['server_device_id']:
        network_status = 'unknown' if network_status == 'passed' else network_status

    resource_service = _service_status((context or {}).get('resource_service'))
    directory_service = _service_status((context or {}).get('directory_service'))
    steps = [('network', 'Connectivité observée', network_status),
            ('resource_service', 'Service de ressource', resource_service),
            ('directory_service', 'Service d\'annuaire', directory_service)]
    tree, statuses = _chain(steps)
    if statuses[-1][2] != 'passed':
        code = (NETWORK_UNAVAILABLE if statuses[0][2] != 'passed' else SERVICE_UNAVAILABLE)
        return {'allowed': False, 'status': 'blocked', 'code': code, 'tree': tree}

    locked = user['locked_until'] is not None and now < user['locked_until']
    account_ok = user['enabled'] and not locked
    account_status = 'passed' if account_ok else 'failed'
    if not account_ok:
        code = ACCOUNT_DISABLED if not user['enabled'] else ACCOUNT_LOCKED
        full_tree, _ = _chain(steps + [('account', 'État du compte', account_status)])
        return {'allowed': False, 'status': 'failed', 'code': code, 'tree': full_tree}

    authentication = (context or {}).get('authentication') or {}
    authenticated = authentication.get('user_id') == user_id and authentication.get('status') == 'authenticated'
    auth_status = 'passed' if authenticated else 'failed'
    if not authenticated:
        full_tree, _ = _chain(steps + [('account', 'État du compte', account_status),
                                       ('authentication', 'Authentification', auth_status)])
        return {'allowed': False, 'status': 'failed', 'code': NOT_AUTHENTICATED, 'tree': full_tree}

    allowed_users = set(resource['allowed_user_ids'].get(action, []))
    allowed_groups = set(resource['allowed_group_ids'].get(action, []))
    member_of = {g['id'] for g in directory['groups'].values() if user_id in g['member_user_ids']}
    granted = user_id in allowed_users or bool(allowed_groups & member_of)
    right_status = 'passed' if granted else 'failed'
    full_tree, _ = _chain(steps + [('account', 'État du compte', account_status),
                                   ('authentication', 'Authentification', auth_status),
                                   ('resource_right', 'Droit sur la ressource', right_status)])
    return {'allowed': granted, 'status': right_status, 'code': OK if granted else ACCESS_DENIED, 'tree': full_tree}
