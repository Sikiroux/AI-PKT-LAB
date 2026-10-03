"""
exercises.py — Exercices « papier », sans Packet Tracer, vérifiés par calcul.

Types :
  subnet_info   : réseau, broadcast, 1re/dernière adresse hôte, nombre d'hôtes
  vlsm_plan     : découper un réseau pour plusieurs services (toute réponse
                  valide est acceptée, pas seulement celle du corrigé)
  ipv6_compress : abréger une adresse IPv6
  ipv6_expand   : développer une adresse IPv6 abrégée
  eui64         : calculer l'adresse IPv6 EUI-64 à partir d'une adresse MAC

Chaque générateur renvoie un Exercise : l'énoncé, les champs à saisir, une
fonction de correction et le corrigé détaillé (le « pourquoi », pas juste la réponse).
"""

import random
import ipaddress
from dataclasses import dataclass, field
from typing import Callable, List, Tuple


@dataclass
class Exercise:
    title: str
    statement: str
    fields: List[str]                                   # libellés des réponses à saisir
    grade: Callable[[List[str]], List[Tuple[bool, str]]]  # -> [(ok, commentaire)] par champ
    correction: str
    kind: str = ''
    extra: dict = field(default_factory=dict)


def _private_network(rng, prefix):
    """Un réseau privé aléatoire de la taille demandée, dans une des trois plages RFC 1918."""
    base = rng.choice(['10.0.0.0/8', '172.16.0.0/12', '192.168.0.0/16'])
    parent = ipaddress.IPv4Network(base)
    count = 2 ** (prefix - parent.prefixlen)
    index = rng.randrange(count)
    return ipaddress.IPv4Network((int(parent.network_address) + index * 2 ** (32 - prefix), prefix))


def _same_ip(answer, expected):
    try:
        return ipaddress.ip_address(answer.strip()) == ipaddress.ip_address(expected)
    except ValueError:
        return False


# ─── Sous-réseau : informations ──────────────────────────────────────────────

def subnet_info(rng, level=1):
    prefix = rng.choice([24, 25, 26, 27, 28] if level == 1 else [19, 20, 21, 22, 23, 26, 27, 28, 29, 30])
    net = _private_network(rng, prefix)
    host = net.network_address + rng.randrange(1, net.num_addresses - 1)
    first, last = net.network_address + 1, net.broadcast_address - 1
    n_hosts = net.num_addresses - 2
    expected = [str(net.network_address), str(net.broadcast_address), str(first), str(last), str(n_hosts)]

    def grade(ans):
        out = []
        for label, a, e in zip(['réseau', 'broadcast', '1re hôte', 'dernière hôte'], ans[:4], expected[:4]):
            out.append((_same_ip(a, e), f'{label} : {e}'))
        out.append((ans[4].strip() == expected[4], f"nombre d'hôtes : {expected[4]}"))
        return out

    mask = str(net.netmask)
    block = 2 ** (32 - prefix)
    correction = (f'/{prefix} = masque {mask} → bloc de {block} adresses '
                  f'(2^{32 - prefix}), dont 2 réservées (réseau + broadcast).\n'
                  f'  {host} appartient au bloc qui commence à {net.network_address}.\n'
                  f'  Réseau {net.network_address}, broadcast {net.broadcast_address}, '
                  f'hôtes {first} → {last} ({n_hosts} adresses utilisables).')
    return Exercise('Informations de sous-réseau',
                    f'Pour l\'adresse {host}/{prefix}, donne :',
                    ['Adresse réseau', 'Adresse de broadcast', '1re adresse hôte', 'Dernière adresse hôte', "Nombre d'hôtes"],
                    grade, correction, 'subnet_info')


# ─── Plan d'adressage VLSM ───────────────────────────────────────────────────

SERVICES = ['Comptabilité', 'RH', 'Commercial', 'Direction', 'Logistique', 'Accueil', 'Informatique',
            'Production', 'Wi-Fi invités', 'Serveurs']


def _min_prefix(hosts):
    p = 32
    while 2 ** (32 - p) - 2 < hosts:
        p -= 1
    return p


