"""
builder.py — Construit une topologie saine en réutilisant le moteur du fork
TeodorPetrovic/tracketpacin (core.Lab), qui produit déjà des fichiers PT 9
valides (c'est lui qui a généré le .pka de test).

Ce qu'on ajoute par-dessus core.Lab :
  - le choix du MODÈLE exact (2911, 2960-24TT...) et pas seulement de la
    catégorie (router/switch/pc) : le fork prenait toujours le premier modèle
    trouvé (par ex. un routeur 8200) ;
  - le catalogue de 74 appareils (templates/packettracer/catalogue_source.xml),
    découvert automatiquement par le fork grâce au suffixe _source.xml ;
  - la passerelle des PC écrite aux deux endroits où PT la lit ;
  - un dictionnaire topology_info qui décrit l'état SAIN attendu, utilisé
    ensuite par faults.py (injection) et checker.py (vérification).
"""

import os
import sys
import io
import random
import ipaddress
import contextlib
import xml.etree.ElementTree as ET

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)

from core import Lab          # moteur du fork
import ptexplorer as _pte

ROUTER_Y, SWITCH_Y, PC_Y = 120, 320, 520


class PktLab(Lab):
    """core.Lab + choix du modèle exact via un type 'categorie:modele'."""

    def add(self, name, category, model, position, config=None, settings=None):
        profile = None
        if config:
            text = '\n'.join(config)
            profile = {'device_type': category, 'running_config': text, 'startup_config': text}
        return self.add_device(name, f'{category}:{model}', position=position,
                               profile=profile, settings=settings)

    def _pick_template(self, requested_type, template_map):
        if ':' in requested_type:
            wanted = requested_type.split(':', 1)[1]
            for bucket in template_map.values():
                for tpl in bucket:
                    t = tpl.find('ENGINE/TYPE')
                    if t is not None and t.get('model') == wanted:
                        return tpl
            raise ValueError(f'Modèle {wanted} absent des templates (catalogue_source.xml ?)')
        return super()._pick_template(requested_type, template_map)

    def _apply_settings(self, device_elem, dev_info):
        super()._apply_settings(device_elem, dev_info)
        gw = (dev_info.get('settings') or {}).get('default_gateway')
        if gw is not None:
            engine = device_elem.find('ENGINE')
            el = engine.find('GATEWAY')
            if el is None:
                el = ET.SubElement(engine, 'GATEWAY')
            el.text = gw


def switch_mgmt_config(name, ip, mask, gateway):
    """Config de base d'un switch administrable : adresse de management sur la SVI
    Vlan1 + passerelle par défaut (pour répondre aux machines des autres réseaux).
    PT ne stocke ces deux informations QUE dans la running-config (vérifié sur un
    fichier sauvegardé par PT 9)."""
    return [f'hostname {name}', '!', 'interface Vlan1', f' ip address {ip} {mask}', ' no shutdown', '!',
            f'ip default-gateway {gateway}', '!', 'end']


def admin_segment(rng):
    """Réseau d'administration (poste de l'informatique + supervision), relié à R1 G0/1.
    Sert à rendre observables les pannes qui ne se voient QUE depuis un autre réseau
    (ex. passerelle par défaut du switch absente). Plage 192.168.x.0/24, distincte
    des LAN en 10.x pour ne jamais les chevaucher."""
    net = ipaddress.IPv4Network(f'192.168.{rng.randint(100, 199)}.0/24')
    return {'network': str(net), 'gateway': str(net.network_address + 1), 'mask': '255.255.255.0',
            'pc_ip': str(net.network_address + 10), 'iface': 'GigabitEthernet0/1'}


def add_admin(lab, adm, x):
    """Pose PC-ADMIN relié directement à R1 (routeur <-> PC : câble croisé)."""
    lab.add('PC-ADMIN', 'pc', 'PC-PT', (x, ROUTER_Y), settings={
        'ip_address': adm['pc_ip'], 'subnet_mask': adm['mask'], 'default_gateway': adm['gateway'], 'dhcp': False})
    return ('R1', adm['iface'], 'PC-ADMIN', 'FastEthernet0', 'eCrossOver')


def admin_router_lines(adm):
    return [f'interface {adm["iface"]}', f' ip address {adm["gateway"]} {adm["mask"]}', ' no shutdown', '!']


# ─── Topologies ──────────────────────────────────────────────────────────────

def _random_lan(rng):
    return ipaddress.IPv4Network(f'10.{rng.randint(1, 254)}.{rng.randint(0, 254)}.0/24')


