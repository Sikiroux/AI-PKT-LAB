"""Moteur DNS pédagogique simulé — bibliothèque pure, sans IO.

Contrat complet dans docs/SIM-DNS-IMPLEMENTATION.md (à lire avant toute
intégration). Résumé des règles qui structurent ce fichier, cohérent avec
web/sim_files.py et web/sim_ad.py (même philosophie, module totalement
indépendant — pas d'import croisé, pas de second annuaire ni de second
moteur de fichiers) :

- Aucune résolution DNS réelle, aucun socket, aucune commande système.
  Simulation pédagogique d'un serveur DNS pour UNE zone interne, pas un
  serveur DNS complet ni une implémentation des RFC.
- generate_dns() est seule à devoir être reproductible (seed dédiée, jamais
  hash()/random global). apply_operation()/flush_cache() simulent des
  actions « en direct » (secrets, pas la seed).
- Toute fonction qui mute un état opère sur une COPIE (copy.deepcopy) prise
  avant la moindre validation ; l'objet reçu en paramètre n'est jamais
  touché, y compris quand une erreur est levée ou qu'une requête est
  refusée.
- Erreurs de contrat (requête mal formée, référence inconnue, capacité
  manquante...) : exception DNSServiceError (sous-classe de ValueError) avec
  un code stable (.code). Refus/réponses « normaux » (NXDOMAIN, réseau
  indisponible, service arrêté, configuration client absente...) : pas
  d'exception, un résultat avec status/code/dns_rcode/tree.
- Le DNS ne fait AUCUNE vérification d'identité ou d'authentification :
  c'est volontaire (section 5 du brief ne fournit pas de bloc identity dans
  le contexte). Les comptes/groupes restent entièrement gérés par sim_ad ;
  les droits sur les fichiers restent entièrement gérés par sim_files. Ce
  module ne modélise qu'un sous-ensemble hostname déclaré (voir docs), pas
  une résolution DNS universelle.
"""

import copy
import hashlib
import ipaddress
import math
import re
import secrets

SCHEMA_VERSION = 1

MAX_CLIENTS = 100
MAX_RECORDS = 1000
MAX_CACHE_PER_CLIENT = 200
MAX_TTL = 86400
MAX_CNAME_HOPS = 8

RECORD_TYPES = ('A', 'AAAA', 'CNAME')
QUERY_TYPES = ('A', 'AAAA', 'CNAME')

# ─── Codes « contrat » (toujours une exception DNSServiceError) ─────────────
INVALID_SCHEMA = 'INVALID_SCHEMA'
INVALID_REQUEST = 'INVALID_REQUEST'
UNKNOWN_ENVIRONMENT = 'UNKNOWN_ENVIRONMENT'
PERMISSION_DENIED = 'PERMISSION_DENIED'
UNKNOWN_OPERATION = 'UNKNOWN_OPERATION'
UNKNOWN_CLIENT = 'UNKNOWN_CLIENT'
UNKNOWN_RECORD = 'UNKNOWN_RECORD'
RECORD_CONFLICT = 'RECORD_CONFLICT'
RECORD_OUT_OF_ZONE = 'RECORD_OUT_OF_ZONE'

# ─── Codes « résultat » (jamais levés, renvoyés dans result/tree) ───────────
OK = 'OK'
NODATA = 'NODATA'
NXDOMAIN = 'NXDOMAIN'
CNAME_LOOP = 'CNAME_LOOP'
CNAME_DEPTH = 'CNAME_DEPTH'
REFUSED = 'REFUSED'
INVALID_NAME = 'INVALID_NAME'
INVALID_CONTEXT = 'INVALID_CONTEXT'
DNS_NOT_CONFIGURED = 'DNS_NOT_CONFIGURED'
DNS_SERVER_UNMODELED = 'DNS_SERVER_UNMODELED'
NETWORK_DOWN = 'NETWORK_DOWN'
OBSERVATION_UNKNOWN = 'OBSERVATION_UNKNOWN'
DNS_TRANSPORT_BLOCKED = 'DNS_TRANSPORT_BLOCKED'
DNS_SERVICE_STOPPED = 'DNS_SERVICE_STOPPED'

# dns_rcode associé à chaque code de résultat ; None = aucun échange DNS n'a
# eu lieu (pas de réponse protocolaire à rapporter).
_DNS_RCODE_BY_CODE = {
    OK: 'NOERROR', NODATA: 'NOERROR', NXDOMAIN: 'NXDOMAIN',
    CNAME_LOOP: 'SERVFAIL', CNAME_DEPTH: 'SERVFAIL', REFUSED: 'REFUSED',
}

# status global associé à chaque code de résultat. 'resolved' = la couche DNS
# a produit une réponse définitive (même négative) ; 'failed' = la résolution
# n'a pas pu aboutir pour une raison connue ; 'unknown' = on ne sait pas
# (preuve absente/périmée/incohérente). Voir §3 de la doc.
_STATUS_BY_CODE = {
    OK: 'resolved', NODATA: 'resolved', NXDOMAIN: 'resolved',
    REFUSED: 'failed', CNAME_LOOP: 'failed', CNAME_DEPTH: 'failed',
    INVALID_NAME: 'failed', NETWORK_DOWN: 'failed',
    DNS_TRANSPORT_BLOCKED: 'failed', DNS_SERVICE_STOPPED: 'failed',
    DNS_NOT_CONFIGURED: 'failed',
    INVALID_CONTEXT: 'unknown', OBSERVATION_UNKNOWN: 'unknown',
    DNS_SERVER_UNMODELED: 'unknown',
}

# Codes dont le résultat est mis en cache (positif ou négatif). Tout le reste
# (pannes de transport/réseau/service, requêtes hors périmètre) n'est jamais
# caché : voir §6 du brief.
_CACHEABLE_CODES = frozenset({OK, NXDOMAIN, NODATA})

