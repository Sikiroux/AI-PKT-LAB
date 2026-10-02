"""
faults.py — Catalogue de pannes et injection dans un lab généré par builder.py

Principe :
  builder.py produit un lab SAIN (fichier XML + topology_info).
  faults.py choisit une ou plusieurs pannes compatibles avec la topologie et
  la difficulté, les applique au XML, puis rechiffre en .pkt.

Chaque panne renvoie un "rapport" (dict) qui sert ensuite :
  - à ticket.py  : décrire le SYMPTÔME côté utilisateur (jamais la cause) ;
  - à checker.py : savoir ce qui doit être vrai une fois la panne réparée.

Règle d'or (validée par tests) : on n'injecte que des pannes que Packet Tracer
sait lui-même créer ET réparer depuis son interface.
"""

import io
import os
import sys
import json
import random
import ipaddress
import contextlib
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ptexplorer as _pte
import ticket as _ticket
import instructions as _instructions
import worksheet as _worksheet
import activity as _activity
from builder import PktLab

# Réutilise la synchronisation config IOS -> ports du moteur du fork
_SYNC = PktLab()._sync_ios_interface_ports

# Gabarit d'activité PT réel (racine PACKETTRACER5_ACTIVITY, COMPARISONS et
# INITIALSETUP pré-générés par PT lui-même) utilisé comme source de
# prototypes par activity.assemble_activity(). Modèles couverts par ce
# gabarit : 2960-24TT (switch) et PC-PT (PC/serveur) correspondent
# exactement aux nôtres ; un modèle absent retombe sur un nœud minimal
# (pas de crash, juste moins détaillé — la notation native reste désactivée
# de toute façon, checker.py est seul juge).
_ACTIVITY_TEMPLATE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  'templates', 'activities', 'subnetting_activity.xml')


# ─── Accès au XML ────────────────────────────────────────────────────────────

def _devices(root):
    return {d.findtext('ENGINE/NAME'): d for d in root.iter('DEVICE') if d.find('ENGINE') is not None}


def _wired_port(engine):
    for p in engine.iter('PORT'):
        t = (p.findtext('TYPE') or '').lower()
        if 'copper' in t:
            return p
    return None


def _set(parent, tag, value):
    el = parent.find(tag)
    if el is None:
        el = ET.SubElement(parent, tag)
    el.text = value


def _config_lines(engine, section='RUNNINGCONFIG'):
    sec = engine.find(section)
    return [l.text or '' for l in sec.findall('LINE')] if sec is not None else []


def _write_config(engine, lines):
    """Réécrit running + startup (la panne est 'sauvegardée'), puis resynchronise les ports."""
    for section in ('RUNNINGCONFIG', 'STARTUPCONFIG'):
        sec = engine.find(section)
        if sec is None:
            sec = ET.SubElement(engine, section)
        sec.clear()
        for line in lines:
            ET.SubElement(sec, 'LINE').text = line
    _SYNC(engine, '\n'.join(lines))


def _interface_block(lines, interface):
    """Indices (début, fin) du bloc 'interface X' dans la config, fin exclue."""
    start = next(i for i, l in enumerate(lines) if l.strip() == f'interface {interface}')
    end = start + 1
    while end < len(lines) and lines[end].startswith(' '):
        end += 1
    return start, end


def _router_ospf_block(lines):
    """Même principe que _interface_block, pour le bloc 'router ospf 1'."""
    start = next(i for i, l in enumerate(lines) if l.strip() == 'router ospf 1')
    end = start + 1
    while end < len(lines) and lines[end].startswith(' '):
        end += 1
    return start, end


def _vlan_block(lines, vid):
    """Même principe que _interface_block, pour le bloc 'vlan X'."""
    start = next(i for i, l in enumerate(lines) if l.strip() == f'vlan {vid}')
    end = start + 1
    while end < len(lines) and lines[end].startswith(' '):
        end += 1
    return start, end


def _pc_access_point(topo, pc):
    """Switch + port auxquels un PC est relié, déduits de topo['links']."""
    return next(((l[0], l[1]) if l[2] == pc else (l[2], l[3])) for l in topo['links'] if pc in (l[0], l[2]))


def _set_pc_gateway(engine, gw):
    _set(engine, 'GATEWAY', gw)
    port = _wired_port(engine)
    if port is not None:
        _set(port, 'PORT_GATEWAY', gw)


def _pick_pc(topo, rng, dhcp=None):
    """Choisit un PC, en évitant ceux déjà touchés par une autre panne (topo['_busy'])."""
    busy = topo.get('_busy', set())
    pcs = [n for n, d in topo['devices'].items() if d['type'] == 'pc' and n not in busy
           and d.get('role') != 'admin'
           and (dhcp is None or bool(d.get('dhcp')) == dhcp)]
    if not pcs:
        raise LookupError('Aucun PC disponible pour cette panne')
    return rng.choice(pcs)


def _pick_device(topo, rng, candidates):
    """Choisit un appareil parmi une liste de candidats, en évitant ceux déjà
    touchés par une autre panne (topo['_busy']) — même principe que _pick_pc,
    généralisé aux pannes routeur dont la cible n'est pas fixe."""
    busy = topo.get('_busy', set())
    choices = [c for c in candidates if c not in busy]
    if not choices:
        raise LookupError('Aucun appareil disponible pour cette panne')
    return rng.choice(choices)


# ─── Pannes ──────────────────────────────────────────────────────────────────
# Chaque fonction : (root, topo, rng) -> rapport
# rapport = {id, device, cause, solution, checks}
# checks = liste d'assertions sur l'état attendu APRÈS réparation, lues par checker.py

def f_pc_wrong_gateway(root, topo, rng):
    pc = _pick_pc(topo, rng, dhcp=False)
    net = ipaddress.IPv4Network(topo['network'])
    wrong = str(net.network_address + rng.choice([2, 100, 254]))
    _set_pc_gateway(_devices(root)[pc].find('ENGINE'), wrong)
    return {'device': pc,
            'cause': f'Passerelle de {pc} à {wrong} au lieu de {topo["gateway"]}',
            'solution': f'Sur {pc} : Desktop > IP Configuration > Default Gateway = {topo["gateway"]}',
            'checks': [['pc_gateway', pc, topo['gateway']]]}


def f_pc_wrong_ip(root, topo, rng):
    pc = _pick_pc(topo, rng, dhcp=False)
    good = topo['devices'][pc]['ip']
    octets = good.split('.')
    octets[2] = str((int(octets[2]) + 1) % 255)
    wrong = '.'.join(octets)
    _set(_wired_port(_devices(root)[pc].find('ENGINE')), 'IP', wrong)
    return {'device': pc,
            'cause': f'IP de {pc} à {wrong} (hors du réseau {topo["network"]})',
            'solution': f'Sur {pc} : IP = {good}',
            'checks': [['pc_in_network', pc, topo['network']]]}


def f_pc_wrong_mask(root, topo, rng):
    # /30 : le PC voit encore son voisin immédiat mais plus la passerelle -> panne subtile
    pc = _pick_pc(topo, rng, dhcp=False)
    _set(_wired_port(_devices(root)[pc].find('ENGINE')), 'SUBNET', '255.255.255.252')
    return {'device': pc,
            'cause': f'Masque de {pc} en 255.255.255.252 au lieu de {topo["mask"]}',
            'solution': f'Sur {pc} : masque = {topo["mask"]}',
            'checks': [['pc_mask', pc, topo['mask']]]}


