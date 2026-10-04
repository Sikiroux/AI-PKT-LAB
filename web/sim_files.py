"""Moteur de partages de fichiers simulés — bibliothèque pure, sans IO.

Contrat complet dans docs/SIM-FILES-IMPLEMENTATION.md (à lire avant toute
intégration). Résumé des règles qui structurent tout ce fichier, cohérent
avec web/sim_ad.py (même philosophie, module totalement indépendant — pas
d'import croisé, pas de deuxième annuaire) :

- Aucune lecture/écriture de fichier réel, aucun réseau, aucune commande
  système. Simulation pédagogique d'un partage SMB, pas un serveur SMB.
- generate_file_service() est seule à devoir être reproductible (seed dédiée,
  jamais hash()/random global). apply_operation() simule des actions
  « en direct » (secrets, pas la seed).
- Toute fonction qui mute un état opère sur une COPIE (copy.deepcopy) prise
  avant la moindre validation ; l'objet reçu en paramètre n'est jamais touché,
  y compris quand une erreur est levée.
- Erreurs de contrat (requête mal formée, référence inconnue, capacité
  manquante...) : exception FileServiceError (sous-classe de ValueError) avec
  un code stable (.code). Refus « normaux » d'accès (réseau indisponible,
  partage désactivé, droit manquant, quota...) : pas d'exception, un résultat
  avec allowed/status/code/tree, jamais un succès par défaut sur une valeur
  manquante ou ambiguë.
- Identités, état de compte et groupes viennent de l'extérieur (moteur AD
  sim_ad, via l'adaptateur) : ce module ne les recalcule jamais, il les reçoit
  déjà évalués dans context['identity'].
"""

import copy
import hashlib
import math
import secrets

SCHEMA_VERSION = 1

MAX_FILE_BYTES = 64 * 1024
MAX_FILES = 100
MAX_SHARES = 10

ACTIONS = ('list', 'read', 'write', 'delete')
ACL_ACTIONS = ('list', 'read', 'write', 'delete')
QUOTA_MODES = ('off', 'hard', 'soft')

# ─── Codes « contrat » (toujours une exception FileServiceError) ────────────
INVALID_SCHEMA = 'INVALID_SCHEMA'
INVALID_REQUEST = 'INVALID_REQUEST'
UNKNOWN_ENVIRONMENT = 'UNKNOWN_ENVIRONMENT'
PERMISSION_DENIED = 'PERMISSION_DENIED'
UNKNOWN_OPERATION = 'UNKNOWN_OPERATION'
UNKNOWN_SHARE = 'UNKNOWN_SHARE'
UNKNOWN_FILE = 'UNKNOWN_FILE'
UNKNOWN_PRINCIPAL = 'UNKNOWN_PRINCIPAL'

# ─── Codes « résultat » (jamais levés, renvoyés dans result/tree) ───────────
OK = 'OK'
INVALID_CONTEXT = 'INVALID_CONTEXT'
NAME_UNRESOLVED = 'NAME_UNRESOLVED'
NETWORK_DOWN = 'NETWORK_DOWN'
OBSERVATION_UNKNOWN = 'OBSERVATION_UNKNOWN'
TCP445_BLOCKED = 'TCP445_BLOCKED'
SERVICE_STOPPED = 'SERVICE_STOPPED'
SHARE_NOT_FOUND = 'SHARE_NOT_FOUND'
SHARE_DISABLED = 'SHARE_DISABLED'
ACCOUNT_UNAVAILABLE = 'ACCOUNT_UNAVAILABLE'
NOT_AUTHENTICATED = 'NOT_AUTHENTICATED'
SHARE_ACCESS_DENIED = 'SHARE_ACCESS_DENIED'
FILESYSTEM_ACCESS_DENIED = 'FILESYSTEM_ACCESS_DENIED'
FILE_NOT_FOUND = 'FILE_NOT_FOUND'
NAME_CONFLICT = 'NAME_CONFLICT'
FILE_READ_ONLY = 'FILE_READ_ONLY'
DISK_FULL = 'DISK_FULL'
QUOTA_EXCEEDED = 'QUOTA_EXCEEDED'
QUOTA_WARNING = 'QUOTA_WARNING'
REVISION_CONFLICT = 'REVISION_CONFLICT'

CAPABILITY_FILES = 'files.manage'


class FileServiceError(ValueError):
    """Erreur de contrat : requête mal formée, référence inconnue, capacité
    manquante... Jamais utilisée pour un refus d'accès normal (ceux-là
    retournent un résultat, voir evaluate_access()/perform_file_action())."""

    def __init__(self, code, message):
        self.code = code
        super().__init__(f'{code}: {message}')


# ─── Identifiants ────────────────────────────────────────────────────────────

def _seeded_rng(seed):
    import random
    digest = hashlib.sha256((str(seed) + ':files:v1').encode('utf-8')).hexdigest()
    return random.Random(digest)


def _seeded_id(rng, prefix, existing):
    while True:
        candidate = f'{prefix}-{rng.getrandbits(32):08x}'
        if candidate not in existing:
            return candidate