def _topo_simple_lan(rng):
    net = _random_lan(rng)
    gw, mask = str(net.network_address + 1), '255.255.255.0'
    pcs = {'PC1': str(net.network_address + 10), 'PC2': str(net.network_address + 11)}

    adm = admin_segment(rng)
    lab = PktLab(rng=rng)
    lab.add('R1', 'router', '2911', (400, ROUTER_Y), config=[
        'hostname R1', '!', 'interface GigabitEthernet0/0',
        f' ip address {gw} {mask}', ' no shutdown', '!'] + admin_router_lines(adm) + ['end'])
    sw_ip = str(net.network_address + 2)
    lab.add('S1', 'switch', '2960-24TT', (400, SWITCH_Y), config=switch_mgmt_config('S1', sw_ip, mask, gw))
    for (name, ip), x in zip(pcs.items(), (250, 550)):
        lab.add(name, 'pc', 'PC-PT', (x, PC_Y), settings={
            'ip_address': ip, 'subnet_mask': mask, 'default_gateway': gw, 'dhcp': False})

    links = [('R1', 'GigabitEthernet0/0', 'S1', 'GigabitEthernet0/1'),
             ('S1', 'FastEthernet0/1', 'PC1', 'FastEthernet0'),
             ('S1', 'FastEthernet0/2', 'PC2', 'FastEthernet0'),
             add_admin(lab, adm, 700)]
    for l in links:
        lab.add_link(*l)

    info = {'name': 'simple_lan', 'network': str(net), 'gateway': gw, 'mask': mask,
            'admin': adm,
            'devices': {'R1': {'model': '2911', 'type': 'router',
                               'interfaces': {'GigabitEthernet0/0': {'ip': gw, 'mask': mask},
                                              adm['iface']: {'ip': adm['gateway'], 'mask': adm['mask']}}},
                        'PC-ADMIN': {'model': 'PC-PT', 'type': 'pc', 'role': 'admin', 'ip': adm['pc_ip'],
                                     'mask': adm['mask'], 'gateway': adm['gateway']},
                        'S1': {'model': '2960-24TT', 'type': 'switch',
                               'mgmt': {'ip': sw_ip, 'mask': mask, 'gateway': gw}},
                        **{n: {'model': 'PC-PT', 'type': 'pc', 'ip': ip, 'mask': mask, 'gateway': gw}
                           for n, ip in pcs.items()}},
            'links': links}
    return lab, info


def _topo_dhcp_lan(rng):
    net = _random_lan(rng)
    gw, mask = str(net.network_address + 1), '255.255.255.0'
    pool, dns = 'LAN_POOL', '8.8.8.8'

    adm = admin_segment(rng)
    lab = PktLab(rng=rng)
    lab.add('R1', 'router', '2911', (450, ROUTER_Y), config=[
        'hostname R1', '!',
        f'ip dhcp excluded-address {gw} {net.network_address + 9}', '!',
        f'ip dhcp pool {pool}', f' network {net.network_address} {mask}',
        f' default-router {gw}', f' dns-server {dns}', '!',
        'interface GigabitEthernet0/0', f' ip address {gw} {mask}', ' no shutdown', '!']
        + admin_router_lines(adm) + ['end'])
    sw_ip = str(net.network_address + 2)
    lab.add('S1', 'switch', '2960-24TT', (450, SWITCH_Y), config=switch_mgmt_config('S1', sw_ip, mask, gw))
    names = ['PC1', 'PC2', 'PC3']
    for name, x in zip(names, (200, 450, 700)):
        lab.add(name, 'pc', 'PC-PT', (x, PC_Y), settings={'dhcp': True})

    links = [('R1', 'GigabitEthernet0/0', 'S1', 'GigabitEthernet0/1')] + \
            [('S1', f'FastEthernet0/{i}', n, 'FastEthernet0') for i, n in enumerate(names, 1)] + \
            [add_admin(lab, adm, 750)]
    for l in links:
        lab.add_link(*l)

    info = {'name': 'dhcp_lan', 'network': str(net), 'gateway': gw, 'mask': mask,
            'dhcp_pool': pool, 'dns': dns,
            'admin': adm,
            'devices': {'R1': {'model': '2911', 'type': 'router',
                               'interfaces': {'GigabitEthernet0/0': {'ip': gw, 'mask': mask},
                                              adm['iface']: {'ip': adm['gateway'], 'mask': adm['mask']}},
                               'dhcp_pool': {'name': pool, 'network': str(net), 'gateway': gw, 'dns': dns}},
                        'S1': {'model': '2960-24TT', 'type': 'switch',
                               'mgmt': {'ip': sw_ip, 'mask': mask, 'gateway': gw}},
                        'PC-ADMIN': {'model': 'PC-PT', 'type': 'pc', 'role': 'admin', 'ip': adm['pc_ip'],
                                     'mask': adm['mask'], 'gateway': adm['gateway']},
                        **{n: {'model': 'PC-PT', 'type': 'pc', 'dhcp': True} for n in names}},
            'links': links}
    return lab, info


