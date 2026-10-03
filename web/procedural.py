"""Choix contraint des incidents ; versionner les règles pour rejouer un tirage."""
import random
VERSION = 3
SITES = ('ALB', 'MPL', 'ROD', 'TLS', 'LYO', 'BOR')
REQUESTERS = ('Camille', 'Nora', 'Samir', 'Léa', 'Hugo', 'Mina')
FAMILIES = [
 ('names', 'Les services ne sont plus accessibles par leur nom', ('dns_service_off',)),
 ('intranet_name', 'Le nom de l’intranet ne mène plus à la bonne page', ('dns_record_delete', 'dns_record_wrong')),
 ('web', 'La page intranet ne s’ouvre plus', ('http_service_off',)),
 ('ftp', 'Le dépôt documentaire ne répond plus', ('ftp_service_off',)),
 ('upload', 'Impossible de déposer les documents', ('ftp_write_denied',)),
 ('account', 'Un compte ne peut plus accéder au dépôt', ('ftp_password_wrong',)),
 ('lease', 'Un poste ne reçoit plus de bail DHCP', ('dhcp_server_off', 'dhcp_relay_missing', 'dhcp_relay_wrong')),
 ('backup', 'La sauvegarde réseau échoue', ('tftp_service_off',)),
]
def choose(seed, requested=None, history=(), opened=()):
 rng=random.Random(seed)
 blocked={t.get('procedural',{}).get('family') for t in opened}
 active_causes={t.get('service_scenario') for t in opened}
 options=[]
 for family,title,causes in FAMILIES:
  if family in blocked:continue
  for cause in causes:
   if cause in active_causes:continue
   if requested and requested not in (family,cause):continue
   options.append((family,title,cause))
 if not options:raise ValueError('Aucun incident disponible : termine les tickets de cette famille déjà ouverts.')
 # Préférer une cause absente des six dernières interventions ; sinon la moins récente.
 recent=[t.get('service_scenario') for t in history[-6:]]
 fresh=[x for x in options if x[2] not in recent]
 if fresh:options=fresh
 else:
  oldest=min(recent.index(x[2]) for x in options)
  options=[x for x in options if recent.index(x[2])==oldest]
 family,title,cause=rng.choice(options)
 return dict(version=VERSION,seed=seed,family=family,title=title,cause=cause,
             address_family=rng.choice(('10','172','192')),
             site_code=rng.choice(SITES)+str(rng.randint(1,99)).zfill(2),
             requester=rng.choice(REQUESTERS),employee_count=rng.randint(2,6))