def f_pc_wrong_dns(root, topo, rng):
    candidates = [n for n, d in topo['devices'].items() if d.get('dns')]
    pc = _pick_device(topo, rng, candidates)
    correct = topo['devices'][pc]['dns']
    wrong = ipaddress.IPv4Address(correct)
    wrong = str(wrong + 1 if int(wrong) % 2 == 0 else wrong - 1)
    _set(_wired_port(_devices(root)[pc].find('ENGINE')), 'PORT_DNS', wrong)
    return {'device': pc,
            'cause': f'DNS de {pc} à {wrong} au lieu de {correct} : les sites web par nom ne s\'ouvrent plus, '
                     f'mais tout fonctionne encore par adresse IP',
            'solution': f'Sur {pc} : Desktop > IP Configuration > DNS Server = {correct}',
            'checks': [['pc_dns', pc, correct]]}


def f_pc_firewall_enabled(root, topo, rng):
    # Pare-feu local du poste (Desktop > Firewall dans PT) activé par erreur :
    # bloque le trafic ENTRANT vers ce poste (ping, partage...), mais le poste
    # continue de sortir normalement lui-même — asymétrique, comme un vrai
    # pare-feu hôte.
    pc = _pick_pc(topo, rng)
    _set(_wired_port(_devices(root)[pc].find('ENGINE')), 'PC_FIREWALL', 'true')
    return {'device': pc,
            'cause': f'{pc} : pare-feu local activé, plus personne ne peut le joindre (ping, partage...) '
                     f'alors qu\'il continue de sortir normalement lui-même',
            'solution': f'Sur {pc} : Desktop > Firewall > Désactiver',
            'checks': [['pc_firewall', pc, False]]}


def f_router_interface_shutdown(root, topo, rng):
    engine = _devices(root)['R1'].find('ENGINE')
    iface = next(iter(topo['devices']['R1']['interfaces']))
    lines = _config_lines(engine)
    start, end = _interface_block(lines, iface)
    block = [l for l in lines[start + 1:end] if l.strip() != 'no shutdown'] + [' shutdown']
    _write_config(engine, lines[:start + 1] + block + lines[end:])
    return {'device': 'R1',
            'cause': f'Interface {iface} de R1 administrativement éteinte (shutdown)',
            'solution': f'R1 : interface {iface} → no shutdown (puis copy run start)',
            'checks': [['iface_up', 'R1', iface]]}


def f_router_wrong_ip(root, topo, rng):
    engine = _devices(root)['R1'].find('ENGINE')
    iface, cfg = next(iter(topo['devices']['R1']['interfaces'].items()))
    net = ipaddress.IPv4Network(topo['network'])
    wrong = str(net.network_address + 254)
    lines = _config_lines(engine)
    start, end = _interface_block(lines, iface)   # seulement l'interface du LAN, pas celle de l'admin
    lines[start + 1:end] = [f' ip address {wrong} {cfg["mask"]}' if l.strip().startswith('ip address') else l
                            for l in lines[start + 1:end]]
    _write_config(engine, lines)
    return {'device': 'R1',
            'cause': f'IP de R1 {iface} à {wrong} au lieu de {cfg["ip"]} (la passerelle des PC)',
            'solution': f'R1 : interface {iface} → ip address {cfg["ip"]} {cfg["mask"]}',
            'checks': [['iface_ip', 'R1', iface, cfg['ip']]]}


def f_cable_missing(root, topo, rng):
    links = root.find('NETWORK/LINKS')
    order = [d.findtext('ENGINE/NAME') for d in root.find('NETWORK/DEVICES').findall('DEVICE')]
    pc = _pick_pc(topo, rng)
    idx = str(order.index(pc))
    for link in links.findall('LINK'):
        c = link.find('CABLE')
        if idx in (c.findtext('FROM'), c.findtext('TO')):
            ports = [p.text for p in c.findall('PORT')]
            links.remove(link)
            break
    # Déduit le switch côté PC depuis la topo plutôt que de supposer 'S1' :
    # vrai sur simple_lan/dhcp_lan, faux dans un gabarit à plusieurs switchs.
    other, sw_port = _pc_access_point(topo, pc)
    return {'device': pc,
            'cause': f'Câble débranché entre {pc} et {other} ({sw_port})',
            'solution': f'Rebrancher {pc} FastEthernet0 ↔ {other} {sw_port} (câble droit)',
            'checks': [['link', pc, other]]}


def f_pc_power_off(root, topo, rng):
    pc = _pick_pc(topo, rng)
    _set(_devices(root)[pc].find('ENGINE'), 'POWER', 'false')
    return {'device': pc,
            'cause': f'{pc} éteint',
            'solution': f'Allumer {pc} (onglet Physical, bouton d\'alimentation)',
            'checks': [['power', pc, True]]}


def f_dhcp_wrong_default_router(root, topo, rng):
    engine = _devices(root)['R1'].find('ENGINE')
    net = ipaddress.IPv4Network(topo['network'])
    wrong = str(net.network_address + 254)
    lines = [f' default-router {wrong}' if l.strip().startswith('default-router') else l
             for l in _config_lines(engine)]
    _write_config(engine, lines)
    return {'device': 'R1',
            'cause': f'Le pool DHCP distribue la passerelle {wrong} au lieu de {topo["gateway"]}',
            'solution': f'R1 : ip dhcp pool {topo["dhcp_pool"]} → default-router {topo["gateway"]}, '
                        f'puis renouveler l\'IP des PC',
            'checks': [['dhcp_default_router', 'R1', topo['gateway']]]}


def f_dhcp_wrong_network(root, topo, rng):
    engine = _devices(root)['R1'].find('ENGINE')
    net = ipaddress.IPv4Network(topo['network'])
    wrong = ipaddress.IPv4Network(f'{net.network_address + 256}/24')
    lines = [f' network {wrong.network_address} {topo["mask"]}' if l.strip().startswith('network ') else l
             for l in _config_lines(engine)]
    _write_config(engine, lines)
    return {'device': 'R1',
            'cause': f'Pool DHCP déclaré sur {wrong} au lieu de {net} : aucun bail distribué',
            'solution': f'R1 : ip dhcp pool {topo["dhcp_pool"]} → network {net.network_address} {topo["mask"]}',
            'checks': [['dhcp_network', 'R1', str(net)]]}


def f_switch_no_default_gateway(root, topo, rng):
    # Invisible depuis le LAN : ne se voit que depuis un AUTRE réseau (PC-ADMIN)
    engine = _devices(root)['S1'].find('ENGINE')
    gw = topo['devices']['S1']['mgmt']['gateway']
    _write_config(engine, [l for l in _config_lines(engine) if not l.startswith('ip default-gateway')])
    return {'device': 'S1',
            'cause': 'S1 n\'a plus de passerelle par défaut : il reçoit les pings de PC-ADMIN '
                     'mais ne sait pas où envoyer ses réponses (autre réseau)',
            'solution': f'S1 : ip default-gateway {gw} (puis copy run start)',
            'checks': [['sw_default_gateway', 'S1', gw]]}