def _topo_multisite_ospf_nat(rng):
    """Gabarit multi-sites : 2 sites (SITE1/SITE2) reliés via un routeur de
    bordure (R-EDGE) qui fait du NAT overload vers un ISP, le tout en OSPF
    (area 0) côté privé. Conventions validées sur de vrais labs NetAcad/CCNA
    (voir docs/RULES_TOPOLOGIES.md) : liens WAN en /30, adresses publiques en
    plages de documentation (192.0.2.0/30, 203.0.113.0/24), NAT overload sur
    l'interface de sortie (pas de pool : la forme la plus simple, cf. §5),
    ISP hors du domaine OSPF (pas de route statique nécessaire côté ISP :
    son seul trafic retour vise l'IP de R-EDGE, directement connectée)."""
    site1_net = _random_lan(rng)
    site2_net = _random_lan(rng)
    wan_base = ipaddress.IPv4Network(f'10.{rng.randint(1, 254)}.250.0/24')
    wan1_net, wan2_net = list(wan_base.subnets(new_prefix=30))[:2]
    isp_wan_net = ipaddress.IPv4Network('192.0.2.0/30')
    internet_net = ipaddress.IPv4Network('203.0.113.0/24')
    mask24 = '255.255.255.0'

    edge_isp_ip, isp_edge_ip = str(isp_wan_net[1]), str(isp_wan_net[2])
    edge_wan1_ip, site1_wan_ip = str(wan1_net[1]), str(wan1_net[2])
    edge_wan2_ip, site2_wan_ip = str(wan2_net[1]), str(wan2_net[2])
    site1_gw, site2_gw = str(site1_net.network_address + 1), str(site2_net.network_address + 1)
    isp_lan_ip, web_ip = str(internet_net[1]), str(internet_net[11])

    def ospf_line(net):
        return f' network {net.network_address} {net.hostmask} area 0'

    # Lignes dédiées à ce gabarit (plus espacées que ROUTER_Y/SWITCH_Y/PC_Y des
    # topologies simples, pour éviter le chevauchement visuel ISP/R-EDGE/WEB
    # signalé lors du premier test réel).
    isp_row, edge_row, site_router_row, site_switch_row, site_pc_row = 100, 260, 420, 580, 740

    lab = PktLab(rng=rng)
    lab.add('R-EDGE', 'router', '2911', (550, edge_row), config=[
        'hostname R-EDGE', '!',
        'interface GigabitEthernet0/0', f' ip address {edge_isp_ip} {isp_wan_net.netmask}',
        ' ip nat outside', ' no shutdown', '!',
        'interface GigabitEthernet0/1', f' ip address {edge_wan1_ip} {wan1_net.netmask}',
        ' ip nat inside', ' no shutdown', '!',
        'interface GigabitEthernet0/2', f' ip address {edge_wan2_ip} {wan2_net.netmask}',
        ' ip nat inside', ' no shutdown', '!',
        'router ospf 1', ospf_line(wan1_net), ospf_line(wan2_net), ' default-information originate', '!',
        f'ip route 0.0.0.0 0.0.0.0 {isp_edge_ip}', '!',
        'access-list 1 permit 10.0.0.0 0.255.255.255',
        'ip nat inside source list 1 interface GigabitEthernet0/0 overload', 'end'])

    lab.add('ISP', 'router', '2911', (400, isp_row), config=[
        'hostname ISP', '!',
        'interface GigabitEthernet0/0', f' ip address {isp_edge_ip} {isp_wan_net.netmask}', ' no shutdown', '!',
        'interface GigabitEthernet0/1', f' ip address {isp_lan_ip} {mask24}', ' no shutdown', '!', 'end'])

    lab.add('WEB', 'pc', 'Server-PT', (700, isp_row), settings={
        'ip_address': web_ip, 'subnet_mask': mask24, 'default_gateway': isp_lan_ip, 'dhcp': False})

    sites = {}
    for i, (tag, site_net, wan_net, edge_ip, site_wan_ip, gw, x) in enumerate((
            ('SITE1', site1_net, wan1_net, edge_wan1_ip, site1_wan_ip, site1_gw, 200),
            ('SITE2', site2_net, wan2_net, edge_wan2_ip, site2_wan_ip, site2_gw, 900))):
        sw = f'SW-{tag}'
        pcs = {f'PC-{tag}-1': str(site_net.network_address + 10), f'PC-{tag}-2': str(site_net.network_address + 11)}
        lab.add(tag, 'router', '2911', (x, site_router_row), config=[
            f'hostname {tag}', '!',
            'interface GigabitEthernet0/0', f' ip address {site_wan_ip} {wan_net.netmask}', ' no shutdown', '!',
            'interface GigabitEthernet0/1', f' ip address {gw} {mask24}', ' no shutdown', '!',
            'router ospf 1', ospf_line(wan_net), ospf_line(site_net), '!', 'end'])
        sw_ip = str(site_net.network_address + 2)
        lab.add(sw, 'switch', '2960-24TT', (x, site_switch_row), config=switch_mgmt_config(sw, sw_ip, mask24, gw))
        for name, ip in pcs.items():
            lab.add(name, 'pc', 'PC-PT', (x + (-70 if name.endswith('-1') else 70), site_pc_row), settings={
                'ip_address': ip, 'subnet_mask': mask24, 'default_gateway': gw, 'dhcp': False})
        sites[tag] = {'net': site_net, 'wan_net': wan_net, 'gw': gw, 'switch': sw, 'pcs': pcs,
                      'wan_iface': 'GigabitEthernet0/0', 'edge_ip': edge_ip}

    links = [
        ('R-EDGE', 'GigabitEthernet0/0', 'ISP', 'GigabitEthernet0/0'),
        ('ISP', 'GigabitEthernet0/1', 'WEB', 'FastEthernet0'),
        ('R-EDGE', 'GigabitEthernet0/1', 'SITE1', 'GigabitEthernet0/0'),
        ('R-EDGE', 'GigabitEthernet0/2', 'SITE2', 'GigabitEthernet0/0'),
    ]
    for tag, s in sites.items():
        links.append((tag, 'GigabitEthernet0/1', s['switch'], 'GigabitEthernet0/1'))
        for i, name in enumerate(s['pcs'], 1):
            links.append((s['switch'], f'FastEthernet0/{i}', name, 'FastEthernet0'))
    for l in links:
        lab.add_link(*l)

    devices = {
        'R-EDGE': {'model': '2911', 'type': 'router',
                   'interfaces': {'GigabitEthernet0/0': {'ip': edge_isp_ip, 'mask': str(isp_wan_net.netmask)},
                                  'GigabitEthernet0/1': {'ip': edge_wan1_ip, 'mask': str(wan1_net.netmask)},
                                  'GigabitEthernet0/2': {'ip': edge_wan2_ip, 'mask': str(wan2_net.netmask)}},
                   'ospf_networks': [(str(wan1_net), 0), (str(wan2_net), 0)],
                   'nat_inside_ifaces': ['GigabitEthernet0/1', 'GigabitEthernet0/2'],
                   'nat_outside_iface': 'GigabitEthernet0/0',
                   'default_route_next_hop': isp_edge_ip},
        'ISP': {'model': '2911', 'type': 'router',
                'interfaces': {'GigabitEthernet0/0': {'ip': isp_edge_ip, 'mask': str(isp_wan_net.netmask)},
                               'GigabitEthernet0/1': {'ip': isp_lan_ip, 'mask': mask24}}},
        'WEB': {'model': 'Server-PT', 'type': 'pc', 'ip': web_ip, 'mask': mask24, 'gateway': isp_lan_ip},
    }
    for tag, s in sites.items():
        devices[tag] = {'model': '2911', 'type': 'router',
                         'interfaces': {'GigabitEthernet0/0': {'ip': str(s['wan_net'][2]), 'mask': str(s['wan_net'].netmask)},
                                        'GigabitEthernet0/1': {'ip': s['gw'], 'mask': mask24}},
                         'ospf_networks': [(str(s['wan_net']), 0), (str(s['net']), 0)],
                         'wan_iface': s['wan_iface']}
        devices[s['switch']] = {'model': '2960-24TT', 'type': 'switch',
                                 'mgmt': {'ip': str(s['net'].network_address + 2), 'mask': mask24, 'gateway': s['gw']}}
        for name, ip in s['pcs'].items():
            devices[name] = {'model': 'PC-PT', 'type': 'pc', 'ip': ip, 'mask': mask24, 'gateway': s['gw']}

    return lab, {'name': 'multisite_ospf_nat', 'devices': devices, 'links': links}