CAPABILITY_DNS_MANAGE = 'dns.manage'
CAPABILITY_DNS_FLUSH_OWN = 'dns.flush_own'


class DNSServiceError(ValueError):
    """Erreur de contrat : requête mal formée, référence inconnue, capacité
    manquante... Jamais utilisée pour un refus/réponse normal (ceux-là
    retournent un résultat, voir resolve())."""

    def __init__(self, code, message):
        self.code = code
        super().__init__(f'{code}: {message}')


# ─── Identifiants ────────────────────────────────────────────────────────────

def _seeded_rng(seed):
    import random
    digest = hashlib.sha256((str(seed) + ':dns:v1').encode('utf-8')).hexdigest()
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


# ─── Types stricts ───────────────────────────────────────────────────────────

def _is_strict_bool(value):
    return isinstance(value, bool)


def _is_strict_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


def _is_finite_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _is_valid_ttl(value):
    return _is_strict_int(value) and 0 <= value <= MAX_TTL


def _valid_ipv4(value):
    if not isinstance(value, str):
        return False
    try:
        ipaddress.IPv4Address(value)
        return True
    except ValueError:
        return False


def _valid_ipv6(value):
    if not isinstance(value, str):
        return False
    try:
        ipaddress.IPv6Address(value)
        return True
    except ValueError:
        return False


def _valid_ip_any(value):
    return _valid_ipv4(value) or _valid_ipv6(value)


# ─── Noms d'hôtes : sous-ensemble hostname déclaré (voir §3 de la doc) ──────
# ASCII, labels 1-63 caractères lettres/chiffres/tiret, sans tiret
# initial/final, FQDN max 253 caractères (hors point final optionnel). Pas
# d'underscore, joker, URL, espace ou chemin UNC. Pas une règle DNS
# universelle : un sous-ensemble volontairement restreint pour ce modèle v1.
_LABEL_RE = re.compile(r'^[A-Za-z0-9]([A-Za-z0-9-]{0,61}[A-Za-z0-9])?$')


def _valid_hostname(name):
    if not isinstance(name, str) or not name:
        return False
    if not name.isascii():
        return False
    if any(ch.isspace() for ch in name):
        return False
    if any(ch in name for ch in ('*', '_', '/', '\\', ':')):
        return False
    core = name[:-1] if name.endswith('.') else name
    if not core or len(core) > 253:
        return False
    labels = core.split('.')
    return all(_LABEL_RE.match(label) for label in labels)


def _normalize_fqdn(name):
    core = name[:-1] if name.endswith('.') else name
    return core.lower()


def _in_zone(fqdn, zone):
    fqdn = fqdn.lower()
    zone = zone.lower()
    return fqdn == zone or fqdn.endswith('.' + zone)


# ─── Arbre de diagnostic : {stage,label,status,children} ────────────────────

_STAGE_LABELS = {
    'scope': 'Périmètre et requête',
    'query': 'Nom demandé',
    'cache': 'Cache local du client',
    'resolver_config': 'Configuration du résolveur client',
    'network': 'Connectivité réseau observée',
    'transport': 'Transport DNS simulé',
    'service': 'Service DNS',
    'records': 'Enregistrements et chaîne',
}
_CACHE_HIT_LABEL = 'non nécessaire : réponse en cache'


def _node(stage, status, label=None, children=()):
    return {'stage': stage, 'label': label or _STAGE_LABELS.get(stage, stage),
           'status': status, 'children': list(children)}


def _chain(steps):
    """steps : liste de (stage, status[, label]) dans l'ordre pédagogique. Un
    statut différent de 'passed' bloque (status='blocked', jamais réévalué)
    toutes les étapes suivantes. Retourne (tree_racine, liste_des_statuts)."""
    statuses = []
    parent_ok = True
    for step in steps:
        stage, status = step[0], step[1]
        label = step[2] if len(step) > 2 else None
        effective = status if parent_ok else 'blocked'
        statuses.append((stage, effective, label))
        parent_ok = parent_ok and effective == 'passed'
    children = []
    for stage, status, label in reversed(statuses):
        children = [_node(stage, status, label, children)]
    return children[0], [(s, st) for s, st, _ in statuses]


def _forced_tree(leading_passed_stages, forced_label=_CACHE_HIT_LABEL):
    """Construit un arbre où `leading_passed_stages` sont 'passed' (dans
    l'ordre) puis TOUTES les étapes restantes du pipeline sont 'blocked' avec
    un libellé explicite — utilisé uniquement pour la branche cache_hit, où
    une chaîne stricte all(passed) ne convient pas (voir §5 du brief : la
    réponse peut être resolved sans qu'aucune étape serveur n'ait été
    consultée)."""
    all_stages = ('scope', 'query', 'cache', 'resolver_config', 'network', 'transport', 'service', 'records')
    steps = []
    for stage in all_stages:
        if stage in leading_passed_stages:
            steps.append((stage, 'passed'))
        else:
            steps.append((stage, 'blocked', forced_label))
    children = []
    for stage, status, *rest in reversed(steps):
        label = rest[0] if rest else None
        children = [_node(stage, status, label, children)]
    return children[0]


# ─── validate_dns ────────────────────────────────────────────────────────────