def _live_id(prefix, existing):
    while True:
        candidate = f'{prefix}-{secrets.token_hex(4)}'
        if candidate not in existing:
            return candidate


_FORBIDDEN_NAME_CHARS = frozenset({'/', '\\'} | {chr(c) for c in range(0, 32)})


def _valid_file_name(name):
    if not isinstance(name, str) or not name.strip():
        return False
    if '..' in name:
        return False
    return not any(ch in _FORBIDDEN_NAME_CHARS for ch in name)


def _is_strict_bool(value):
    return isinstance(value, bool)


def _is_strict_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


def _is_finite_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _file_size(content):
    return len(content.encode('utf-8'))


# ─── Arbre de diagnostic : {stage, status, children} ─────────────────────────

def _node(stage, status, children=()):
    return {'stage': stage, 'status': status, 'children': list(children)}


def _chain(steps):
    """steps : liste de (stage, status) dans l'ordre pédagogique. Un statut
    différent de 'passed' bloque (status='blocked', jamais réévalué) toutes
    les étapes suivantes. Retourne (tree_racine, liste_des_statuts_effectifs)."""
    statuses = []
    parent_ok = True
    for stage, status in steps:
        effective = status if parent_ok else 'blocked'
        statuses.append((stage, effective))
        parent_ok = parent_ok and effective == 'passed'
    children = []
    for stage, status in reversed(statuses):
        children = [_node(stage, status, children)]
    return children[0], statuses


# ─── validate_file_service ───────────────────────────────────────────────────

def validate_file_service(service):
    if not isinstance(service, dict):
        raise FileServiceError(INVALID_SCHEMA, 'service absent ou mal formé')
    if service.get('schema_version') != SCHEMA_VERSION:
        raise FileServiceError(INVALID_SCHEMA, f'schema_version attendu {SCHEMA_VERSION}')
    for key in ('environment_id', 'server', 'principal_catalog', 'service_status', 'firewall_tcp445_allowed',
               'volume', 'shares', 'files', 'revision', 'audit'):
        if key not in service:
            raise FileServiceError(INVALID_SCHEMA, f'clé manquante : {key}')

    server = service['server']
    for key in ('id', 'name', 'ip', 'dns_name'):
        if not isinstance(server.get(key), str) or not server[key]:
            raise FileServiceError(INVALID_SCHEMA, f'server.{key} invalide')
    # server.id (identité de l'appareil) et environment_id (identité de session)
    # sont deux identifiants distincts : rien n'exige qu'ils soient égaux. Voir
    # §3 de la doc pour les deux contrôles séparés appliqués côté contexte.

    if service['service_status'] not in ('running', 'stopped'):
        raise FileServiceError(INVALID_SCHEMA, 'service_status invalide')
    if not _is_strict_bool(service['firewall_tcp445_allowed']):
        raise FileServiceError(INVALID_SCHEMA, 'firewall_tcp445_allowed doit être un booléen strict')

    catalog = service['principal_catalog']
    for key in ('user_ids', 'group_ids'):
        if not isinstance(catalog.get(key), list) or not all(isinstance(v, str) for v in catalog[key]):
            raise FileServiceError(INVALID_SCHEMA, f'principal_catalog.{key} invalide')
    known_users = set(catalog['user_ids'])
    known_groups = set(catalog['group_ids'])

    volume = service['volume']
    if not _is_strict_int(volume.get('capacity_bytes')) or volume['capacity_bytes'] <= 0:
        raise FileServiceError(INVALID_SCHEMA, 'volume.capacity_bytes doit être un entier strictement positif')
    if not _is_strict_int(volume.get('background_used_bytes')) or volume['background_used_bytes'] < 0:
        raise FileServiceError(INVALID_SCHEMA, 'volume.background_used_bytes doit être un entier non négatif')

    shares = service['shares']
    if len(shares) > MAX_SHARES:
        raise FileServiceError(INVALID_SCHEMA, f'plus de {MAX_SHARES} partages')
    for share_id, share in shares.items():
        if share.get('id') != share_id:
            raise FileServiceError(INVALID_SCHEMA, f'partage {share_id} : id incohérent')
        if not isinstance(share.get('name'), str) or not share['name'].strip():
            raise FileServiceError(INVALID_SCHEMA, f'partage {share_id} : nom vide')
        if not _is_strict_bool(share.get('enabled')) or not _is_strict_bool(share.get('hidden')):
            raise FileServiceError(INVALID_SCHEMA, f'partage {share_id} : enabled/hidden doivent être des booléens stricts')
        for layer_name in ('share_acl', 'folder_acl'):
            acl = share.get(layer_name)
            if not isinstance(acl, dict) or set(acl) != set(ACL_ACTIONS):
                raise FileServiceError(INVALID_SCHEMA, f'partage {share_id} : {layer_name} doit couvrir {ACL_ACTIONS}')
            for action, grant in acl.items():
                if not isinstance(grant, dict) or set(grant) != {'user_ids', 'group_ids'}:
                    raise FileServiceError(INVALID_SCHEMA, f'partage {share_id} : {layer_name}.{action} mal formé')
                for uid in grant['user_ids']:
                    if uid not in known_users:
                        raise FileServiceError(UNKNOWN_PRINCIPAL, f'utilisateur {uid} absent du catalogue')
                for gid in grant['group_ids']:
                    if gid not in known_groups:
                        raise FileServiceError(UNKNOWN_PRINCIPAL, f'groupe {gid} absent du catalogue')
        quota = share.get('quota')
        if not isinstance(quota, dict) or quota.get('mode') not in QUOTA_MODES:
            raise FileServiceError(INVALID_SCHEMA, f'partage {share_id} : quota.mode invalide')
        limit = quota.get('limit_bytes')
        if quota['mode'] == 'off':
            if limit is not None:
                raise FileServiceError(INVALID_SCHEMA, f'partage {share_id} : quota off exige limit_bytes=null')
        else:
            if not _is_strict_int(limit) or limit <= 0:
                raise FileServiceError(INVALID_SCHEMA, f'partage {share_id} : limit_bytes doit être positif')

    files = service['files']
    if len(files) > MAX_FILES:
        raise FileServiceError(INVALID_SCHEMA, f'plus de {MAX_FILES} fichiers')
    names_by_share = {}
    for file_id, file_ in files.items():
        if file_.get('id') != file_id:
            raise FileServiceError(INVALID_SCHEMA, f'fichier {file_id} : id incohérent')
        if file_.get('share_id') not in shares:
            raise FileServiceError(UNKNOWN_SHARE, f'fichier {file_id} : partage introuvable')
        if not _valid_file_name(file_.get('name')):
            raise FileServiceError(INVALID_SCHEMA, f'fichier {file_id} : nom invalide')
        key = (file_['share_id'], file_['name'].lower())
        if key in names_by_share:
            raise FileServiceError(INVALID_SCHEMA, f'fichier {file_id} : nom en double dans le partage')
        names_by_share[key] = file_id
        if not isinstance(file_.get('content'), str):
            raise FileServiceError(INVALID_SCHEMA, f'fichier {file_id} : contenu doit être une chaîne')
        if _file_size(file_['content']) > MAX_FILE_BYTES:
            raise FileServiceError(INVALID_SCHEMA, f'fichier {file_id} : dépasse {MAX_FILE_BYTES} octets')
        if not _is_strict_bool(file_.get('read_only')):
            raise FileServiceError(INVALID_SCHEMA, f'fichier {file_id} : read_only doit être un booléen strict')
        if not _is_finite_number(file_.get('updated_at')):
            raise FileServiceError(INVALID_SCHEMA, f'fichier {file_id} : updated_at invalide')

    if not _is_strict_int(service['revision']) or service['revision'] < 0:
        raise FileServiceError(INVALID_SCHEMA, 'revision doit être un entier non négatif')