def _topo_switched_redundant(rng):
    """Gabarit purement L2 : 3 switchs en triangle (S1 distribution + S2/S3
    accès), donc un lien redondant/une boucle sur laquelle le Spanning Tree
    doit élire un root bridge et bloquer un port. Confirmé comme vrai cas
    officiel CCNA (ENSA 12.5.13 Troubleshoot Enterprise Networks, voir
    docs/BACKLOG_EXERCICES.md) : priorité STP absente sur le switch censé
    être root. Pas de routeur ici (pas nécessaire : les PC communiquent en
    direct, dans le même VLAN/sous-réseau, à travers les 3 switchs) ; la
    passerelle réservée dans l'adressage n'est donc rattachée à aucun
    appareil réel, comme pour `admin_segment`."""
    net = _random_lan(rng)
    mask = '255.255.255.0'
    gw = str(net.network_address + 1)   # réservée par convention, aucun routeur ne la porte ici
    s1_ip = str(net.network_address + 2)
    pcs = {'PC-S2': str(net.network_address + 10), 'PC-S3': str(net.network_address + 11)}
    stp_vlan, stp_priority = 1, 4096

    lab = PktLab(rng=rng)
    lab.add('S1', 'switch', '2960-24TT', (400, SWITCH_Y - 100), config=[
        'hostname S1', '!', 'interface Vlan1', f' ip address {s1_ip} {mask}', ' no shutdown', '!',
        f'ip default-gateway {gw}', f'spanning-tree vlan {stp_vlan} priority {stp_priority}', '!', 'end'])
    lab.add('S2', 'switch', '2960-24TT', (250, SWITCH_Y + 100), config=['hostname S2', '!', 'end'])
    lab.add('S3', 'switch', '2960-24TT', (550, SWITCH_Y + 100), config=['hostname S3', '!', 'end'])
    for name, x in zip(pcs, (250, 550)):
        lab.add(name, 'pc', 'PC-PT', (x, PC_Y + 100), settings={
            'ip_address': pcs[name], 'subnet_mask': mask, 'default_gateway': gw, 'dhcp': False})

    links = [
        ('S1', 'FastEthernet0/1', 'S2', 'FastEthernet0/1'),
        ('S2', 'FastEthernet0/2', 'S3', 'FastEthernet0/1'),
        ('S3', 'FastEthernet0/2', 'S1', 'FastEthernet0/2'),
        ('S2', 'FastEthernet0/3', 'PC-S2', 'FastEthernet0'),
        ('S3', 'FastEthernet0/3', 'PC-S3', 'FastEthernet0'),
    ]
    for l in links:
        lab.add_link(*l)

    devices = {
        'S1': {'model': '2960-24TT', 'type': 'switch', 'mgmt': {'ip': s1_ip, 'mask': mask, 'gateway': gw},
               'stp_priority': {'vlan': stp_vlan, 'priority': stp_priority}},
        'S2': {'model': '2960-24TT', 'type': 'switch'},
        'S3': {'model': '2960-24TT', 'type': 'switch'},
        **{n: {'model': 'PC-PT', 'type': 'pc', 'ip': ip, 'mask': mask, 'gateway': gw} for n, ip in pcs.items()},
    }
    return lab, {'name': 'switched_redundant', 'network': str(net), 'mask': mask, 'gateway': gw,
                 'devices': devices, 'links': links}