def validate_dns(service):
    if not isinstance(service, dict):
        raise DNSServiceError(INVALID_SCHEMA, 'service absent ou mal formé')
    if service.get('schema_version') != SCHEMA_VERSION:
        raise DNSServiceError(INVALID_SCHEMA, f'schema_version attendu {SCHEMA_VERSION}')
    for key in ('environment_id', 'server', 'clients', 'records', 'service_status', 'transport_allowed',
               'negative_ttl', 'cache', 'revision', 'audit'):
        if key not in service:
            raise DNSServiceError(INVALID_SCHEMA, f'clé manquante : {key}')
    if not isinstance(service['environment_id'], str) or not service['environment_id']:
        raise DNSServiceError(INVALID_SCHEMA, 'environment_id invalide')

    server = service['server']
    for key in ('id', 'name', 'ip', 'zone'):
        if not isinstance(server.get(key), str) or not server[key]:
            raise DNSServiceError(INVALID_SCHEMA, f'server.{key} invalide')
    if not _valid_ip_any(server['ip']):
        raise DNSServiceError(INVALID_SCHEMA, 'server.ip invalide')
    if not _valid_hostname(server['zone']):
        raise DNSServiceError(INVALID_SCHEMA, 'server.zone invalide')
    # server.id (identité de l'appareil) et environment_id (identité de
    # session) sont deux identités distinctes : rien n'exige leur égalité
    # (cf. le correctif analogue sur sim_files, voir §3 de la doc).

    if service['service_status'] not in ('running', 'stopped'):
        raise DNSServiceError(INVALID_SCHEMA, 'service_status invalide')
    if not _is_strict_bool(service['transport_allowed']):
        raise DNSServiceError(INVALID_SCHEMA, 'transport_allowed doit être un booléen strict')
    if not _is_valid_ttl(service['negative_ttl']):
        raise DNSServiceError(INVALID_SCHEMA, 'negative_ttl doit être un entier entre 0 et ' + str(MAX_TTL))

    clients = service['clients']
    if len(clients) > MAX_CLIENTS:
        raise DNSServiceError(INVALID_SCHEMA, f'plus de {MAX_CLIENTS} clients')
    for client_id, client in clients.items():
        if client.get('id') != client_id:
            raise DNSServiceError(INVALID_SCHEMA, f'client {client_id} : id incohérent')
        if not isinstance(client.get('name'), str) or not client['name']:
            raise DNSServiceError(INVALID_SCHEMA, f'client {client_id} : nom invalide')
        dns_ip = client.get('dns_server_ip')
        if dns_ip is not None and not _valid_ip_any(dns_ip):
            raise DNSServiceError(INVALID_SCHEMA, f'client {client_id} : dns_server_ip invalide')
        suffix = client.get('search_suffix')
        if not isinstance(suffix, str):
            raise DNSServiceError(INVALID_SCHEMA, f'client {client_id} : search_suffix doit être une chaîne')
        if suffix and not _valid_hostname(suffix):
            raise DNSServiceError(INVALID_SCHEMA, f'client {client_id} : search_suffix invalide')

    records = service['records']
    if len(records) > MAX_RECORDS:
        raise DNSServiceError(INVALID_SCHEMA, f'plus de {MAX_RECORDS} enregistrements')
    by_name_type = {}
    by_name_enabled = {}
    for record_id, record in records.items():
        if record.get('id') != record_id:
            raise DNSServiceError(INVALID_SCHEMA, f'enregistrement {record_id} : id incohérent')
        if record.get('type') not in RECORD_TYPES:
            raise DNSServiceError(INVALID_SCHEMA, f'enregistrement {record_id} : type invalide')
        name = record.get('name')
        if not _valid_hostname(name) or _normalize_fqdn(name) != name:
            raise DNSServiceError(INVALID_SCHEMA, f'enregistrement {record_id} : name invalide ou non normalisé')
        if not _in_zone(name, server['zone']):
            raise DNSServiceError(RECORD_OUT_OF_ZONE, f'enregistrement {record_id} : name hors zone')
        value = record.get('value')
        rtype = record['type']
        if rtype == 'A' and not _valid_ipv4(value):
            raise DNSServiceError(INVALID_SCHEMA, f'enregistrement {record_id} : value IPv4 invalide')
        if rtype == 'AAAA' and not _valid_ipv6(value):
            raise DNSServiceError(INVALID_SCHEMA, f'enregistrement {record_id} : value IPv6 invalide')
        if rtype == 'CNAME':
            if not _valid_hostname(value) or _normalize_fqdn(value) != value:
                raise DNSServiceError(INVALID_SCHEMA, f'enregistrement {record_id} : cible CNAME invalide')
            if not _in_zone(value, server['zone']):
                raise DNSServiceError(RECORD_OUT_OF_ZONE, f'enregistrement {record_id} : cible CNAME hors zone')
        if not _is_valid_ttl(record.get('ttl')):
            raise DNSServiceError(INVALID_SCHEMA, f'enregistrement {record_id} : ttl invalide')
        if not _is_strict_bool(record.get('enabled')):
            raise DNSServiceError(INVALID_SCHEMA, f'enregistrement {record_id} : enabled doit être un booléen strict')

        key_type = (name, rtype)
        if record['enabled']:
            if key_type in by_name_type:
                raise DNSServiceError(INVALID_SCHEMA, f'enregistrement {record_id} : doublon actif nom/type')
            by_name_type[key_type] = record_id
            by_name_enabled.setdefault(name, set()).add(rtype)

    for name, types in by_name_enabled.items():
        if 'CNAME' in types and len(types) > 1:
            raise DNSServiceError(INVALID_SCHEMA, f'{name} : CNAME actif coexiste avec A/AAAA actif')

    cache = service['cache']
    for client_id, entries in cache.items():
        if client_id not in clients:
            raise DNSServiceError(INVALID_SCHEMA, f'cache : client {client_id} inconnu')
        if len(entries) > MAX_CACHE_PER_CLIENT:
            raise DNSServiceError(INVALID_SCHEMA, f'cache : plus de {MAX_CACHE_PER_CLIENT} entrées pour {client_id}')
        for cache_key, entry in entries.items():
            if not isinstance(cache_key, str) or not cache_key:
                raise DNSServiceError(INVALID_SCHEMA, 'cache : clé invalide')
            for field in ('response', 'cached_at', 'expires_at', 'provenance'):
                if field not in entry:
                    raise DNSServiceError(INVALID_SCHEMA, f'cache {cache_key} : champ manquant {field}')
            if not _is_finite_number(entry['cached_at']) or not _is_finite_number(entry['expires_at']):
                raise DNSServiceError(INVALID_SCHEMA, f'cache {cache_key} : horodatage invalide')
            if entry['expires_at'] < entry['cached_at']:
                raise DNSServiceError(INVALID_SCHEMA, f'cache {cache_key} : expires_at < cached_at')

    if not _is_strict_int(service['revision']) or service['revision'] < 0:
        raise DNSServiceError(INVALID_SCHEMA, 'revision doit être un entier non négatif')