# ─── Occupation (volume partagé vs quota par partage, §4 du brief) ───────────

def _share_used_bytes(service, share_id, exclude_file_id=None):
    return sum(_file_size(f['content']) for f in service['files'].values()
              if f['share_id'] == share_id and f['id'] != exclude_file_id)


def _volume_used_bytes(service, exclude_file_id=None):
    return service['volume']['background_used_bytes'] + sum(
        _file_size(f['content']) for f in service['files'].values() if f['id'] != exclude_file_id)


# ─── generate_file_service ───────────────────────────────────────────────────

_SHARE_NAMES = ('Documents', 'Public', 'Projets', 'Archives', 'Comptabilité', 'Support')
_FILE_NAMES = ('Procedure.txt', 'Notes.txt', 'Budget.txt', 'Lisez-moi.txt', 'Compte-rendu.txt',
              'Contacts.txt', 'Planning.txt', 'Historique.txt')
_FILE_SENTENCES = (
    "Document de formation genere automatiquement, contenu fictif.",
    "Rappel : ceci est un environnement de simulation pedagogique.",
    "Aucune donnee reelle n'est stockee dans ce fichier.",
    "Procedure interne de test, a ne pas utiliser en production.",
)


def generate_file_service(seed, environment_id, server, principals, now):
    """Construit un service de partage sain et reproductible. N'invente aucun
    identifiant de principal : seuls ceux fournis dans `principals` peuvent
    apparaître dans les ACL. Aucune panne cachée (service en marche, pare-feu
    ouvert, partages activés, quotas non dépassés)."""
    for key in ('id', 'name', 'ip', 'dns_name'):
        if not isinstance(server.get(key), str) or not server[key]:
            raise FileServiceError(INVALID_REQUEST, f'server.{key} invalide')
    user_ids = list((principals or {}).get('user_ids') or [])
    group_ids = list((principals or {}).get('group_ids') or [])
    if not user_ids:
        raise FileServiceError(INVALID_REQUEST, 'au moins un utilisateur doit être fourni')
    if not all(isinstance(u, str) for u in user_ids) or not all(isinstance(g, str) for g in group_ids):
        raise FileServiceError(INVALID_REQUEST, 'principals doit contenir des listes de chaînes')

    rng = _seeded_rng(seed)
    first_user = user_ids[0]

    share_count = rng.randint(2, 4)
    share_names = list(_SHARE_NAMES)
    rng.shuffle(share_names)
    share_names = share_names[:share_count]

    shares = {}
    files = {}
    file_pool = list(_FILE_NAMES)
    for index, name in enumerate(share_names):
        share_id = _seeded_id(rng, 'shr', set(shares))
        quota_mode = rng.choice(QUOTA_MODES)
        rng.shuffle(file_pool)
        file_count = rng.randint(1, 3)
        chosen_names = file_pool[:file_count]
        share_files = []
        for file_name in chosen_names:
            file_id = _seeded_id(rng, 'file', set(files))
            content = rng.choice(_FILE_SENTENCES)
            files[file_id] = {'id': file_id, 'share_id': share_id, 'name': file_name, 'content': content,
                              'read_only': False, 'updated_at': now}
            share_files.append(file_id)

        empty_acl = {action: {'user_ids': [], 'group_ids': []} for action in ACL_ACTIONS}
        share_acl = copy.deepcopy(empty_acl)
        folder_acl = copy.deepcopy(empty_acl)
        if index == 0:
            # Le premier utilisateur fourni peut faire les 4 actions sur le premier partage.
            for action in ACL_ACTIONS:
                share_acl[action]['user_ids'].append(first_user)
                folder_acl[action]['user_ids'].append(first_user)

        used = sum(_file_size(files[fid]['content']) for fid in share_files)
        if quota_mode == 'off':
            quota = {'mode': 'off', 'limit_bytes': None}
        else:
            headroom = rng.randint(2048, 8192)
            quota = {'mode': quota_mode, 'limit_bytes': used + headroom}
        shares[share_id] = {'id': share_id, 'name': name, 'enabled': True, 'hidden': False,
                            'share_acl': share_acl, 'folder_acl': folder_acl, 'quota': quota}

    background_used_bytes = rng.randint(1024, 4096)
    total_file_bytes = sum(_file_size(f['content']) for f in files.values())
    headroom = rng.randint(4096, 16384)
    capacity_bytes = background_used_bytes + total_file_bytes + headroom

    service = {
        'schema_version': SCHEMA_VERSION,
        'environment_id': environment_id,
        'server': dict(server),
        'principal_catalog': {'user_ids': sorted(set(user_ids)), 'group_ids': sorted(set(group_ids))},
        'service_status': 'running',
        'firewall_tcp445_allowed': True,
        'volume': {'capacity_bytes': capacity_bytes, 'background_used_bytes': background_used_bytes},
        'shares': shares,
        'files': files,
        'revision': 0,
        'audit': [{'at': now, 'operation': 'generate_file_service', 'actor_id': None, 'code': OK}],
    }
    validate_file_service(service)
    return service