THEMES = {'simple_lan': _topo_simple_lan, 'dhcp_lan': _topo_dhcp_lan,
          'multisite_ospf_nat': _topo_multisite_ospf_nat, 'switched_redundant': _topo_switched_redundant}


# ─── Déploiement d'un plan d'adressage (exercice VLSM → Packet Tracer) ──────

ROUTER_PORTS = ['GigabitEthernet0/0', 'GigabitEthernet0/1', 'GigabitEthernet0/2']  # 2911 : 3 ports Gigabit


SHORT_NAMES = {'Comptabilité': 'COMPTA', 'RH': 'RH', 'Ressources humaines': 'RH', 'Commercial': 'COMM',
               'Direction': 'DIR', 'Logistique': 'LOG', 'Accueil': 'ACCUEIL', 'Informatique': 'INFO',
               'Production': 'PROD', 'Wi-Fi invités': 'WIFI', 'Serveurs': 'SRV'}


def slug(name):
    """'Comptabilité' -> 'COMPTA' : abréviation métier, sinon nom sans accent ni espace."""
    if name in SHORT_NAMES:
        return SHORT_NAMES[name]
    import unicodedata
    ascii_name = unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode()
    return ''.join(ch for ch in ascii_name.upper() if ch.isalnum())[:8]