def f_switch_svi_shutdown(root, topo, rng):
    engine = _devices(root)['S1'].find('ENGINE')
    lines = _config_lines(engine)
    start, end = _interface_block(lines, 'Vlan1')
    block = [l for l in lines[start + 1:end] if l.strip() != 'no shutdown'] + [' shutdown']
    _write_config(engine, lines[:start + 1] + block + lines[end:])
    return {'device': 'S1',
            'cause': 'Interface de management Vlan1 de S1 éteinte (shutdown) : switch injoignable, '
                     'alors que la commutation des postes fonctionne',
            'solution': 'S1 : interface vlan 1 → no shutdown (puis copy run start)',
            'checks': [['iface_up', 'S1', 'Vlan1']]}


# ─── Pannes multi-sites (OSPF / NAT) ──────────────────────────────────────────
# Topologie 'multisite_ospf_nat' uniquement (voir builder.py). Conventions et
# variantes confirmées sur de vrais labs NetAcad/CCNA, voir docs/RULES_TOPOLOGIES.md.

def f_ospf_network_missing(root, topo, rng):
    candidates = [n for n, d in topo['devices'].items() if d.get('ospf_networks')]
    router = _pick_device(topo, rng, candidates)
    net_str, area = rng.choice(topo['devices'][router]['ospf_networks'])
    net = ipaddress.IPv4Network(net_str)
    target_line = f' network {net.network_address} {net.hostmask} area {area}'
    engine = _devices(root)[router].find('ENGINE')
    lines = [l for l in _config_lines(engine) if l != target_line]
    _write_config(engine, lines)
    return {'device': router,
            'cause': f'{router} n\'annonce plus le réseau {net_str} dans OSPF (ligne network manquante)',
            'solution': f'{router} : router ospf 1 → {target_line.strip()}',
            'checks': [['ospf_network', router, net_str]]}


def f_wan_wrong_ip(root, topo, rng):
    candidates = [n for n, d in topo['devices'].items() if d.get('wan_iface')]
    router = _pick_device(topo, rng, candidates)
    iface = topo['devices'][router]['wan_iface']
    cfg = topo['devices'][router]['interfaces'][iface]
    correct_net = ipaddress.IPv4Network(f'{cfg["ip"]}/{cfg["mask"]}', strict=False)
    # Décale vers le bloc /30 voisin (même panne que celle confirmée sur un vrai lab :
    # IP déplacée dans un autre sous-réseau que celui du lien, casse l'adjacence OSPF).
    wrong_base = ipaddress.IPv4Address(int(correct_net.network_address) + correct_net.num_addresses)
    wrong_net = ipaddress.IPv4Network(f'{wrong_base}/{correct_net.prefixlen}', strict=False)
    wrong_ip = str(wrong_net.network_address + 2)
    engine = _devices(root)[router].find('ENGINE')
    lines = _config_lines(engine)
    start, end = _interface_block(lines, iface)
    lines[start + 1:end] = [f' ip address {wrong_ip} {cfg["mask"]}' if l.strip().startswith('ip address') else l
                            for l in lines[start + 1:end]]
    _write_config(engine, lines)
    return {'device': router,
            'cause': f'IP de {router} {iface} à {wrong_ip} au lieu de {cfg["ip"]} (lien WAN vers R-EDGE, '
                     f'hors du bon sous-réseau)',
            'solution': f'{router} : interface {iface} → ip address {cfg["ip"]} {cfg["mask"]}',
            'checks': [['iface_ip', router, iface, cfg['ip']]]}


def f_nat_inside_missing(root, topo, rng):
    candidates = [n for n, d in topo['devices'].items() if d.get('nat_inside_ifaces')]
    router = _pick_device(topo, rng, candidates)
    iface = rng.choice(topo['devices'][router]['nat_inside_ifaces'])
    engine = _devices(root)[router].find('ENGINE')
    lines = _config_lines(engine)
    start, end = _interface_block(lines, iface)
    block = [l for l in lines[start + 1:end] if l.strip() != 'ip nat inside']
    _write_config(engine, lines[:start + 1] + block + lines[end:])
    return {'device': router,
            'cause': f'{router} : "ip nat inside" absent sur {iface}, traduction NAT cassée pour ce site',
            'solution': f'{router} : interface {iface} → ip nat inside',
            'checks': [['nat_inside', router, iface]]}


def f_default_route_wrong_nexthop(root, topo, rng):
    # Confirmé sur un vrai lab officiel CCNA (SRWE 16.3.1 Troubleshoot Static
    # and Default Routes, voir docs/BACKLOG_EXERCICES.md) : route par défaut
    # pointant vers une adresse qui n'existe sur aucun appareil du lien, au
    # lieu du voisin réel. Décale vers le bloc /30 voisin (même mécanique que
    # f_wan_wrong_ip) plutôt que d'utiliser l'adresse de broadcast du lien :
    # un /30 n'a que 2 adresses d'hôte, déjà prises par les 2 extrémités, et
    # Damien a relevé (Catalogue_pannes_Packet_Tracer_Damien.pdf, fiche 31)
    # qu'IOS/PT peut refuser un next-hop égal au broadcast d'un sous-réseau
    # connecté — autant éviter le risque avec un mécanisme déjà utilisé.
    router = 'R-EDGE'
    correct = topo['devices'][router]['default_route_next_hop']
    out_iface = topo['devices'][router]['nat_outside_iface']
    cfg = topo['devices'][router]['interfaces'][out_iface]
    net = ipaddress.IPv4Network(f'{cfg["ip"]}/{cfg["mask"]}', strict=False)
    wrong_base = ipaddress.IPv4Address(int(net.network_address) + net.num_addresses)
    wrong_net = ipaddress.IPv4Network(f'{wrong_base}/{net.prefixlen}', strict=False)
    wrong = str(wrong_net.network_address + 2)
    engine = _devices(root)[router].find('ENGINE')
    lines = [f'ip route 0.0.0.0 0.0.0.0 {wrong}' if l.strip().startswith('ip route 0.0.0.0 0.0.0.0') else l
             for l in _config_lines(engine)]
    _write_config(engine, lines)
    return {'device': router,
            'cause': f'{router} : route par défaut vers {wrong}, qui n\'existe sur aucun appareil '
                     f'(au lieu de {correct}, l\'interface de l\'ISP)',
            'solution': f'{router} : ip route 0.0.0.0 0.0.0.0 {correct}',
            'checks': [['default_route', router, correct]]}


def f_stp_root_priority_missing(root, topo, rng):
    # Confirmé sur un vrai lab officiel CCNA (ENSA 12.5.13 Troubleshoot
    # Enterprise Networks, voir docs/BACKLOG_EXERCICES.md) : priorité STP
    # absente sur le switch censé être root bridge du VLAN.
    candidates = [n for n, d in topo['devices'].items() if d.get('stp_priority')]
    switch = _pick_device(topo, rng, candidates)
    prio = topo['devices'][switch]['stp_priority']
    target_line = f'spanning-tree vlan {prio["vlan"]} priority {prio["priority"]}'
    engine = _devices(root)[switch].find('ENGINE')
    lines = [l for l in _config_lines(engine) if l.strip() != target_line]
    _write_config(engine, lines)
    return {'device': switch,
            'cause': f'{switch} a perdu sa priorité STP ({target_line}) : il n\'est plus garanti d\'être '
                     f'root bridge, l\'arbre de recouvrement peut bloquer un port différent sur le lien redondant',
            'solution': f'{switch} : {target_line}',
            'checks': [['stp_priority', switch, prio['vlan'], prio['priority']]]}