# ─── public_file_service ──────────────────────────────────────────────────────

def public_file_service(service, actor):
    """Projection pour console d'administration (capacité files.manage).
    Refuse l'acteur non autorisé (exception, pas un résultat : c'est un appel
    d'administration, pas une action utilisateur normale). Jamais de contenu
    de fichier ni de contexte d'authentification dans la sortie."""
    if actor.get('environment_id') != service['environment_id']:
        raise FileServiceError(UNKNOWN_ENVIRONMENT, 'acteur hors environnement')
    if CAPABILITY_FILES not in (actor.get('permissions') or ()):
        raise FileServiceError(PERMISSION_DENIED, 'capacité manquante : ' + CAPABILITY_FILES)

    files_meta = {}
    for file_id, f in service['files'].items():
        files_meta[file_id] = {'id': f['id'], 'share_id': f['share_id'], 'name': f['name'],
                               'read_only': f['read_only'], 'updated_at': f['updated_at'],
                               'size_bytes': _file_size(f['content'])}
    shares_view = {}
    for share_id, share in service['shares'].items():
        shares_view[share_id] = copy.deepcopy(share)
        shares_view[share_id]['used_bytes'] = _share_used_bytes(service, share_id)

    return {
        'schema_version': service['schema_version'],
        'environment_id': service['environment_id'],
        'server': copy.deepcopy(service['server']),
        'principal_catalog': copy.deepcopy(service['principal_catalog']),
        'service_status': service['service_status'],
        'firewall_tcp445_allowed': service['firewall_tcp445_allowed'],
        'volume': {**service['volume'], 'used_bytes': _volume_used_bytes(service)},
        'shares': shares_view,
        'files': files_meta,
        'revision': service['revision'],
        'audit': copy.deepcopy(service['audit']),
    }


# ─── Validation de la requête (forme) et du contexte (contenu) ──────────────