def build_vlsm_deploy(plan, seed=None, output_dir='.'):
    """
    plan : liste de (service, 'réseau/préfixe'), 3 services maximum.
    Tout est câblé, rien n'est configuré : R1 sans IP (ports éteints, comme
    en sortie d'usine), switchs vierges, PC sans adresse.
    Convention de l'exercice : passerelle = 1re adresse utilisable du sous-réseau.
    """
    if not 1 <= len(plan) <= len(ROUTER_PORTS):
        raise ValueError(f'Le 2911 a {len(ROUTER_PORTS)} ports : 1 à {len(ROUTER_PORTS)} services')
    rng = random.Random(seed)
    lab = PktLab(rng=rng)
    width = 300
    x0 = 450 - width * (len(plan) - 1) // 2
    lab.add('R1', 'router', '2911', (450, ROUTER_Y), config=['hostname R1', '!', 'end'])

    links, services = [], {}
    devices = {'R1': {'model': '2911', 'type': 'router'}}
    for i, (service, cidr) in enumerate(plan):
        net = ipaddress.IPv4Network(cidr)
        tag = slug(service)
        sw, x = f'SW-{tag}', x0 + i * width
        pcs = [f'PC-{tag}-1', f'PC-{tag}-2']
        lab.add(sw, 'switch', '2960-24TT', (x, SWITCH_Y), config=[f'hostname {sw}', '!', 'end'])
        for j, pc in enumerate(pcs):
            # PC réellement vierges : le modèle d'origine porte une IP (192.168.1.1)
            lab.add(pc, 'pc', 'PC-PT', (x - 70 + 140 * j, PC_Y), settings={
                'dhcp': False, 'ip_address': '', 'subnet_mask': '', 'default_gateway': ''})
            links.append((sw, f'FastEthernet0/{j + 1}', pc, 'FastEthernet0'))
            devices[pc] = {'model': 'PC-PT', 'type': 'pc', 'unconfigured': True}
        links.append(('R1', ROUTER_PORTS[i], sw, 'GigabitEthernet0/1'))
        devices[sw] = {'model': '2960-24TT', 'type': 'switch'}
        services[service] = {'network': str(net), 'gateway': str(net.network_address + 1),
                             'mask': str(net.netmask), 'router_iface': ROUTER_PORTS[i],
                             'switch': sw, 'pcs': pcs}
    for l in links:
        lab.add_link(*l)

    xml_path = os.path.join(output_dir, 'lab_vlsm.xml')
    pkt_path = os.path.join(output_dir, 'lab_vlsm.pkt')
    with contextlib.redirect_stdout(io.StringIO()):
        lab.to_packettracer_xml(xml_path)
        _pte.ptfile_encode(xml_path, pkt_path)
    info = {'name': 'vlsm_deploy', 'devices': devices, 'links': links, 'services': services,
            'pkt_path': pkt_path, 'xml_path': xml_path, 'seed': seed}
    return pkt_path, info


def build(theme='simple_lan', seed=None, output_dir='.'):
    """Génère lab_<theme>.pkt dans output_dir. Retourne (chemin_pkt, topology_info)."""
    if theme not in THEMES:
        raise ValueError(f'Thème inconnu : {theme}. Disponibles : {list(THEMES)}')
    rng = random.Random(seed)
    lab, info = THEMES[theme](rng)

    xml_path = os.path.join(output_dir, f'lab_{theme}.xml')
    pkt_path = os.path.join(output_dir, f'lab_{theme}.pkt')
    with contextlib.redirect_stdout(io.StringIO()):
        lab.to_packettracer_xml(xml_path)
        _pte.ptfile_encode(xml_path, pkt_path)
    info.update(pkt_path=pkt_path, xml_path=xml_path, seed=seed)
    return pkt_path, info


if __name__ == '__main__':
    for theme in THEMES:
        pkt, info = build(theme, seed=123, output_dir='/tmp')
        print(theme, pkt, info['network'])