def f_nat_outside_missing(root, topo, rng):
    router = 'R-EDGE'
    iface = topo['devices'][router]['nat_outside_iface']
    engine = _devices(root)[router].find('ENGINE')
    lines = _config_lines(engine)
    start, end = _interface_block(lines, iface)
    block = [l for l in lines[start + 1:end] if l.strip() != 'ip nat outside']
    _write_config(engine, lines[:start + 1] + block + lines[end:])
    return {'device': router,
            'cause': f'{router} : "ip nat outside" absent sur {iface}, la traduction NAT ne se déclenche plus '
                     f'pour le trafic sortant vers Internet',
            'solution': f'{router} : interface {iface} → ip nat outside',
            'checks': [['nat_outside', router, iface]]}


def f_pat_rule_missing(root, topo, rng):
    router = 'R-EDGE'
    acl = topo['devices'][router]['nat_acl']
    iface = topo['devices'][router]['nat_outside_iface']
    target = f'ip nat inside source list {acl} interface {iface} overload'
    engine = _devices(root)[router].find('ENGINE')
    lines = [l for l in _config_lines(engine) if l.strip() != target]
    _write_config(engine, lines)
    return {'device': router,
            'cause': f'{router} : la règle de surcharge NAT ("{target}") a disparu, plus aucune traduction '
                     f'ne se fait malgré des interfaces inside/outside correctement marquées',
            'solution': f'{router} : {target}',
            'checks': [['pat_rule', router, acl, iface]]}


def f_switch_svi_wrong_ip(root, topo, rng):
    engine = _devices(root)['S1'].find('ENGINE')
    m = topo['devices']['S1']['mgmt']
    net = ipaddress.IPv4Network(f'{m["ip"]}/{m["mask"]}', strict=False)
    wrong = str(net.network_address + 254)
    lines = _config_lines(engine)
    start, end = _interface_block(lines, 'Vlan1')
    lines[start + 1:end] = [f' ip address {wrong} {m["mask"]}' if l.strip().startswith('ip address') else l
                            for l in lines[start + 1:end]]
    _write_config(engine, lines)
    return {'device': 'S1',
            'cause': f'S1 : adresse de management Vlan1 à {wrong} au lieu de {m["ip"]}',
            'solution': f'S1 : interface Vlan1 → ip address {m["ip"]} {m["mask"]}',
            'checks': [['iface_addr', 'S1', 'Vlan1', m['ip'], m['mask']]]}


def f_hostname_wrong(root, topo, rng):
    candidates = [n for n, d in topo['devices'].items() if d['type'] in ('router', 'switch')]
    name = _pick_device(topo, rng, candidates)
    wrong = f'{name}-TMP'
    engine = _devices(root)[name].find('ENGINE')
    lines = [f'hostname {wrong}' if l.strip().startswith('hostname ') else l for l in _config_lines(engine)]
    _write_config(engine, lines)
    return {'device': name,
            'cause': f'{name} : renommé en hostname "{wrong}", ne correspond plus à l\'inventaire réseau',
            'solution': f'{name} : hostname {name}',
            'checks': [['hostname', name, name]]}


def f_ospf_wrong_area(root, topo, rng):
    # Confirmé proche d'un pattern réel (secteur OSPF incohérent entre 2
    # routeurs du même lien, voir Catalogue_pannes_Packet_Tracer_Damien.pdf
    # fiche 35) : le lien reste joignable en IP, mais l'adjacence OSPF ne se
    # forme plus puisque les 2 extrémités ne sont pas dans la même area.
    candidates = [n for n, d in topo['devices'].items() if d.get('ospf_networks')]
    router = _pick_device(topo, rng, candidates)
    net_str, area = rng.choice(topo['devices'][router]['ospf_networks'])
    net = ipaddress.IPv4Network(net_str)
    target_line = f' network {net.network_address} {net.hostmask} area {area}'
    wrong_line = f' network {net.network_address} {net.hostmask} area {area + 1}'
    engine = _devices(root)[router].find('ENGINE')
    lines = [wrong_line if l == target_line else l for l in _config_lines(engine)]
    _write_config(engine, lines)
    return {'device': router,
            'cause': f'{router} : {net_str} annoncé en area {area + 1} au lieu de {area} (voisin incompatible)',
            'solution': f'{router} : router ospf 1 → {target_line.strip()}',
            'checks': [['ospf_network', router, net_str, area]]}


def f_ospf_transit_passive(root, topo, rng):
    # Confirmé proche d'un pattern réel (interface de transit déclarée
    # passive par erreur, fiche 36) : le lien répond au ping mais l'adjacence
    # OSPF ne se forme plus puisqu'une interface passive n'envoie plus de
    # paquets Hello.
    candidates = [n for n, d in topo['devices'].items() if d.get('wan_iface')]
    router = _pick_device(topo, rng, candidates)
    iface = topo['devices'][router]['wan_iface']
    engine = _devices(root)[router].find('ENGINE')
    lines = _config_lines(engine)
    start, _ = _router_ospf_block(lines)
    lines.insert(start + 1, f' passive-interface {iface}')
    _write_config(engine, lines)
    return {'device': router,
            'cause': f'{router} : {iface} déclarée passive dans OSPF alors qu\'un voisin y est bien connecté '
                     f'(plus de paquets Hello envoyés sur ce lien)',
            'solution': f'{router} : router ospf 1 → no passive-interface {iface}',
            'checks': [['ospf_not_passive', router, iface]]}


def f_ospf_timer_mismatch(root, topo, rng):
    # Confirmé proche d'un pattern réel (timers hello/dead personnalisés sur
    # un seul côté d'un lien, fiche 37) : le lien IP fonctionne mais le
    # voisinage OSPF ne reste jamais stable (timers incompatibles entre les
    # 2 extrémités).
    candidates = [n for n, d in topo['devices'].items() if d.get('wan_iface')]
    router = _pick_device(topo, rng, candidates)
    iface = topo['devices'][router]['wan_iface']
    engine = _devices(root)[router].find('ENGINE')
    lines = _config_lines(engine)
    start, end = _interface_block(lines, iface)
    block = lines[start + 1:end] + [' ip ospf hello-interval 5', ' ip ospf dead-interval 20']
    _write_config(engine, lines[:start + 1] + block + lines[end:])
    return {'device': router,
            'cause': f'{router} : {iface} a des timers OSPF personnalisés (hello 5 / dead 20) incompatibles '
                     f'avec les valeurs par défaut utilisées en face',
            'solution': f'{router} : interface {iface} → no ip ospf hello-interval, no ip ospf dead-interval',
            'checks': [['ospf_default_timers', router, iface]]}


# ─── Pannes VLAN / trunk / routeur-bâton ──────────────────────────────────────
# Topologie 'vlan_trunk' uniquement (voir builder.py). Patterns tirés du
# catalogue soumis par Damien (Catalogue_pannes_Packet_Tracer_Damien.pdf),
# rendus procéduraux : aucune valeur de son exemple illustratif n'est reprise
# telle quelle, tout est lu depuis topo['devices']/topo['links'] du lab réel.