def _validate_request_shape(request):
    if not isinstance(request, dict):
        raise FileServiceError(INVALID_REQUEST, 'request doit être un dict')
    action = request.get('action')
    if action not in ACTIONS:
        raise FileServiceError(INVALID_REQUEST, f'action inconnue : {action}')
    if not isinstance(request.get('share_id'), str) or not request['share_id']:
        raise FileServiceError(INVALID_REQUEST, 'share_id requis')
    if action in ('read', 'delete'):
        if not isinstance(request.get('file_id'), str) or not request['file_id']:
            raise FileServiceError(INVALID_REQUEST, 'file_id requis pour ' + action)
    if action == 'write':
        if 'file_id' in request and request['file_id'] is not None:
            if not isinstance(request['file_id'], str):
                raise FileServiceError(INVALID_REQUEST, 'file_id doit être une chaîne')
        else:
            if not _valid_file_name(request.get('name')):
                raise FileServiceError(INVALID_REQUEST, 'name invalide pour une création')
        if not isinstance(request.get('content'), str):
            raise FileServiceError(INVALID_REQUEST, 'content doit être une chaîne')
        if _file_size(request['content']) > MAX_FILE_BYTES:
            raise FileServiceError(INVALID_REQUEST, f'content dépasse {MAX_FILE_BYTES} octets')
    if action in ('write', 'delete'):
        if 'expected_revision' not in request or request['expected_revision'] is None:
            raise FileServiceError(INVALID_REQUEST, 'expected_revision requis pour ' + action)
        if not _is_strict_int(request['expected_revision']):
            raise FileServiceError(INVALID_REQUEST, 'expected_revision doit être un entier')


def _context_scope_ok(service, context):
    if not isinstance(context, dict):
        return False
    if context.get('environment_id') != service['environment_id']:
        return False
    if context.get('target_device_id') != service['server']['id']:
        return False
    if not isinstance(context.get('source_device_id'), str) or not context['source_device_id']:
        return False
    if context.get('address_mode') not in ('ip', 'name'):
        return False
    identity = context.get('identity')
    if not isinstance(identity, dict):
        return False
    if not isinstance(identity.get('user_id'), str) or not identity['user_id']:
        return False
    if not isinstance(identity.get('group_ids'), list) or not all(isinstance(g, str) for g in identity['group_ids']):
        return False
    if not _is_strict_bool(identity.get('account_allowed')) or not _is_strict_bool(identity.get('authentication_valid')):
        return False
    # Le moteur ne prouve aucune appartenance, mais il exige un user_id et des
    # group_ids CONNUS du catalogue : une identité qui en référence un absent
    # ne peut pas obtenir un accès via un octroi de groupe qu'elle n'a pas
    # réellement (contrat section 5 du brief).
    catalog = service['principal_catalog']
    if identity['user_id'] not in catalog['user_ids']:
        return False
    if not set(identity['group_ids']).issubset(set(catalog['group_ids'])):
        return False
    return True


def _name_resolution_status(context, server):
    """'unknown' pour une preuve absente/périmée/future/invalide ou un statut
    explicitement 'unknown' : on ne sait rien, ce n'est pas une panne prouvée.
    'failed' uniquement pour un échec frais explicitement observé, ou une
    résolution fraîche vers une adresse différente de server.ip."""
    if context.get('address_mode') != 'name':
        return None  # étape non applicable, omise de l'arbre
    resolution = context.get('name_resolution')
    if not isinstance(resolution, dict):
        return 'unknown'
    status = resolution.get('status')
    if status not in ('resolved', 'failed', 'unknown'):
        return 'unknown'
    observed_at, valid_until = resolution.get('observed_at'), resolution.get('valid_until')
    if not _is_finite_number(observed_at) or not _is_finite_number(valid_until) or valid_until < observed_at:
        return 'unknown'
    now = context['_now']  # injecté par l'appelant pour cette vérification
    if not (observed_at <= now <= valid_until):
        return 'unknown'
    if status == 'unknown':
        return 'unknown'
    if status == 'failed':
        return 'failed'
    if resolution.get('resolved_ip') != server['ip']:
        return 'failed'
    return 'passed'


def _network_status(context, server, now):
    network = context.get('network')
    if not isinstance(network, dict):
        return 'unknown'
    status = network.get('status')
    if status not in ('up', 'down', 'unknown'):
        return 'unknown'
    if network.get('source_device_id') != context.get('source_device_id'):
        return 'unknown'
    if network.get('target_device_id') != context.get('target_device_id'):
        return 'unknown'
    observed_at, valid_until = network.get('observed_at'), network.get('valid_until')
    if not _is_finite_number(observed_at) or not _is_finite_number(valid_until) or valid_until < observed_at:
        return 'unknown'
    if not (observed_at <= now <= valid_until):
        return 'unknown'
    return status


# ─── evaluate_access ──────────────────────────────────────────────────────────