def vlsm_plan(rng, level=1, services=None):
    """services : nombre imposé de services (3 pour la mise en place sur un 2911)."""
    parent = _private_network(rng, 24 if level == 1 else rng.choice([22, 23]))
    n = services or (rng.randint(3, 4) if level == 1 else rng.randint(4, 6))
    names = rng.sample(SERVICES, n)
    # Besoins tirés au hasard mais qui tiennent toujours dans le réseau parent (vérifié)
    while True:
        needs = sorted((rng.randint(2, parent.num_addresses // (n + 1)) for _ in names), reverse=True)
        if sum(2 ** (32 - _min_prefix(h)) for h in needs) <= parent.num_addresses:
            break
    needs_by_name = dict(zip(names, needs))

    # Corrigé : méthode classique, le plus grand besoin d'abord
    plan, cursor = [], int(parent.network_address)
    for name, hosts in sorted(needs_by_name.items(), key=lambda x: -x[1]):
        p = _min_prefix(hosts)
        plan.append((name, hosts, ipaddress.IPv4Network((cursor, p))))
        cursor += 2 ** (32 - p)

    def grade(ans):
        out, taken = [], []
        for name, a in zip(names, ans):
            hosts = needs_by_name[name]
            try:
                sub = ipaddress.IPv4Network(a.strip(), strict=True)
            except ValueError:
                try:  # adresse d'hôte au lieu d'adresse réseau : on explique pourquoi
                    loose = ipaddress.IPv4Network(a.strip(), strict=False)
                    step = loose.num_addresses
                    out.append((False, f'{name} : {a.strip()} n\'est pas une adresse réseau. Les /{loose.prefixlen} '
                                       f'commencent tous les {step} adresses ; le bloc qui contient '
                                       f'{a.strip().split("/")[0]} commence à {loose.network_address}'))
                except ValueError:
                    out.append((False, f'{name} : « {a} » illisible (format attendu : 192.168.1.0/26)'))
                continue
            problems = []
            if not sub.subnet_of(parent):
                problems.append(f'hors de {parent}')
            if sub.num_addresses - 2 < hosts:
                problems.append(f'trop petit ({sub.num_addresses - 2} hôtes pour {hosts} demandés)')
            if any(sub.overlaps(t) for t in taken):
                problems.append('chevauche un autre service')
            taken.append(sub)
            if problems:
                out.append((False, f'{name} : {sub} → ' + ', '.join(problems)))
            else:
                best = _min_prefix(hosts)
                note = '' if sub.prefixlen == best else f' (valide, mais un /{best} suffisait : adresses gaspillées)'
                out.append((True, f'{name} : {sub}{note}'))
        return out

    lines = '\n'.join(f'   - {name} : {needs_by_name[name]} hôtes' for name in names)
    corr = '\n'.join(f'   {name:14} {hosts:4} hôtes → {net}  (/{net.prefixlen} = {net.num_addresses - 2} hôtes max, '
                     f'passerelle {net.network_address + 1})' for name, hosts, net in plan)
    correction = ('Méthode : trier les besoins du plus grand au plus petit, choisir pour chacun le plus petit '
                  'préfixe suffisant (2^(32-p) - 2 ≥ besoin), puis allouer les blocs à la suite.\n' + corr)
    return Exercise('Plan d\'adressage VLSM',
                    f'Découpe {parent} pour ces services (réponse au format réseau/préfixe, ex. 192.168.1.0/26) :\n{lines}',
                    names, grade, correction, 'vlsm_plan',
                    extra={'plan': [(name, str(net)) for name, _, net in plan]})


# ─── IPv6 ────────────────────────────────────────────────────────────────────

def _random_ipv6(rng):
    groups = []
    for _ in range(8):
        r = rng.random()
        groups.append(0 if r < 0.35 else rng.randrange(1, 0x10) if r < 0.55 else rng.randrange(0x10, 0x10000))
    groups[0] = rng.choice([0x2001, 0x2a01, 0xfe80, 0xfd00])
    # garantir au moins une suite de zéros, sinon l'abréviation « :: » n'a rien à faire
    i = rng.randrange(2, 6)
    groups[i] = groups[i + 1] = 0
    return ipaddress.IPv6Address(':'.join(f'{g:x}' for g in groups))


def ipv6_compress(rng, level=1):
    addr = _random_ipv6(rng)
    full, short = addr.exploded, addr.compressed

    def grade(ans):
        a = ans[0].strip().lower()
        try:
            same = ipaddress.IPv6Address(a) == addr
        except ValueError:
            return [(False, f'« {a} » n\'est pas une adresse IPv6 valide. Attendu : {short}')]
        if a == short:
            return [(True, short)]
        if same:
            return [(False, f'Adresse équivalente, mais pas la forme la plus courte. Attendu : {short}')]
        return [(False, f'Ce n\'est pas la même adresse. Attendu : {short}')]

    correction = ('Règle 1 : supprimer les zéros en tête de chaque groupe (0db8 → db8, 0000 → 0).\n'
                  '  Règle 2 : remplacer UNE SEULE fois la plus longue suite de groupes à 0 par « :: »\n'
                  '  (si deux suites ont la même longueur, on abrège la première : RFC 5952).\n'
                  f'  {full}\n  → {short}')
    return Exercise('IPv6 : abréger', f'Écris sous sa forme la plus courte :\n   {full}',
                    ['Adresse abrégée'], grade, correction, 'ipv6_compress')


def ipv6_expand(rng, level=1):
    addr = _random_ipv6(rng)

    def grade(ans):
        ok = ans[0].strip().lower() == addr.exploded
        return [(ok, addr.exploded)]

    correction = ('Rétablir les zéros en tête pour avoir 4 chiffres par groupe, puis remplacer « :: » '
                  'par autant de groupes 0000 qu\'il en faut pour arriver à 8 groupes.\n'
                  f'  {addr.compressed}\n  → {addr.exploded}')
    return Exercise('IPv6 : développer', f'Écris la forme complète (8 groupes de 4 chiffres) :\n   {addr.compressed}',
                    ['Adresse complète'], grade, correction, 'ipv6_expand')


def eui64(rng, level=1):
    mac = [rng.randrange(256) for _ in range(6)]
    mac[0] &= 0xFC  # adresse unicast, administrée globalement
    mac_str = '-'.join(f'{b:02X}' for b in mac)
    prefix = ipaddress.IPv6Network(f'2001:db8:{rng.randrange(0x10000):x}:{rng.randrange(0x10000):x}::/64')
    eui = [mac[0] ^ 0x02] + mac[1:3] + [0xFF, 0xFE] + mac[3:]
    iid = ':'.join(f'{eui[i] << 8 | eui[i + 1]:x}' for i in range(0, 8, 2))
    addr = ipaddress.IPv6Address(int(prefix.network_address) | int(ipaddress.IPv6Address('::' + iid)))

    def grade(ans):
        try:
            iid_ok = ipaddress.IPv6Address('::' + ans[0].strip()) == ipaddress.IPv6Address('::' + iid)
        except ValueError:
            iid_ok = False
        return [(iid_ok, f'ID d\'interface : {iid}'), (_same_ip(ans[1], str(addr)), f'adresse : {addr.compressed}')]

    b0 = mac[0]
    correction = (f'1. Couper la MAC en deux : {mac_str[:8]} | {mac_str[9:]}\n'
                  f'  2. Insérer FF-FE au milieu : {mac_str[:8]}-FF-FE-{mac_str[9:]}\n'
                  f'  3. Inverser le 7e bit du 1er octet : {b0:02X} = {b0:08b} → {b0 ^ 2:08b} = {b0 ^ 2:02X}\n'
                  f'  4. ID d\'interface : {iid}\n'
                  f'  5. Préfixe + ID : {addr.compressed}')
    return Exercise('IPv6 : EUI-64',
                    f'Un PC a la MAC {mac_str} et reçoit le préfixe {prefix}. Calcule :',
                    ['ID d\'interface (64 bits, ex. 21a:2bff:fe3c:4d5e)', 'Adresse IPv6 complète'],
                    grade, correction, 'eui64')


GENERATORS = {
    'subnet_info': ('Sous-réseaux : réseau, broadcast, plage d\'hôtes', subnet_info),
    'vlsm_plan': ('Plan d\'adressage VLSM', vlsm_plan),
    'ipv6_compress': ('IPv6 : abréger une adresse', ipv6_compress),
    'ipv6_expand': ('IPv6 : développer une adresse', ipv6_expand),
    'eui64': ('IPv6 : calcul EUI-64', eui64),
}


def generate(kind=None, level=1, seed=None):
    rng = random.Random(seed)
    kind = kind or rng.choice(list(GENERATORS))
    return GENERATORS[kind][1](rng, level)


if __name__ == '__main__':
    # Autotest : chaque corrigé doit être accepté par sa propre correction
    for kind in GENERATORS:
        for seed in range(200):
            ex = generate(kind, level=1 + seed % 2, seed=seed)
            if kind == 'subnet_info':
                import re
                net = ipaddress.IPv4Network(re.search(r'\d+\.\d+\.\d+\.\d+/\d+', ex.statement).group(), strict=False)
                ans = [str(net.network_address), str(net.broadcast_address),
                       str(net.network_address + 1), str(net.broadcast_address - 1), str(net.num_addresses - 2)]
            elif kind == 'vlsm_plan':
                sol = {l.split()[0]: l.split('→')[1].split()[0] for l in ex.correction.splitlines()[1:]}
                ans = [sol[n.split()[0]] for n in ex.fields]
            elif kind == 'ipv6_compress':
                ans = [ex.correction.splitlines()[-1].split('→ ')[1]]
            elif kind == 'ipv6_expand':
                ans = [ex.correction.splitlines()[-1].split('→ ')[1]]
            else:
                lines = ex.correction.splitlines()
                ans = [lines[3].split(': ')[1], lines[4].split(': ')[1]]
            res = ex.grade(ans)
            assert all(ok for ok, _ in res), (kind, seed, ans, res)
    print('autotest OK :', ', '.join(GENERATORS))
    print()
    ex = generate('vlsm_plan', seed=4)
    print(ex.statement, '\n\nCorrigé :', ex.correction)