def f_access_wrong_vlan(root, topo, rng):
    candidates = [n for n, d in topo['devices'].items() if d.get('access_vlan') is not None]
    pc = _pick_device(topo, rng, candidates)
    sw, iface = _pc_access_point(topo, pc)
    correct_vlan = topo['devices'][pc]['access_vlan']
    # Seuls 2 VLAN existent dans ce gabarit : bascule vers l'autre.
    wrong_vlan = next(d['access_vlan'] for d in topo['devices'].values()
                      if d.get('access_vlan') not in (None, correct_vlan))
    engine = _devices(root)[sw].find('ENGINE')
    lines = _config_lines(engine)
    start, end = _interface_block(lines, iface)
    block = [f' switchport access vlan {wrong_vlan}' if l.strip().startswith('switchport access vlan') else l
             for l in lines[start + 1:end]]
    _write_config(engine, lines[:start + 1] + block + lines[end:])
    return {'device': pc,
            'cause': f'{pc} : port {iface} de {sw} basculé sur le VLAN {wrong_vlan} au lieu de {correct_vlan}',
            'solution': f'{sw} : interface {iface} → switchport access vlan {correct_vlan}',
            'checks': [['access_vlan', sw, iface, correct_vlan]]}


def f_vlan_missing(root, topo, rng):
    candidates = [n for n, d in topo['devices'].items() if d.get('vlans')]
    switch = _pick_device(topo, rng, candidates)
    vid = rng.choice(list(topo['devices'][switch]['vlans']))
    name = topo['devices'][switch]['vlans'][vid]
    engine = _devices(root)[switch].find('ENGINE')
    lines = _config_lines(engine)
    start, end = _vlan_block(lines, vid)
    _write_config(engine, lines[:start] + lines[end:])
    return {'device': switch,
            'cause': f'{switch} : VLAN {vid} supprimé de la base ({name}), les ports qui y étaient affectés '
                     f'perdent leur connectivité',
            'solution': f'{switch} : vlan {vid} puis name {name}',
            'checks': [['vlan_exists', switch, vid]]}


def f_trunk_access_mode(root, topo, rng):
    candidates = [n for n, d in topo['devices'].items() if d.get('trunk_ifaces')]
    sw = _pick_device(topo, rng, candidates)
    iface = rng.choice(list(topo['devices'][sw]['trunk_ifaces']))
    engine = _devices(root)[sw].find('ENGINE')
    lines = _config_lines(engine)
    start, end = _interface_block(lines, iface)
    block = [l for l in lines[start + 1:end] if l.strip() != 'switchport mode trunk']
    block += [' switchport mode access', ' switchport access vlan 1']
    _write_config(engine, lines[:start + 1] + block + lines[end:])
    return {'device': sw,
            'cause': f'{sw} : {iface} repassé en mode access (VLAN 1) au lieu de trunk, le lien ne transporte '
                     f'plus les VLAN utilisateurs',
            'solution': f'{sw} : interface {iface} → switchport mode trunk',
            'checks': [['trunk_mode', sw, iface]]}


def f_trunk_vlan_filtered(root, topo, rng):
    candidates = [n for n, d in topo['devices'].items() if d.get('trunk_ifaces')]
    sw = _pick_device(topo, rng, candidates)
    iface = rng.choice(list(topo['devices'][sw]['trunk_ifaces']))
    allowed = topo['devices'][sw]['trunk_ifaces'][iface]
    removed = rng.choice(allowed)
    kept = ','.join(str(v) for v in allowed if v != removed)
    engine = _devices(root)[sw].find('ENGINE')
    lines = _config_lines(engine)
    start, end = _interface_block(lines, iface)
    block = [f' switchport trunk allowed vlan {kept}' if l.strip().startswith('switchport trunk allowed vlan') else l
             for l in lines[start + 1:end]]
    _write_config(engine, lines[:start + 1] + block + lines[end:])
    return {'device': sw,
            'cause': f'{sw} : VLAN {removed} retiré de la liste autorisée sur le trunk {iface}, ce VLAN ne '
                     f'traverse plus ce lien',
            'solution': f'{sw} : interface {iface} → switchport trunk allowed vlan '
                        f'{",".join(str(v) for v in allowed)}',
            'checks': [['trunk_allowed_vlan', sw, iface, removed]]}


def f_dot1q_wrong_vlan(root, topo, rng):
    # Confirmé sur un vrai lab officiel CCNA (SRWE 4.4.8 Troubleshoot
    # Inter-VLAN Routing, voir docs/BACKLOG_EXERCICES.md) : VLAN ID interverti
    # entre 2 sous-interfaces d'un routeur bâton.
    router = 'R1'
    sub_ifaces = list(topo['devices'][router]['subinterfaces'])
    iface = rng.choice(sub_ifaces)
    correct_vlan = topo['devices'][router]['subinterfaces'][iface]['vlan']
    wrong_vlan = next(v['vlan'] for i, v in topo['devices'][router]['subinterfaces'].items() if i != iface)
    engine = _devices(root)[router].find('ENGINE')
    lines = _config_lines(engine)
    start, end = _interface_block(lines, iface)
    block = [f' encapsulation dot1Q {wrong_vlan}' if l.strip().startswith('encapsulation dot1Q') else l
             for l in lines[start + 1:end]]
    _write_config(engine, lines[:start + 1] + block + lines[end:])
    return {'device': router,
            'cause': f'{router} : {iface} tagguée en dot1Q {wrong_vlan} au lieu de {correct_vlan}, ce VLAN ne '
                     f'reçoit plus son routage',
            'solution': f'{router} : interface {iface} → encapsulation dot1Q {correct_vlan}',
            'checks': [['dot1q_vlan', router, iface, correct_vlan]]}


def f_subinterface_shutdown(root, topo, rng):
    router = 'R1'
    iface = rng.choice(list(topo['devices'][router]['subinterfaces']))
    engine = _devices(root)[router].find('ENGINE')
    lines = _config_lines(engine)
    start, end = _interface_block(lines, iface)
    block = [l for l in lines[start + 1:end] if l.strip() != 'no shutdown'] + [' shutdown']
    _write_config(engine, lines[:start + 1] + block + lines[end:])
    return {'device': router,
            'cause': f'{router} : sous-interface {iface} administrativement éteinte (shutdown)',
            'solution': f'{router} : interface {iface} → no shutdown',
            'checks': [['iface_up', router, iface]]}


# ─── Pannes ACL (multisite_ospf_nat) ──────────────────────────────────────────
# L'ACL 120 (icmp + http vers WEB uniquement) est posée dans le gabarit
# lui-même comme politique de sécurité volontaire, pas une porte grande
# ouverte (voir builder.py). Patterns tirés du catalogue de Damien (fiches
# 42/43), rendus procéduraux : chaque fonction retire UNE des 2 lignes de
# l'ACL réelle de ce lab, jamais une valeur recopiée de l'exemple du PDF.