# ─── generate_dns ────────────────────────────────────────────────────────────

_ALIAS_POOL = ('www', 'intranet', 'portail', 'acces')
_TTL_POOL = (300, 600, 3600)
_NEGATIVE_TTL_POOL = (60, 120, 300)


def generate_dns(seed, environment_id, server, clients, resources, now):
    """Construit un service DNS sain et reproductible pour UNE zone interne.
    N'invente aucun nom/adresse de ressource ni de client : seuls ceux
    fournis peuvent apparaître. Exige des clients déjà configurés sainement
    (dns_server_ip == server.ip, search_suffix vide ou égal à la zone) —
    c'est une validation du contrat d'entrée, pas une correction silencieuse
    (voir §3 de la doc)."""
    if not isinstance(environment_id, str) or not environment_id:
        raise DNSServiceError(INVALID_REQUEST, 'environment_id invalide')
    for key in ('id', 'name', 'ip', 'zone'):
        if not isinstance(server.get(key), str) or not server[key]:
            raise DNSServiceError(INVALID_REQUEST, f'server.{key} invalide')
    if not _valid_ip_any(server['ip']):
        raise DNSServiceError(INVALID_REQUEST, 'server.ip invalide')
    if not _valid_hostname(server['zone']):
        raise DNSServiceError(INVALID_REQUEST, 'server.zone invalide')
    zone = _normalize_fqdn(server['zone'])

    clients = list(clients or [])
    if not clients:
        raise DNSServiceError(INVALID_REQUEST, 'au moins un client doit être fourni')
    resources = list(resources or [])
    if not resources:
        raise DNSServiceError(INVALID_REQUEST, 'au moins une ressource doit être fournie')

    client_states = {}
    for c in clients:
        for key in ('id', 'name'):
            if not isinstance(c.get(key), str) or not c[key]:
                raise DNSServiceError(INVALID_REQUEST, f'client.{key} invalide')
        if c['id'] in client_states:
            raise DNSServiceError(INVALID_REQUEST, f'client {c["id"]} dupliqué')
        if c.get('dns_server_ip') != server['ip']:
            raise DNSServiceError(INVALID_REQUEST, f'client {c["id"]} : dns_server_ip doit être server.ip pour une génération saine')
        suffix = c.get('search_suffix', '')
        if not isinstance(suffix, str) or suffix not in ('', zone):
            raise DNSServiceError(INVALID_REQUEST, f'client {c["id"]} : search_suffix doit être vide ou égal à la zone')
        client_states[c['id']] = {'id': c['id'], 'name': c['name'], 'dns_server_ip': c['dns_server_ip'],
                                  'search_suffix': suffix}

    rng = _seeded_rng(seed)
    records = {}
    resource_names = []
    for r in resources:
        for key in ('id', 'dns_name'):
            if not isinstance(r.get(key), str) or not r[key]:
                raise DNSServiceError(INVALID_REQUEST, f'resource.{key} invalide')
        dns_name = _normalize_fqdn(r['dns_name'])
        if not _valid_hostname(dns_name):
            raise DNSServiceError(INVALID_REQUEST, f'resource {r["id"]} : dns_name invalide')
        if not _in_zone(dns_name, zone):
            raise DNSServiceError(INVALID_REQUEST, f'resource {r["id"]} : dns_name hors zone')
        ipv4 = r.get('ipv4')
        ipv6 = r.get('ipv6')
        if ipv4 is not None and not _valid_ipv4(ipv4):
            raise DNSServiceError(INVALID_REQUEST, f'resource {r["id"]} : ipv4 invalide')
        if ipv6 is not None and not _valid_ipv6(ipv6):
            raise DNSServiceError(INVALID_REQUEST, f'resource {r["id"]} : ipv6 invalide')
        if ipv4 is None and ipv6 is None:
            raise DNSServiceError(INVALID_REQUEST, f'resource {r["id"]} : ipv4 ou ipv6 requis')
        if ipv4 is not None:
            rid = _seeded_id(rng, 'rec', set(records))
            records[rid] = {'id': rid, 'name': dns_name, 'type': 'A', 'value': ipv4,
                            'ttl': rng.choice(_TTL_POOL), 'enabled': True}
        if ipv6 is not None:
            rid = _seeded_id(rng, 'rec', set(records))
            records[rid] = {'id': rid, 'name': dns_name, 'type': 'AAAA', 'value': ipv6,
                            'ttl': rng.choice(_TTL_POOL), 'enabled': True}
        resource_names.append(dns_name)

    # Alias déterministes optionnels : toujours une CNAME vers une ressource
    # RÉELLEMENT fournie, jamais un nom inventé sans rapport avec
    # l'environnement (cf. §3 du brief).
    alias_pool = list(_ALIAS_POOL)
    rng.shuffle(alias_pool)
    alias_count = min(rng.randint(0, 2), len(alias_pool))
    for i in range(alias_count):
        alias_name = f'{alias_pool[i]}.{zone}'
        if alias_name in resource_names:
            continue
        target = rng.choice(resource_names)
        rid = _seeded_id(rng, 'rec', set(records))
        records[rid] = {'id': rid, 'name': alias_name, 'type': 'CNAME', 'value': target,
                        'ttl': rng.choice(_TTL_POOL), 'enabled': True}

    service = {
        'schema_version': SCHEMA_VERSION,
        'environment_id': environment_id,
        'server': dict(server),
        'clients': client_states,
        'records': records,
        'service_status': 'running',
        'transport_allowed': True,
        'negative_ttl': rng.choice(_NEGATIVE_TTL_POOL),
        'cache': {cid: {} for cid in client_states},
        'revision': 0,
        'audit': [{'at': now, 'operation': 'generate_dns', 'actor_id': None, 'code': OK}],
    }
    validate_dns(service)
    return service