def evaluate_access(service, request, context, now):
    """Évaluation pure (ne mute jamais `service`) de la chaîne pédagogique
    décrite section 6 du brief. Ne réalise aucune action : perform_file_action
    l'appelle d'abord, puis agit seulement si allowed=True.

    Toutes les étapes pertinentes pour cette `action` sont TOUJOURS ajoutées à
    `steps`, même quand une étape antérieure a déjà échoué (avec des valeurs
    sûres par défaut, jamais une erreur) : c'est _chain() qui les convertit en
    'blocked' le cas échéant. Conforme à la section 6 du brief : l'étage
    suivant un échec est 'blocked', jamais simplement absent de l'arbre."""
    _validate_request_shape(request)
    action = request['action']
    server = service['server']
    codes = {}
    steps = []

    scope_ok = _context_scope_ok(service, context)
    steps.append(('scope', 'passed' if scope_ok else 'unknown'))
    codes['scope'] = INVALID_CONTEXT

    ctx = dict(context, _now=now) if scope_ok else {}
    identity = ctx.get('identity') or {}

    name_status = _name_resolution_status(ctx, server) if scope_ok else None
    if name_status is not None:
        steps.append(('name_resolution', name_status))
        codes['name_resolution'] = NAME_UNRESOLVED if name_status == 'failed' else OBSERVATION_UNKNOWN

    net_status = _network_status(context, server, now) if isinstance(context, dict) else 'unknown'
    net_effective = 'passed' if net_status == 'up' else ('failed' if net_status == 'down' else 'unknown')
    steps.append(('network', net_effective))
    codes['network'] = NETWORK_DOWN if net_status == 'down' else OBSERVATION_UNKNOWN

    steps.append(('firewall', 'passed' if service['firewall_tcp445_allowed'] else 'failed'))
    codes['firewall'] = TCP445_BLOCKED

    steps.append(('service', 'passed' if service['service_status'] == 'running' else 'failed'))
    codes['service'] = SERVICE_STOPPED

    share = service['shares'].get(request['share_id'])
    steps.append(('share_found', 'passed' if share is not None else 'failed'))
    codes['share_found'] = SHARE_NOT_FOUND

    steps.append(('share_enabled', 'passed' if (share and share['enabled']) else 'failed'))
    codes['share_enabled'] = SHARE_DISABLED

    steps.append(('account', 'passed' if identity.get('account_allowed') else 'failed'))
    codes['account'] = ACCOUNT_UNAVAILABLE

    steps.append(('authentication', 'passed' if identity.get('authentication_valid') else 'failed'))
    codes['authentication'] = NOT_AUTHENTICATED

    member_of = set(identity.get('group_ids') or [])

    def _granted(acl_layer):
        grant = acl_layer[action]
        return identity.get('user_id') in grant['user_ids'] or bool(member_of & set(grant['group_ids']))

    steps.append(('share_permission', 'passed' if (share and _granted(share['share_acl'])) else 'failed'))
    codes['share_permission'] = SHARE_ACCESS_DENIED

    steps.append(('filesystem_permission', 'passed' if (share and _granted(share['folder_acl'])) else 'failed'))
    codes['filesystem_permission'] = FILESYSTEM_ACCESS_DENIED

    requested_file_id = request.get('file_id')
    raw_target_file = service['files'].get(requested_file_id) if requested_file_id else None
    # Un file_id valide mais appartenant à un AUTRE partage que request['share_id']
    # ne doit jamais être traité comme trouvé ici : sans ce filtre, les ACL
    # vérifiées plus haut sont celles du partage demandé alors que le fichier
    # réellement lu/modifié/supprimé serait celui d'un partage différent.
    target_file = (raw_target_file if raw_target_file is not None
                  and raw_target_file['share_id'] == request['share_id'] else None)
    creating = action == 'write' and not requested_file_id

    if action in ('read', 'delete'):
        steps.append(('file_lookup', 'passed' if target_file is not None else 'failed'))
        codes['file_lookup'] = FILE_NOT_FOUND
    elif action == 'write':
        if creating:
            name_taken = bool(share) and any(
                f['share_id'] == share['id'] and f['name'].lower() == request['name'].lower()
                for f in service['files'].values())
            steps.append(('file_lookup', 'failed' if name_taken else 'passed'))
            codes['file_lookup'] = NAME_CONFLICT
        else:
            steps.append(('file_lookup', 'passed' if target_file is not None else 'failed'))
            codes['file_lookup'] = FILE_NOT_FOUND

    if action in ('delete', 'write') and not creating:
        steps.append(('read_only', 'failed' if (target_file and target_file['read_only']) else 'passed'))
        codes['read_only'] = FILE_READ_ONLY

    quota_warning = False
    if action == 'write':
        new_size = _file_size(request['content'])
        old_size = _file_size(target_file['content']) if target_file is not None else 0
        delta = new_size - old_size
        if delta > 0:
            exclude = target_file['id'] if target_file is not None else None
            new_volume_used = _volume_used_bytes(service, exclude_file_id=exclude) + new_size
            capacity_ok = new_volume_used <= service['volume']['capacity_bytes']
            steps.append(('capacity', 'passed' if capacity_ok else 'failed'))
            codes['capacity'] = DISK_FULL
            if share is not None:
                new_share_used = _share_used_bytes(service, share['id'], exclude_file_id=exclude) + new_size
                quota = share['quota']
                quota_exceeded_hard = quota['mode'] == 'hard' and new_share_used > quota['limit_bytes']
                steps.append(('quota', 'failed' if quota_exceeded_hard else 'passed'))
                codes['quota'] = QUOTA_EXCEEDED
                quota_warning = quota['mode'] == 'soft' and new_share_used > (quota['limit_bytes'] or 0)

    tree, statuses = _chain(steps)
    allowed = all(status == 'passed' for _, status in statuses)
    evidence = (context.get('network') or {}).get('evidence') if isinstance(context, dict) else None
    if allowed:
        return {'allowed': True, 'status': 'passed', 'code': QUOTA_WARNING if quota_warning else OK,
               'tree': tree, 'evidence': evidence}
    first_stage, first_status = next((s, st) for s, st in statuses if st != 'passed')
    overall_status = first_status if first_status == 'unknown' else 'failed'
    return {'allowed': False, 'status': overall_status, 'code': codes[first_stage], 'tree': tree, 'evidence': evidence}