def f_acl_wrong_direction(root, topo, rng):
    # Classique CCNA : l'ACL elle-même est correcte, mais appliquée "out"
    # au lieu de "in" (ou l'inverse) sur l'interface — elle ne filtre plus
    # le trafic censé être contrôlé.
    router = 'R-EDGE'
    iface = rng.choice(list(topo['devices'][router]['acl_applied']))
    num, direction = topo['devices'][router]['acl_applied'][iface]
    wrong_direction = 'out' if direction == 'in' else 'in'
    engine = _devices(root)[router].find('ENGINE')
    lines = _config_lines(engine)
    start, end = _interface_block(lines, iface)
    block = [f' ip access-group {num} {wrong_direction}' if l.strip() == f'ip access-group {num} {direction}' else l
             for l in lines[start + 1:end]]
    _write_config(engine, lines[:start + 1] + block + lines[end:])
    return {'device': router,
            'cause': f'{router} : ACL {num} appliquée en "{wrong_direction}" au lieu de "{direction}" sur '
                     f'{iface}, elle ne filtre plus le trafic attendu',
            'solution': f'{router} : interface {iface} → ip access-group {num} {direction}',
            'checks': [['acl_direction', router, iface, num, direction]]}


def f_acl_http_denied(root, topo, rng):
    router = 'R-EDGE'
    line = next(l for l in topo['devices'][router]['acl_lines'] if ' tcp ' in l)
    engine = _devices(root)[router].find('ENGINE')
    lines = [l for l in _config_lines(engine) if l.strip() != line]
    _write_config(engine, lines)
    return {'device': router,
            'cause': f'{router} : ligne ACL "{line}" supprimée, le ping vers le serveur web passe '
                     f'toujours mais plus la page HTTP',
            'solution': f'{router} : {line}',
            'checks': [['acl_line', router, line]]}


def f_acl_implicit_deny(root, topo, rng):
    router = 'R-EDGE'
    line = next(l for l in topo['devices'][router]['acl_lines'] if ' icmp ' in l)
    engine = _devices(root)[router].find('ENGINE')
    lines = [l for l in _config_lines(engine) if l.strip() != line]
    _write_config(engine, lines)
    return {'device': router,
            'cause': f'{router} : ligne ACL "{line}" supprimée, la page HTTP du serveur web reste '
                     f'accessible mais le ping ne passe plus (deny implicite)',
            'solution': f'{router} : {line}',
            'checks': [['acl_line', router, line]]}


# ─── Pannes EtherChannel (etherchannel) ────────────────────────────────────────
# Baseline volontairement asymétrique (S1 active / S2 passive, voir
# builder.py) : patterns tirés du catalogue de Damien (fiche 49) et d'une
# vraie soumission étudiante (docs/BACKLOG_EXERCICES.md), rendus procéduraux.

def f_port_security_wrong_mac(root, topo, rng):
    # La vraie MAC du PC est générée aléatoirement par le moteur et lue après
    # coup (voir builder.py::_post_build_port_security) : la panne remplace
    # la bonne adresse statique par une MAC inventée (convention reprise de
    # Catalogue_pannes_Packet_Tracer_Damien.pdf fiche 47 pour la valeur
    # factice, jamais pour une vraie adresse).
    candidates = [n for n, d in topo['devices'].items() if d.get('port_security_lines')]
    switch = _pick_device(topo, rng, candidates)
    iface, mac_info = next(iter(topo['devices'][switch]['port_security_lines'].items()))
    correct_mac = mac_info['mac']
    wrong_mac = '0000.0000.0099' if correct_mac != '0000.0000.0099' else '0000.0000.0098'
    engine = _devices(root)[switch].find('ENGINE')
    lines = _config_lines(engine)
    start, end = _interface_block(lines, iface)
    block = [f' switchport port-security mac-address {wrong_mac}'
             if l.strip().startswith('switchport port-security mac-address') else l
             for l in lines[start + 1:end]]
    _write_config(engine, lines[:start + 1] + block + lines[end:])
    return {'device': switch,
            'cause': f'{switch} : {iface} autorise la MAC {wrong_mac} au lieu de la vraie MAC du poste '
                     f'({correct_mac}), le trafic est bloqué par le port-security',
            'solution': f'{switch} : interface {iface} → switchport port-security mac-address {correct_mac}',
            'checks': [['port_security_mac', switch, iface, correct_mac]]}


def f_lacp_both_passive(root, topo, rng):
    candidates = [n for n, d in topo['devices'].items() if d.get('etherchannel', {}).get('mode') == 'active']
    switch = _pick_device(topo, rng, candidates)
    ec = topo['devices'][switch]['etherchannel']
    engine = _devices(root)[switch].find('ENGINE')
    lines = _config_lines(engine)
    for iface in ec['members']:
        start, end = _interface_block(lines, iface)
        lines[start + 1:end] = [f' channel-group {ec["group"]} mode passive'
                                if l.strip().startswith('channel-group') else l for l in lines[start + 1:end]]
    _write_config(engine, lines)
    return {'device': switch,
            'cause': f'{switch} : les ports du bundle repassés en LACP passive, plus aucun côté ne '
                     f'négocie activement — l\'agrégat ne se forme plus',
            'solution': f'{switch} : channel-group {ec["group"]} mode {ec["mode"]} sur {", ".join(ec["members"])}',
            'checks': [['channel_group', switch, iface, ec['group'], ec['mode']] for iface in ec['members']]}


def f_channel_mode_access(root, topo, rng):
    # Confirmé par une vraie soumission étudiante (docs/BACKLOG_EXERCICES.md) :
    # un port du bundle resté en switchport mode access au lieu de trunk/channel.
    candidates = [n for n, d in topo['devices'].items() if d.get('etherchannel')]
    switch = _pick_device(topo, rng, candidates)
    ec = topo['devices'][switch]['etherchannel']
    iface = rng.choice(ec['members'])
    engine = _devices(root)[switch].find('ENGINE')
    lines = _config_lines(engine)
    start, end = _interface_block(lines, iface)
    block = [l for l in lines[start + 1:end] if not l.strip().startswith('channel-group')]
    block.append(' switchport mode access')
    _write_config(engine, lines[:start + 1] + block + lines[end:])
    return {'device': switch,
            'cause': f'{switch} : {iface} sorti du bundle (repassé en switchport mode access au lieu '
                     f'de channel-group), l\'agrégat perd un port sur deux',
            'solution': f'{switch} : interface {iface} → channel-group {ec["group"]} mode {ec["mode"]}',
            'checks': [['channel_group', switch, iface, ec['group'], ec['mode']]]}


def f_channel_group_mismatch(root, topo, rng):
    # Les identifiants sont locaux : séparer UN membre sur le même switch.
    candidates = [n for n, d in topo['devices'].items() if d.get('etherchannel')]
    switch = _pick_device(topo, rng, candidates)
    ec = topo['devices'][switch]['etherchannel']
    wrong_group = ec['group'] + 1
    iface = rng.choice(ec['members'])
    engine = _devices(root)[switch].find('ENGINE')
    lines = _config_lines(engine)
    start, end = _interface_block(lines, iface)
    lines[start + 1:end] = [f' channel-group {wrong_group} mode {ec["mode"]}'
                            if l.strip().startswith('channel-group') else l for l in lines[start + 1:end]]
    _write_config(engine, lines)
    return {'device': switch,
            'cause': f'{switch} : {iface} est dans le groupe {wrong_group}, les autres membres '
                     f'restent dans le groupe {ec["group"]} sur ce même switch ; le bundle est scindé',
            'solution': f'{switch} : interface {iface} → no channel-group {wrong_group}, puis '
                        f'channel-group {ec["group"]} mode {ec["mode"]}',
            'checks': [['channel_group', switch, member, ec['group'], ec['mode']] for member in ec['members']]}