# ─── public_dns ──────────────────────────────────────────────────────────────

def public_dns(service, actor):
    """Projection pour console d'administration (capacité dns.manage).
    Expose configuration, enregistrements et compte d'entrées de cache par
    client — jamais le contenu du cache ni un objet de contexte/identité (il
    n'en existe pas dans ce moteur : la résolution DNS n'authentifie
    personne, voir le docstring du module)."""
    if actor.get('environment_id') != service['environment_id']:
        raise DNSServiceError(UNKNOWN_ENVIRONMENT, 'acteur hors environnement')
    if CAPABILITY_DNS_MANAGE not in (actor.get('permissions') or ()):
        raise DNSServiceError(PERMISSION_DENIED, 'capacité manquante : ' + CAPABILITY_DNS_MANAGE)

    clients_view = {}
    for client_id, client in service['clients'].items():
        clients_view[client_id] = {**copy.deepcopy(client), 'cache_count': len(service['cache'].get(client_id, {}))}

    return {
        'schema_version': service['schema_version'],
        'environment_id': service['environment_id'],
        'server': copy.deepcopy(service['server']),
        'clients': clients_view,
        'records': copy.deepcopy(service['records']),
        'service_status': service['service_status'],
        'transport_allowed': service['transport_allowed'],
        'negative_ttl': service['negative_ttl'],
        'revision': service['revision'],
        'audit': copy.deepcopy(service['audit']),
    }


# ─── Validation de la requête (forme) et du contexte (contenu) ─────────────

def _validate_resolve_request(client_id, query, now):
    if not _is_finite_number(now):
        raise DNSServiceError(INVALID_REQUEST, 'now doit être un nombre fini')
    if not isinstance(client_id, str) or not client_id:
        raise DNSServiceError(INVALID_REQUEST, 'client_id requis')
    if not isinstance(query, dict):
        raise DNSServiceError(INVALID_REQUEST, 'query doit être un dict')
    if not isinstance(query.get('name'), str) or not query['name']:
        raise DNSServiceError(INVALID_REQUEST, 'query.name requis')
    if query.get('type') not in QUERY_TYPES:
        raise DNSServiceError(INVALID_REQUEST, f'query.type inconnu : {query.get("type")}')


def _scope_ok(service, client_id, context):
    if not isinstance(context, dict):
        return False
    if context.get('environment_id') != service['environment_id']:
        return False
    if client_id not in service['clients']:
        return False
    if context.get('source_device_id') != client_id:
        return False
    if context.get('target_device_id') != service['server']['id']:
        return False
    return True


def _normalize_query_name(raw_name, client, zone):
    """Retourne (status, fqdn_ou_None, code). status='passed' => fqdn valide
    et normalisé (minuscules, sans point final). 'failed' => code renseigné
    (INVALID_NAME ou REFUSED)."""
    if '.' in raw_name:
        fqdn = _normalize_fqdn(raw_name)
    else:
        suffix = client['search_suffix']
        if not suffix:
            return 'failed', None, INVALID_NAME
        fqdn = _normalize_fqdn(raw_name) + '.' + _normalize_fqdn(suffix)
    if not _valid_hostname(fqdn):
        return 'failed', None, INVALID_NAME
    if not _in_zone(fqdn, zone):
        return 'failed', None, REFUSED
    return 'passed', fqdn, None


def _network_status(context, server, client, now):
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
    if network.get('target_ip') != client.get('dns_server_ip') or client.get('dns_server_ip') != server['ip']:
        return 'unknown'
    observed_at, valid_until = network.get('observed_at'), network.get('valid_until')
    if not _is_finite_number(observed_at) or not _is_finite_number(valid_until) or valid_until < observed_at:
        return 'unknown'
    if not (observed_at <= now <= valid_until):
        return 'unknown'
    return status


# ─── Résolution d'enregistrements : suivi de chaîne CNAME ───────────────────

def _records_at(service, name):
    return [r for r in service['records'].values() if r['name'] == name and r['enabled']]


def _lookup_chain(service, fqdn, qtype):
    """Retourne un dict décrivant l'issue de la résolution d'enregistrements :
    code, canonical_name, answers, addresses, cname_chain, tree_status."""
    if qtype == 'CNAME':
        at_name = _records_at(service, fqdn)
        cname = next((r for r in at_name if r['type'] == 'CNAME'), None)
        if cname is not None:
            return {'code': OK, 'canonical_name': fqdn,
                   'answers': [{'name': fqdn, 'type': 'CNAME', 'value': cname['value'], 'ttl_remaining': cname['ttl']}],
                   'addresses': [], 'cname_chain': [], 'ttl_for_cache': cname['ttl'], 'tree_status': 'passed'}
        if at_name:
            return {'code': NODATA, 'canonical_name': fqdn, 'answers': [], 'addresses': [], 'cname_chain': [],
                   'ttl_for_cache': service['negative_ttl'], 'tree_status': 'passed'}
        return {'code': NXDOMAIN, 'canonical_name': fqdn, 'answers': [], 'addresses': [], 'cname_chain': [],
               'ttl_for_cache': service['negative_ttl'], 'tree_status': 'passed'}

    visited = set()
    cname_chain = []
    answers = []
    current = fqdn
    hops = 0
    while True:
        at_name = _records_at(service, current)
        cname = next((r for r in at_name if r['type'] == 'CNAME'), None)
        if cname is not None:
            if current in visited:
                return {'code': CNAME_LOOP, 'canonical_name': current, 'answers': [], 'addresses': [],
                       'cname_chain': cname_chain, 'ttl_for_cache': None, 'tree_status': 'failed'}
            visited.add(current)
            hops += 1
            if hops > MAX_CNAME_HOPS:
                return {'code': CNAME_DEPTH, 'canonical_name': current, 'answers': [], 'addresses': [],
                       'cname_chain': cname_chain, 'ttl_for_cache': None, 'tree_status': 'failed'}
            answers.append({'name': current, 'type': 'CNAME', 'value': cname['value'], 'ttl_remaining': cname['ttl']})
            cname_chain.append(current)
            current = cname['value']
            continue
        final = next((r for r in at_name if r['type'] == qtype), None)
        if final is not None:
            answers.append({'name': current, 'type': qtype, 'value': final['value'], 'ttl_remaining': final['ttl']})
            ttl_for_cache = min(a['ttl_remaining'] for a in answers)
            return {'code': OK, 'canonical_name': current, 'answers': answers, 'addresses': [final['value']],
                   'cname_chain': cname_chain, 'ttl_for_cache': ttl_for_cache, 'tree_status': 'passed'}
        if at_name:
            return {'code': NODATA, 'canonical_name': current, 'answers': [], 'addresses': [],
                   'cname_chain': cname_chain, 'ttl_for_cache': service['negative_ttl'], 'tree_status': 'passed'}
        return {'code': NXDOMAIN, 'canonical_name': current, 'answers': [], 'addresses': [],
               'cname_chain': cname_chain, 'ttl_for_cache': service['negative_ttl'], 'tree_status': 'passed'}