# ─── perform_file_action ──────────────────────────────────────────────────────

def perform_file_action(service, request, context, now):
    """Retourne {'service': copie, 'result': {...}}. Appelle evaluate_access
    sur la MÊME requête/contexte (pas de chemin de contournement) ; n'agit que
    si allowed=True. Pour write/delete, vérifie ensuite expected_revision
    (contrôle de concurrence optimiste, hors de l'arbre pédagogique : ce n'est
    pas une question de droit mais de coordination serveur)."""
    outcome = evaluate_access(service, request, context, now)
    new_service = copy.deepcopy(service)
    if not outcome['allowed']:
        return {'service': new_service, 'result': {**outcome, 'data': None}}

    action = request['action']
    share_id = request['share_id']

    if action in ('write', 'delete') and request['expected_revision'] != service['revision']:
        conflict = {'allowed': False, 'status': 'failed', 'code': REVISION_CONFLICT,
                   'tree': outcome['tree'], 'evidence': outcome['evidence']}
        return {'service': new_service, 'result': {**conflict, 'data': None}}

    data = None
    if action == 'list':
        data = [{'id': f['id'], 'name': f['name'], 'read_only': f['read_only'], 'updated_at': f['updated_at'],
                'size_bytes': _file_size(f['content'])}
               for f in new_service['files'].values() if f['share_id'] == share_id]
    elif action == 'read':
        f = new_service['files'][request['file_id']]
        data = {'id': f['id'], 'name': f['name'], 'content': f['content'], 'read_only': f['read_only'],
               'updated_at': f['updated_at']}
    elif action == 'write':
        if request.get('file_id'):
            f = new_service['files'][request['file_id']]
            f['content'] = request['content']
            f['updated_at'] = now
            file_id = f['id']
        else:
            file_id = _live_id('file', set(new_service['files']))
            new_service['files'][file_id] = {'id': file_id, 'share_id': share_id, 'name': request['name'],
                                             'content': request['content'], 'read_only': False, 'updated_at': now}
        new_service['revision'] += 1
        new_service['audit'].append({'at': now, 'actor_id': context['identity']['user_id'], 'operation': 'write',
                                     'share_id': share_id, 'file_id': file_id, 'code': outcome['code']})
        data = {'id': file_id}
        validate_file_service(new_service)
    elif action == 'delete':
        file_id = request['file_id']
        del new_service['files'][file_id]
        new_service['revision'] += 1
        new_service['audit'].append({'at': now, 'actor_id': context['identity']['user_id'], 'operation': 'delete',
                                     'share_id': share_id, 'file_id': file_id, 'code': OK})
        data = {'id': file_id}
        validate_file_service(new_service)

    return {'service': new_service, 'result': {**outcome, 'data': data}}


# ─── apply_operation (administration) ─────────────────────────────────────────

def _require(payload, *keys):
    for key in keys:
        if key not in payload:
            raise FileServiceError(INVALID_REQUEST, f'champ manquant : {key}')


def _op_set_service_status(service, payload, now):
    _require(payload, 'status')
    if payload['status'] not in ('running', 'stopped'):
        raise FileServiceError(INVALID_REQUEST, 'status invalide')
    service['service_status'] = payload['status']
    return {'status': 'ok', 'code': OK}


def _op_set_firewall(service, payload, now):
    _require(payload, 'allowed')
    if not _is_strict_bool(payload['allowed']):
        raise FileServiceError(INVALID_REQUEST, 'allowed doit être un booléen strict')
    service['firewall_tcp445_allowed'] = payload['allowed']
    return {'status': 'ok', 'code': OK}


def _op_set_share_enabled(service, payload, now):
    _require(payload, 'share_id', 'enabled')
    share = service['shares'].get(payload['share_id'])
    if share is None:
        raise FileServiceError(UNKNOWN_SHARE, payload['share_id'])
    if not _is_strict_bool(payload['enabled']):
        raise FileServiceError(INVALID_REQUEST, 'enabled doit être un booléen strict')
    share['enabled'] = payload['enabled']
    return {'status': 'ok', 'code': OK, 'share_id': share['id']}


def _op_rename_share(service, payload, now):
    _require(payload, 'share_id', 'name')
    share = service['shares'].get(payload['share_id'])
    if share is None:
        raise FileServiceError(UNKNOWN_SHARE, payload['share_id'])
    if not isinstance(payload['name'], str) or not payload['name'].strip():
        raise FileServiceError(INVALID_REQUEST, 'name invalide')
    share['name'] = payload['name']
    return {'status': 'ok', 'code': OK, 'share_id': share['id']}