# ─── Catalogue ───────────────────────────────────────────────────────────────
# level  = difficulté minimale
# topos  = topologies compatibles
# target = 'pc' (un PC tiré au hasard) ou nom d'appareil fixe ('R1') :
#          sert à ne jamais mettre deux pannes sur le même appareil.
# hidden = True si la panne n'est détectable QUE depuis un autre réseau
#          (supervision PC-ADMIN), jamais par une plainte utilisateur directe.

CATALOGUE = {
    'pc_wrong_gateway':          {'fn': f_pc_wrong_gateway,          'level': 1, 'theme': 'adressage', 'target': 'pc', 'topos': ['simple_lan'], 'hidden': False},
    'pc_wrong_ip':               {'fn': f_pc_wrong_ip,               'level': 1, 'theme': 'adressage', 'target': 'pc', 'topos': ['simple_lan'], 'hidden': False},
    'pc_wrong_dns':              {'fn': f_pc_wrong_dns,              'level': 1, 'theme': 'dns', 'target': 'pc', 'topos': ['multisite_ospf_nat'], 'hidden': False},
    'pc_power_off':              {'fn': f_pc_power_off,              'level': 1, 'theme': 'materiel',  'target': 'pc', 'topos': ['simple_lan', 'dhcp_lan', 'switched_redundant', 'vlan_trunk', 'etherchannel'], 'hidden': False},
    'cable_missing':             {'fn': f_cable_missing,             'level': 1, 'theme': 'cablage',   'target': 'pc', 'topos': ['simple_lan', 'dhcp_lan', 'switched_redundant', 'vlan_trunk', 'etherchannel'], 'hidden': False},
    'router_interface_shutdown': {'fn': f_router_interface_shutdown, 'level': 1, 'theme': 'routeur',   'target': 'R1', 'topos': ['simple_lan', 'dhcp_lan'], 'hidden': False},
    'pc_wrong_mask':             {'fn': f_pc_wrong_mask,             'level': 2, 'theme': 'adressage', 'target': 'pc', 'topos': ['simple_lan'], 'hidden': False},
    'pc_firewall_enabled':       {'fn': f_pc_firewall_enabled,       'level': 1, 'theme': 'pare-feu', 'target': 'pc', 'topos': ['simple_lan', 'dhcp_lan', 'multisite_ospf_nat', 'switched_redundant', 'vlan_trunk', 'etherchannel'], 'hidden': False},
    'router_wrong_ip':           {'fn': f_router_wrong_ip,           'level': 2, 'theme': 'routeur',   'target': 'R1', 'topos': ['simple_lan'], 'hidden': False},
    'dhcp_wrong_default_router': {'fn': f_dhcp_wrong_default_router, 'level': 2, 'theme': 'dhcp',      'target': 'R1', 'topos': ['dhcp_lan'], 'hidden': False},
    'dhcp_wrong_network':        {'fn': f_dhcp_wrong_network,        'level': 2, 'theme': 'dhcp',      'target': 'R1', 'topos': ['dhcp_lan'], 'hidden': False},
    'switch_no_default_gateway': {'fn': f_switch_no_default_gateway, 'level': 2, 'theme': 'switch',    'target': 'S1', 'topos': ['simple_lan', 'dhcp_lan'], 'hidden': True},
    'switch_svi_shutdown':       {'fn': f_switch_svi_shutdown,       'level': 1, 'theme': 'switch',    'target': 'S1', 'topos': ['simple_lan', 'dhcp_lan', 'switched_redundant'], 'hidden': True},
    'switch_svi_wrong_ip':       {'fn': f_switch_svi_wrong_ip,       'level': 2, 'theme': 'switch',    'target': 'S1', 'topos': ['simple_lan', 'dhcp_lan', 'switched_redundant'], 'hidden': True},
    'ospf_network_missing':      {'fn': f_ospf_network_missing,      'level': 1, 'theme': 'routeur',   'target': 'multisite_router', 'topos': ['multisite_ospf_nat'], 'hidden': False},
    'wan_wrong_ip':              {'fn': f_wan_wrong_ip,              'level': 2, 'theme': 'routeur',   'target': 'multisite_router', 'topos': ['multisite_ospf_nat'], 'hidden': False},
    'nat_inside_missing':        {'fn': f_nat_inside_missing,        'level': 2, 'theme': 'nat',       'target': 'R-EDGE',           'topos': ['multisite_ospf_nat'], 'hidden': False},
    'default_route_wrong_nexthop': {'fn': f_default_route_wrong_nexthop, 'level': 2, 'theme': 'routage', 'target': 'R-EDGE', 'topos': ['multisite_ospf_nat'], 'hidden': False},
    'stp_root_priority_missing':   {'fn': f_stp_root_priority_missing,   'level': 2, 'theme': 'switch',  'target': 'stp_switch', 'topos': ['switched_redundant'], 'hidden': False},
    'nat_outside_missing':         {'fn': f_nat_outside_missing,         'level': 2, 'theme': 'nat',     'target': 'R-EDGE', 'topos': ['multisite_ospf_nat'], 'hidden': False},
    'pat_rule_missing':            {'fn': f_pat_rule_missing,            'level': 2, 'theme': 'nat',     'target': 'R-EDGE', 'topos': ['multisite_ospf_nat'], 'hidden': False},
    'hostname_wrong':              {'fn': f_hostname_wrong,              'level': 1, 'theme': 'conformite', 'target': 'any_device', 'topos': ['simple_lan', 'dhcp_lan', 'multisite_ospf_nat', 'switched_redundant', 'vlan_trunk', 'etherchannel'], 'hidden': False},
    'ospf_wrong_area':             {'fn': f_ospf_wrong_area,             'level': 2, 'theme': 'routeur', 'target': 'multisite_router', 'topos': ['multisite_ospf_nat'], 'hidden': False},
    'ospf_transit_passive':        {'fn': f_ospf_transit_passive,        'level': 2, 'theme': 'routeur', 'target': 'multisite_router', 'topos': ['multisite_ospf_nat'], 'hidden': False},
    'ospf_timer_mismatch':         {'fn': f_ospf_timer_mismatch,         'level': 2, 'theme': 'routeur', 'target': 'multisite_router', 'topos': ['multisite_ospf_nat'], 'hidden': False},
    'access_wrong_vlan':           {'fn': f_access_wrong_vlan,           'level': 2, 'theme': 'vlan', 'target': 'pc', 'topos': ['vlan_trunk'], 'hidden': False},
    'vlan_missing':                {'fn': f_vlan_missing,                'level': 2, 'theme': 'vlan', 'target': 'vlan_switch', 'topos': ['vlan_trunk'], 'hidden': False},
    'trunk_access_mode':           {'fn': f_trunk_access_mode,           'level': 2, 'theme': 'vlan', 'target': 'vlan_switch', 'topos': ['vlan_trunk'], 'hidden': False},
    'trunk_vlan_filtered':         {'fn': f_trunk_vlan_filtered,         'level': 2, 'theme': 'vlan', 'target': 'vlan_switch', 'topos': ['vlan_trunk'], 'hidden': False},
    'dot1q_wrong_vlan':            {'fn': f_dot1q_wrong_vlan,            'level': 2, 'theme': 'vlan', 'target': 'R1', 'topos': ['vlan_trunk'], 'hidden': False},
    'subinterface_shutdown':       {'fn': f_subinterface_shutdown,       'level': 1, 'theme': 'vlan', 'target': 'R1', 'topos': ['vlan_trunk'], 'hidden': False},
    'acl_http_denied':             {'fn': f_acl_http_denied,             'level': 2, 'theme': 'acl', 'target': 'R-EDGE', 'topos': ['multisite_ospf_nat'], 'hidden': False},
    'acl_implicit_deny':           {'fn': f_acl_implicit_deny,           'level': 2, 'theme': 'acl', 'target': 'R-EDGE', 'topos': ['multisite_ospf_nat'], 'hidden': False},
    'acl_wrong_direction':         {'fn': f_acl_wrong_direction,         'level': 2, 'theme': 'acl', 'target': 'R-EDGE', 'topos': ['multisite_ospf_nat'], 'hidden': False},
    'port_security_wrong_mac':     {'fn': f_port_security_wrong_mac,     'level': 2, 'theme': 'switch', 'target': 'S1', 'topos': ['simple_lan'], 'hidden': False},
    'lacp_both_passive':           {'fn': f_lacp_both_passive,           'level': 2, 'theme': 'etherchannel', 'target': 'ec_switch', 'topos': ['etherchannel'], 'hidden': False},
    'channel_mode_access':         {'fn': f_channel_mode_access,         'level': 2, 'theme': 'etherchannel', 'target': 'ec_switch', 'topos': ['etherchannel'], 'hidden': False},
    'channel_group_mismatch':      {'fn': f_channel_group_mismatch,      'level': 2, 'theme': 'etherchannel', 'target': 'ec_switch', 'topos': ['etherchannel'], 'hidden': False},
}