# ─── resolve ─────────────────────────────────────────────────────────────────

def _build_result(status, code, tree, evidence, query_type, canonical_name=None, answers=(), addresses=(),
                  cname_chain=(), cache_hit=False, observed_at=None, valid_until=None, provenance=None):
    return {
        'status': status, 'code': code, 'dns_rcode': _DNS_RCODE_BY_CODE.get(code),
        'canonical_name': canonical_name, 'query_type': query_type,
        'answers': list(answers), 'addresses': list(addresses), 'cname_chain': list(cname_chain),
        'cache_hit': cache_hit, 'observed_at': observed_at, 'valid_until': valid_until,
        'evidence': evidence, 'tree': tree,
    }


def resolve(service, client_id, query, context, now):
    """Retourne toujours {'service': copie, 'result': {...}}. Ne mute jamais
    `service` en entrée. Ne modifie revision/audit que lorsqu'une nouvelle
    entrée de cache est effectivement écrite (insertion ou éviction+
    insertion) ; un hit, un refus, ou toute réponse non cachable laissent
    service inchangé (voir §6 de la doc)."""
    _validate_resolve_request(client_id, query, now)
    new_service = copy.deepcopy(service)

    scope_ok = _scope_ok(service, client_id, context)
    if not scope_ok:
        tree, _ = _chain([('scope', 'unknown'), ('query', 'blocked'), ('cache', 'blocked'),
                          ('resolver_config', 'blocked'), ('network', 'blocked'), ('transport', 'blocked'),
                          ('service', 'blocked'), ('records', 'blocked')])
        result = _build_result('unknown', INVALID_CONTEXT, tree, None, query.get('type'))
        return {'service': new_service, 'result': result}

    client = service['clients'][client_id]
    server = service['server']
    name_status, fqdn, name_code = _normalize_query_name(query['name'], client, server['zone'])
    if name_status != 'passed':
        tree, _ = _chain([('scope', 'passed'), ('query', 'failed'), ('cache', 'blocked'),
                          ('resolver_config', 'blocked'), ('network', 'blocked'), ('transport', 'blocked'),
                          ('service', 'blocked'), ('records', 'blocked')])
        result = _build_result('failed', name_code, tree, None, query['type'])
        return {'service': new_service, 'result': result}

    qtype = query['type']
    cache_key = fqdn + '|' + qtype
    client_cache = service['cache'].get(client_id, {})
    entry = client_cache.get(cache_key)
    if entry is not None and entry['cached_at'] <= now < entry['expires_at']:
        ttl_remaining = max(0, entry['expires_at'] - now)
        response = copy.deepcopy(entry['response'])
        answers = [dict(a, ttl_remaining=ttl_remaining) for a in response['answers']]
        tree = _forced_tree(('scope', 'query', 'cache'))
        result = _build_result('resolved', response['code'], tree, 'simulated_cache', qtype,
                               canonical_name=response['canonical_name'], answers=answers,
                               addresses=response['addresses'], cname_chain=response['cname_chain'],
                               cache_hit=True, observed_at=entry['cached_at'], valid_until=entry['expires_at'],
                               provenance=entry['provenance'])
        return {'service': new_service, 'result': result}

    steps = [('scope', 'passed'), ('query', 'passed'), ('cache', 'passed')]
    codes = {}

    dns_ip = client.get('dns_server_ip')
    if dns_ip is None:
        resolver_status, resolver_code = 'failed', DNS_NOT_CONFIGURED
    elif dns_ip != server['ip']:
        resolver_status, resolver_code = 'unknown', DNS_SERVER_UNMODELED
    else:
        resolver_status, resolver_code = 'passed', None
    steps.append(('resolver_config', resolver_status))
    codes['resolver_config'] = resolver_code

    net_status = _network_status(context, server, client, now)
    net_effective = 'passed' if net_status == 'up' else ('failed' if net_status == 'down' else 'unknown')
    steps.append(('network', net_effective))
    codes['network'] = NETWORK_DOWN if net_status == 'down' else OBSERVATION_UNKNOWN

    steps.append(('transport', 'passed' if service['transport_allowed'] else 'failed'))
    codes['transport'] = DNS_TRANSPORT_BLOCKED

    steps.append(('service', 'passed' if service['service_status'] == 'running' else 'failed'))
    codes['service'] = DNS_SERVICE_STOPPED

    outcome = _lookup_chain(service, fqdn, qtype)
    steps.append(('records', outcome['tree_status']))
    codes['records'] = outcome['code']

    tree, statuses = _chain(steps)
    allowed = all(status == 'passed' for _, status in statuses)
    network_evidence = (context.get('network') or {}).get('evidence') if isinstance(context, dict) else None
    net_observed_at = (context.get('network') or {}).get('observed_at') if isinstance(context, dict) else None
    net_valid_until = (context.get('network') or {}).get('valid_until') if isinstance(context, dict) else None

    if allowed:
        status, code = 'resolved', outcome['code']
        result = _build_result(status, code, tree, 'simulated_dns', qtype,
                               canonical_name=outcome['canonical_name'], answers=outcome['answers'],
                               addresses=outcome['addresses'], cname_chain=outcome['cname_chain'],
                               cache_hit=False, observed_at=net_observed_at, valid_until=net_valid_until)
        if code in _CACHEABLE_CODES and outcome['ttl_for_cache'] and outcome['ttl_for_cache'] > 0:
            ttl = outcome['ttl_for_cache']
            entries = new_service['cache'].setdefault(client_id, {})
            evicted = None
            if cache_key not in entries and len(entries) >= MAX_CACHE_PER_CLIENT:
                evicted = min(entries.items(), key=lambda kv: (kv[1]['cached_at'], kv[0]))[0]
                del entries[evicted]
            entries[cache_key] = {
                'response': {'code': code, 'canonical_name': outcome['canonical_name'],
                            'answers': outcome['answers'], 'addresses': outcome['addresses'],
                            'cname_chain': outcome['cname_chain']},
                'cached_at': now, 'expires_at': now + ttl,
                'provenance': {'evidence': 'simulated_dns', 'transport_evidence': network_evidence},
            }
            new_service['revision'] = service['revision'] + 1
            new_service['audit'].append({'at': now, 'operation': 'resolve', 'client_id': client_id,
                                         'cache_key': cache_key, 'code': code,
                                         'evicted_cache_key': evicted})
            validate_dns(new_service)
        return {'service': new_service, 'result': result}

    first_stage, first_status = next((s, st) for s, st in statuses if st != 'passed')
    overall_status = first_status if first_status == 'unknown' else 'failed'
    code = codes[first_stage]
    result = _build_result(overall_status, code, tree, None, qtype,
                           observed_at=net_observed_at if first_stage in ('network', 'transport', 'service', 'records') else None,
                           valid_until=net_valid_until if first_stage in ('network', 'transport', 'service', 'records') else None)
    return {'service': new_service, 'result': result}