def _op_set_acl(service, payload, now):
    _require(payload, 'share_id', 'layer', 'action', 'user_ids', 'group_ids')
    share = service['shares'].get(payload['share_id'])
    if share is None:
        raise FileServiceError(UNKNOWN_SHARE, payload['share_id'])
    if payload['layer'] not in ('share_acl', 'folder_acl'):
        raise FileServiceError(INVALID_REQUEST, 'layer invalide')
    if payload['action'] not in ACL_ACTIONS:
        raise FileServiceError(INVALID_REQUEST, 'action invalide')
    known_users = set(service['principal_catalog']['user_ids'])
    known_groups = set(service['principal_catalog']['group_ids'])
    user_ids, group_ids = payload['user_ids'], payload['group_ids']
    if not isinstance(user_ids, list) or not isinstance(group_ids, list):
        raise FileServiceError(INVALID_REQUEST, 'user_ids/group_ids doivent être des listes')
    for uid in user_ids:
        if uid not in known_users:
            raise FileServiceError(UNKNOWN_PRINCIPAL, uid)
    for gid in group_ids:
        if gid not in known_groups:
            raise FileServiceError(UNKNOWN_PRINCIPAL, gid)
    # Remplace ENTIEREMENT la couche pour cette action (pas un ajout partiel).
    share[payload['layer']][payload['action']] = {'user_ids': list(user_ids), 'group_ids': list(group_ids)}
    return {'status': 'ok', 'code': OK, 'share_id': share['id']}


def _op_set_quota(service, payload, now):
    _require(payload, 'share_id', 'mode')
    share = service['shares'].get(payload['share_id'])
    if share is None:
        raise FileServiceError(UNKNOWN_SHARE, payload['share_id'])
    mode = payload['mode']
    if mode not in QUOTA_MODES:
        raise FileServiceError(INVALID_REQUEST, 'mode invalide')
    limit = payload.get('limit_bytes')
    if mode == 'off':
        if limit is not None:
            raise FileServiceError(INVALID_REQUEST, 'quota off exige limit_bytes=null')
    else:
        if not _is_strict_int(limit) or limit <= 0:
            raise FileServiceError(INVALID_REQUEST, 'limit_bytes doit être un entier strictement positif')
    share['quota'] = {'mode': mode, 'limit_bytes': limit}
    return {'status': 'ok', 'code': OK, 'share_id': share['id']}


def _op_set_volume_capacity(service, payload, now):
    _require(payload, 'capacity_bytes')
    if not _is_strict_int(payload['capacity_bytes']) or payload['capacity_bytes'] <= 0:
        raise FileServiceError(INVALID_REQUEST, 'capacity_bytes doit être un entier strictement positif')
    service['volume']['capacity_bytes'] = payload['capacity_bytes']
    return {'status': 'ok', 'code': OK}


def _op_set_background_usage(service, payload, now):
    _require(payload, 'background_used_bytes')
    if not _is_strict_int(payload['background_used_bytes']) or payload['background_used_bytes'] < 0:
        raise FileServiceError(INVALID_REQUEST, 'background_used_bytes doit être un entier non négatif')
    service['volume']['background_used_bytes'] = payload['background_used_bytes']
    return {'status': 'ok', 'code': OK}


def _op_set_file_read_only(service, payload, now):
    _require(payload, 'file_id', 'read_only')
    file_ = service['files'].get(payload['file_id'])
    if file_ is None:
        raise FileServiceError(UNKNOWN_FILE, payload['file_id'])
    if not _is_strict_bool(payload['read_only']):
        raise FileServiceError(INVALID_REQUEST, 'read_only doit être un booléen strict')
    file_['read_only'] = payload['read_only']
    return {'status': 'ok', 'code': OK, 'file_id': file_['id']}


_HANDLERS = {
    'set_service_status': _op_set_service_status, 'set_firewall': _op_set_firewall,
    'set_share_enabled': _op_set_share_enabled, 'rename_share': _op_rename_share, 'set_acl': _op_set_acl,
    'set_quota': _op_set_quota, 'set_volume_capacity': _op_set_volume_capacity,
    'set_background_usage': _op_set_background_usage, 'set_file_read_only': _op_set_file_read_only,
}


def apply_operation(service, operation, payload, actor, now):
    """Retourne {'service': copie, 'result': {...}}. N'écrit jamais dans
    `service` : la copie de travail est créée avant toute validation. Une
    opération invalide lève FileServiceError sans aucune mutation ni audit."""
    if operation not in _HANDLERS:
        raise FileServiceError(UNKNOWN_OPERATION, operation)
    if actor.get('environment_id') != service.get('environment_id'):
        raise FileServiceError(UNKNOWN_ENVIRONMENT, 'acteur hors environnement')
    if CAPABILITY_FILES not in (actor.get('permissions') or ()):
        raise FileServiceError(PERMISSION_DENIED, 'capacité manquante : ' + CAPABILITY_FILES)

    new_service = copy.deepcopy(service)
    validate_file_service(new_service)  # garde-fou : état de départ toujours cohérent
    payload = payload or {}
    result = _HANDLERS[operation](new_service, payload, now)

    new_service['revision'] = service['revision'] + 1
    audit_entry = {'at': now, 'operation': operation, 'actor_id': actor.get('id'), 'code': result['code']}
    for key, value in result.items():
        if key not in ('status', 'code'):
            audit_entry[key] = value
    new_service['audit'].append(audit_entry)
    validate_file_service(new_service)
    return {'service': new_service, 'result': result}