# Nombre de pannes simultanées selon la difficulté
FAULTS_PER_LEVEL = {1: 1, 2: 1, 3: 2}


def available(topo_name, level, theme=None, hidden=None):
    """hidden : None = toutes les pannes, True = seulement celles détectables
    uniquement depuis un autre réseau (supervision), False = seulement les
    pannes qu'un utilisateur normal peut signaler lui-même."""
    return [fid for fid, f in CATALOGUE.items()
            if topo_name in f['topos'] and f['level'] <= level and (theme in (None, f['theme']))
            and (hidden is None or f['hidden'] == hidden)]


def inject(topo, level=1, theme=None, fault_id=None, fault_ids=None, hidden=None, count=None,
           seed=None, output_path=None, lang='fr'):
    """
    Applique une ou plusieurs pannes au lab décrit par topo (issu de builder.build).
      fault_id/fault_ids : impose une panne précise, ou une liste de pannes précises
                            (le reste, s'il en manque pour atteindre `count`, est
                            tiré au hasard parmi les pannes compatibles).
      hidden   : filtre les pannes tirées au hasard (cf. available()). Ne s'applique
                 pas aux pannes imposées via fault_id/fault_ids.
      count    : nombre de pannes (par défaut selon le niveau).
      lang     : langue ('fr'/'en') du bloc Instructions embarqué dans le .pka.
    Deux pannes ne touchent jamais le même appareil.
    Écrit le .pka piégé + un fichier solution .json. Retourne la liste des rapports.
    """
    rng = random.Random(seed)
    count = count or FAULTS_PER_LEVEL.get(level, 1)
    topo = dict(topo, _busy=set())

    tree = ET.parse(topo['xml_path'])
    root = tree.getroot()
    reports = []
    wanted = list(fault_ids) if fault_ids else ([fault_id] if fault_id else [])

    while len(reports) < count:
        if wanted:
            fid = wanted.pop(0)
        else:
            used = {r['id'] for r in reports}
            choices = [f for f in available(topo['name'], level, theme, hidden=hidden)
                       if f not in used and CATALOGUE[f]['target'] not in topo['_busy']]
            if not choices:
                break  # plus de panne compatible : on s'arrête là
            fid = rng.choice(choices)
        try:
            report = CATALOGUE[fid]['fn'](root, topo, rng)
        except LookupError:
            continue  # ex. plus aucun PC libre pour cette panne
        report['id'] = fid
        topo['_busy'].add(report['device'])
        reports.append(report)

    if not reports:
        raise ValueError(f'Aucune panne pour {topo["name"]}, niveau {level}, thème {theme}')

    paragraphs = _ticket.scenario_paragraphs(reports, lang=lang, seed=seed)
    html_content = _instructions.build_html(lang, topo, paragraphs)
    title = _instructions.build_title(lang, len(reports))

    output_path = output_path or topo['pkt_path'].replace('.pkt', '_panne.pka')
    xml_path = output_path.rsplit('.', 1)[0] + '.xml'
    ET.indent(tree, space=' ')
    tree.write(xml_path, encoding='utf-8', xml_declaration=False, short_empty_elements=False)

    # Assemble le vrai wrapper d'activité PT (3 instantanés + arbres de
    # comparaison générés à partir d'un gabarit réel) plutôt que d'ajouter
    # <ACTIVITY> à la main : voir instructions.py et docs/RULES_TOPOLOGIES.md §7.
    # initial_state='generated' : l'apprenant démarre sur la panne injectée
    # (xml_path), pas sur un lab vierge ; topo['xml_path'] (jamais modifié,
    # encore sain à ce stade) sert de réseau-réponse pour COMPARISONS/INITIALSETUP.
    activity_xml = output_path.rsplit('.', 1)[0] + '_activity.xml'
    _activity.assemble_activity(
        base_xml_path=xml_path, template_path=_ACTIVITY_TEMPLATE, output_xml_path=activity_xml,
        pages=[{'title': title, 'content': html_content}],
        initial_state='generated', answer_xml_path=topo['xml_path'], title=title)
    with contextlib.redirect_stdout(io.StringIO()):
        _pte.ptfile_encode(activity_xml, output_path)
    os.remove(xml_path)
    os.remove(activity_xml)

    for r in reports:
        r['pkt_path'] = output_path
    solution = {'topology': {k: v for k, v in topo.items() if k not in ('xml_path', '_busy')},
                'faults': reports, 'pkt': output_path, 'lang': lang}
    with open(output_path.rsplit('.', 1)[0] + '_solution.json', 'w', encoding='utf-8') as f:
        json.dump(solution, f, ensure_ascii=False, indent=2)

    # Fiche HTML compagnon (indices progressifs + résultat attendu derrière
    # des boutons Montrer/Masquer) : utilisable même sans Packet Tracer ni
    # Python (contrairement à checker.py), voir worksheet.py.
    themes = {fid: info['theme'] for fid, info in CATALOGUE.items()}
    worksheet_html = _worksheet.build_worksheet_html(lang, topo, reports, paragraphs, themes=themes)
    with open(output_path.rsplit('.', 1)[0] + '.html', 'w', encoding='utf-8') as f:
        f.write(worksheet_html)

    return reports


if __name__ == '__main__':
    from builder import build
    for topo_name in ('simple_lan', 'dhcp_lan'):
        for seed in range(3):
            _, topo = build(topo_name, seed=seed, output_dir='/tmp')
            rs = inject(topo, level=3, seed=seed, output_path=f'/tmp/multi_{topo_name}_{seed}.pkt')
            print(f'[{topo_name}] ' + ' + '.join(f"{r['id']}({r['device']})" for r in rs))