# ─── flush_cache ─────────────────────────────────────────────────────────────

def flush_cache(service, actor, client_id, now):
    """Vide le cache d'UN client. Autorisé pour un administrateur
    (dns.manage) ou pour l'acteur du poste lui-même (dns.flush_own,
    device_id==client_id, même environnement) — jamais pour vider le cache
    d'un autre poste avec cette seconde capacité. Toujours
    {'service':copie,'result':...} ; échec = aucun effet."""
    if actor.get('environment_id') != service.get('environment_id'):
        raise DNSServiceError(UNKNOWN_ENVIRONMENT, 'acteur hors environnement')
    permissions = actor.get('permissions') or ()
    authorized = (CAPABILITY_DNS_MANAGE in permissions or
                 (CAPABILITY_DNS_FLUSH_OWN in permissions and actor.get('device_id') == client_id))
    if not authorized:
        raise DNSServiceError(PERMISSION_DENIED, 'capacité manquante pour vider ce cache')
    if client_id not in service['clients']:
        raise DNSServiceError(UNKNOWN_CLIENT, client_id)

    new_service = copy.deepcopy(service)
    validate_dns(new_service)
    new_service['cache'][client_id] = {}
    new_service['revision'] = service['revision'] + 1
    new_service['audit'].append({'at': now, 'operation': 'flush_cache', 'actor_id': actor.get('id'),
                                 'client_id': client_id, 'code': OK})
    validate_dns(new_service)
    return {'service': new_service, 'result': {'status': 'ok', 'allowed': True, 'code': OK, 'client_id': client_id}}


# ─── apply_operation (administration) ───────────────────────────────────────

def _require(payload, *keys):
    for key in keys:
        if key not in payload:
            raise DNSServiceError(INVALID_REQUEST, f'champ manquant : {key}')


def _check_record_conflict(service, record_id, name, rtype):
    """Vérifie qu'activer un enregistrement (name,rtype) ne crée pas de
    doublon actif ni de conflit CNAME/A-AAAA avec un AUTRE enregistrement
    (record_id exclu de la comparaison, pour permettre sa propre mise à jour)."""
    others = [r for rid, r in service['records'].items() if rid != record_id and r['enabled'] and r['name'] == name]
    if rtype == 'CNAME':
        if others:
            raise DNSServiceError(RECORD_CONFLICT, f'{name} : un enregistrement actif existe déjà')
    else:
        if any(r['type'] == 'CNAME' for r in others):
            raise DNSServiceError(RECORD_CONFLICT, f'{name} : un CNAME actif exclut A/AAAA')
        if any(r['type'] == rtype for r in others):
            raise DNSServiceError(RECORD_CONFLICT, f'{name} : un {rtype} actif existe déjà')


