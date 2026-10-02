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
    sw_port = next(l[1] for l in topo['links'] if l[2] == pc)
    return {'device': pc,
            'cause': f'Câble débranché entre {pc} et S1 ({sw_port})',
            'solution': f'Rebrancher {pc} FastEthernet0 ↔ S1 {sw_port} (câble droit)',
            'checks': [['link', pc, 'S1']]}


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
    'pc_power_off':              {'fn': f_pc_power_off,              'level': 1, 'theme': 'materiel',  'target': 'pc', 'topos': ['simple_lan', 'dhcp_lan'], 'hidden': False},
    'cable_missing':             {'fn': f_cable_missing,             'level': 1, 'theme': 'cablage',   'target': 'pc', 'topos': ['simple_lan', 'dhcp_lan'], 'hidden': False},
    'router_interface_shutdown': {'fn': f_router_interface_shutdown, 'level': 1, 'theme': 'routeur',   'target': 'R1', 'topos': ['simple_lan', 'dhcp_lan'], 'hidden': False},
    'pc_wrong_mask':             {'fn': f_pc_wrong_mask,             'level': 2, 'theme': 'adressage', 'target': 'pc', 'topos': ['simple_lan'], 'hidden': False},
    'router_wrong_ip':           {'fn': f_router_wrong_ip,           'level': 2, 'theme': 'routeur',   'target': 'R1', 'topos': ['simple_lan'], 'hidden': False},
    'dhcp_wrong_default_router': {'fn': f_dhcp_wrong_default_router, 'level': 2, 'theme': 'dhcp',      'target': 'R1', 'topos': ['dhcp_lan'], 'hidden': False},
    'dhcp_wrong_network':        {'fn': f_dhcp_wrong_network,        'level': 2, 'theme': 'dhcp',      'target': 'R1', 'topos': ['dhcp_lan'], 'hidden': False},
    'switch_no_default_gateway': {'fn': f_switch_no_default_gateway, 'level': 2, 'theme': 'switch',    'target': 'S1', 'topos': ['simple_lan', 'dhcp_lan'], 'hidden': True},
    'switch_svi_shutdown':       {'fn': f_switch_svi_shutdown,       'level': 1, 'theme': 'switch',    'target': 'S1', 'topos': ['simple_lan', 'dhcp_lan'], 'hidden': True},
    'ospf_network_missing':      {'fn': f_ospf_network_missing,      'level': 1, 'theme': 'routeur',   'target': 'multisite_router', 'topos': ['multisite_ospf_nat'], 'hidden': False},
    'wan_wrong_ip':              {'fn': f_wan_wrong_ip,              'level': 2, 'theme': 'routeur',   'target': 'multisite_router', 'topos': ['multisite_ospf_nat'], 'hidden': False},
    'nat_inside_missing':        {'fn': f_nat_inside_missing,        'level': 2, 'theme': 'nat',       'target': 'R-EDGE',           'topos': ['multisite_ospf_nat'], 'hidden': False},
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