def _op_upsert_record(service, payload, now):
    record_id = payload.get('record_id')
    zone = service['server']['zone']
    if record_id:
        if record_id not in service['records']:
            raise DNSServiceError(UNKNOWN_RECORD, record_id)
        _require(payload, 'name', 'type', 'value', 'ttl', 'enabled')
    else:
        _require(payload, 'name', 'type', 'value', 'ttl', 'enabled')
        record_id = _live_id('rec', set(service['records']))

    rtype = payload['type']
    if rtype not in RECORD_TYPES:
        raise DNSServiceError(INVALID_REQUEST, 'type invalide')
    name = payload['name']
    if not isinstance(name, str) or not _valid_hostname(name):
        raise DNSServiceError(INVALID_REQUEST, 'name invalide')
    name = _normalize_fqdn(name)
    if not _in_zone(name, zone):
        raise DNSServiceError(RECORD_OUT_OF_ZONE, 'name hors zone')
    value = payload['value']
    if rtype == 'A' and not _valid_ipv4(value):
        raise DNSServiceError(INVALID_REQUEST, 'value IPv4 invalide')
    if rtype == 'AAAA' and not _valid_ipv6(value):
        raise DNSServiceError(INVALID_REQUEST, 'value IPv6 invalide')
    if rtype == 'CNAME':
        if not isinstance(value, str) or not _valid_hostname(value):
            raise DNSServiceError(INVALID_REQUEST, 'cible CNAME invalide')
        value = _normalize_fqdn(value)
        if not _in_zone(value, zone):
            raise DNSServiceError(RECORD_OUT_OF_ZONE, 'cible CNAME hors zone')
    if not _is_valid_ttl(payload['ttl']):
        raise DNSServiceError(INVALID_REQUEST, 'ttl invalide')
    if not _is_strict_bool(payload['enabled']):
        raise DNSServiceError(INVALID_REQUEST, 'enabled doit être un booléen strict')

    if payload['enabled']:
        _check_record_conflict(service, record_id, name, rtype)

    service['records'][record_id] = {'id': record_id, 'name': name, 'type': rtype, 'value': value,
                                     'ttl': payload['ttl'], 'enabled': payload['enabled']}
    return {'status': 'ok', 'code': OK, 'record_id': record_id}


def _op_delete_record(service, payload, now):
    _require(payload, 'record_id')
    if payload['record_id'] not in service['records']:
        raise DNSServiceError(UNKNOWN_RECORD, payload['record_id'])
    del service['records'][payload['record_id']]
    return {'status': 'ok', 'code': OK, 'record_id': payload['record_id']}


def _op_set_record_enabled(service, payload, now):
    _require(payload, 'record_id', 'enabled')
    record = service['records'].get(payload['record_id'])
    if record is None:
        raise DNSServiceError(UNKNOWN_RECORD, payload['record_id'])
    if not _is_strict_bool(payload['enabled']):
        raise DNSServiceError(INVALID_REQUEST, 'enabled doit être un booléen strict')
    if payload['enabled']:
        _check_record_conflict(service, record['id'], record['name'], record['type'])
    record['enabled'] = payload['enabled']
    return {'status': 'ok', 'code': OK, 'record_id': record['id']}


def _op_set_service_status(service, payload, now):
    _require(payload, 'status')
    if payload['status'] not in ('running', 'stopped'):
        raise DNSServiceError(INVALID_REQUEST, 'status invalide')
    service['service_status'] = payload['status']
    return {'status': 'ok', 'code': OK}


def _op_set_transport_allowed(service, payload, now):
    _require(payload, 'allowed')
    if not _is_strict_bool(payload['allowed']):
        raise DNSServiceError(INVALID_REQUEST, 'allowed doit être un booléen strict')
    service['transport_allowed'] = payload['allowed']
    return {'status': 'ok', 'code': OK}


def _op_set_negative_ttl(service, payload, now):
    _require(payload, 'negative_ttl')
    if not _is_valid_ttl(payload['negative_ttl']):
        raise DNSServiceError(INVALID_REQUEST, 'negative_ttl invalide')
    service['negative_ttl'] = payload['negative_ttl']
    return {'status': 'ok', 'code': OK}


def _op_set_client_dns(service, payload, now):
    _require(payload, 'client_id', 'dns_server_ip', 'search_suffix')
    client = service['clients'].get(payload['client_id'])
    if client is None:
        raise DNSServiceError(UNKNOWN_CLIENT, payload['client_id'])
    dns_ip = payload['dns_server_ip']
    if dns_ip is not None and not _valid_ip_any(dns_ip):
        raise DNSServiceError(INVALID_REQUEST, 'dns_server_ip invalide')
    suffix = payload['search_suffix']
    if not isinstance(suffix, str):
        raise DNSServiceError(INVALID_REQUEST, 'search_suffix doit être une chaîne')
    if suffix and not _valid_hostname(suffix):
        raise DNSServiceError(INVALID_REQUEST, 'search_suffix invalide')
    client['dns_server_ip'] = dns_ip
    client['search_suffix'] = suffix
    return {'status': 'ok', 'code': OK, 'client_id': client['id']}


_HANDLERS = {
    'upsert_record': _op_upsert_record, 'delete_record': _op_delete_record,
    'set_record_enabled': _op_set_record_enabled, 'set_service_status': _op_set_service_status,
    'set_transport_allowed': _op_set_transport_allowed, 'set_negative_ttl': _op_set_negative_ttl,
    'set_client_dns': _op_set_client_dns,
}


def apply_operation(service, operation, payload, actor, now):
    """Retourne {'service': copie, 'result': {...}}. N'écrit jamais dans
    `service` : la copie de travail est créée avant toute validation. Une
    opération invalide lève DNSServiceError sans aucune mutation ni audit."""
    if operation not in _HANDLERS:
        raise DNSServiceError(UNKNOWN_OPERATION, operation)
    if actor.get('environment_id') != service.get('environment_id'):
        raise DNSServiceError(UNKNOWN_ENVIRONMENT, 'acteur hors environnement')
    if CAPABILITY_DNS_MANAGE not in (actor.get('permissions') or ()):
        raise DNSServiceError(PERMISSION_DENIED, 'capacité manquante : ' + CAPABILITY_DNS_MANAGE)

    new_service = copy.deepcopy(service)
    validate_dns(new_service)  # garde-fou : état de départ toujours cohérent
    payload = payload or {}
    result = _HANDLERS[operation](new_service, payload, now)

    new_service['revision'] = service['revision'] + 1
    audit_entry = {'at': now, 'operation': operation, 'actor_id': actor.get('id'), 'code': result['code']}
    for key, value in result.items():
        if key not in ('status', 'code'):
            audit_entry[key] = value
    new_service['audit'].append(audit_entry)
    validate_dns(new_service)
    return {'service': new_service, 'result': result}

