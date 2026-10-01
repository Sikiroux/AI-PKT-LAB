"""
checker.py — Vérifie un lab réparé par l'apprenant.

Deux niveaux de vérification :
  1. CAUSE RACINE : les 'checks' du rapport de panne sont-ils satisfaits ?
  2. DÉGÂTS COLLATÉRAUX : tout ce qui était sain au départ l'est-il resté ?
     (ex. le technicien a "réparé" en changeant l'IP du routeur au lieu du PC)

Plus un avertissement de bonne pratique : config corrigée mais non
sauvegardée (running-config différente de la startup-config).

Particularité PT 9 : à la sauvegarde, PT réécrit les câbles avec des
identifiants save-ref-id, alors que le générateur les écrit avec des numéros
d'ordre. On résout donc les deux formats.
"""

import io
import os
import re
import sys
import json
import tempfile
import ipaddress
import contextlib
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ptexplorer as _pte


# ─── Lecture de l'état du fichier ────────────────────────────────────────────

def _load(pkt_path):
    tmp = tempfile.NamedTemporaryFile(suffix='.xml', delete=False).name
    with contextlib.redirect_stdout(io.StringIO()):
        _pte.ptfile_decode(pkt_path, tmp)
    root = ET.parse(tmp).getroot()
    os.remove(tmp)
    return root


def _wired_port(engine):
    for p in engine.iter('PORT'):
        if 'copper' in (p.findtext('TYPE') or '').lower():
            return p
    return None


def read_state(pkt_path):
    root = _load(pkt_path)
    devices, by_ref, by_index = {}, {}, {}
    for i, d in enumerate(root.find('NETWORK/DEVICES').findall('DEVICE')):
        e = d.find('ENGINE')
        name = e.findtext('NAME')
        port = _wired_port(e)
        devices[name] = {
            'power': (e.findtext('POWER') or 'true') == 'true',
            'ip': port.findtext('IP') if port is not None else None,
            'mask': port.findtext('SUBNET') if port is not None else None,
            'gateway': (e.findtext('GATEWAY') or (port.findtext('PORT_GATEWAY') if port is not None else '') or ''),
            'dhcp': port is not None and port.findtext('PORT_DHCP_ENABLE') == 'true',
            'running': [l.text or '' for l in e.findall('RUNNINGCONFIG/LINE')],
            'startup': [l.text or '' for l in e.findall('STARTUPCONFIG/LINE')],
        }
        by_ref[e.findtext('SAVE_REF_ID')] = name
        by_index[str(i)] = name
    links = []
    for l in root.iter('LINK'):
        c = l.find('CABLE')
        ends = []
        for ref in (c.findtext('FROM'), c.findtext('TO')):
            ends.append(by_ref.get(ref) or by_index.get(ref))
        ports = [p.text for p in c.findall('PORT')]
        links.append((ends[0], ports[0], ends[1], ports[1]))
    return {'devices': devices, 'links': links}


# ─── Lecture de config IOS ───────────────────────────────────────────────────

def _iface_block(lines, iface):
    try:
        start = next(i for i, l in enumerate(lines) if l.strip() == f'interface {iface}')
    except StopIteration:
        return []
    block = []
    for l in lines[start + 1:]:
        if not l.startswith(' '):
            break
        block.append(l.strip())
    return block


def _iface_ip(lines, iface):
    for l in _iface_block(lines, iface):
        m = re.match(r'ip address (\S+) (\S+)', l)
        if m:
            return m.group(1)
    return None


def _iface_addr(lines, iface):
    for l in _iface_block(lines, iface):
        m = re.match(r'ip address (\S+) (\S+)', l)
        if m:
            return m.group(1), m.group(2)
    return None, None


def _iface_up(lines, iface):
    """Sur un routeur, une interface est éteinte par défaut : sans bloc de config
    (jamais configurée), elle est considérée comme éteinte."""
    block = _iface_block(lines, iface)
    return bool(block) and 'shutdown' not in block


def _dhcp_value(lines, key):
    """Première valeur de 'key' dans un bloc ip dhcp pool (default-router, network)."""
    inside = False
    for l in lines:
        if l.startswith('ip dhcp pool'):
            inside = True
            continue
        if inside and not l.startswith(' '):
            inside = False
        if inside and l.strip().startswith(key + ' '):
            return l.strip().split()[1:]
    return None


def _has_link(state, a, b):
    return any({x[0], x[2]} == {a, b} for x in state['links'])


# ─── Évaluation d'un check ───────────────────────────────────────────────────
# Retourne (ok: bool, libellé lisible)

def evaluate(check, state):
    kind, dev = check[0], check[1]
    d = state['devices'].get(dev)
    if d is None and kind != 'unique_ips':
        return False, f'{dev} introuvable dans le fichier'
    if kind == 'pc_gateway':
        return d['gateway'] == check[2], f'Passerelle de {dev} = {check[2]} (actuelle : {d["gateway"] or "vide"})'
    if kind == 'pc_in_network':
        ok = bool(d['ip']) and ipaddress.IPv4Address(d['ip']) in ipaddress.IPv4Network(check[2])
        return ok, f'IP de {dev} dans {check[2]} (actuelle : {d["ip"] or "vide"})'
    if kind == 'pc_ip':
        return d['ip'] == check[2], f'IP de {dev} = {check[2]} (actuelle : {d["ip"] or "vide"})'
    if kind == 'pc_mask':
        return d['mask'] == check[2], f'Masque de {dev} = {check[2]} (actuel : {d["mask"] or "vide"})'
    if kind == 'power':
        return d['power'] == check[2], f'{dev} allumé'
    if kind == 'link':
        return _has_link(state, dev, check[2]), f'Câble {dev} ↔ {check[2]} présent'
    if kind == 'iface_up':
        return _iface_up(d['running'], check[2]), f'{dev} {check[2]} activée (pas de shutdown)'
    if kind == 'iface_ip':
        ip = _iface_ip(d['running'], check[2])
        return ip == check[3], f'{dev} {check[2]} = {check[3]} (actuelle : {ip or "aucune"})'
    if kind == 'iface_addr':
        ip, mask = _iface_addr(d['running'], check[2])
        ok = ip == check[3] and mask == check[4]
        return ok, (f'{dev} {check[2]} = {check[3]} {check[4]} '
                    f'(actuelle : {f"{ip} {mask}" if ip else "aucune"})')
    if kind == 'pc_host_in':
        net = ipaddress.IPv4Network(check[2])
        try:
            ip = ipaddress.IPv4Address(d['ip'])
            ok = ip in net and ip not in (net.network_address, net.broadcast_address)
        except (ValueError, TypeError):
            ok = False
        return ok, f'IP de {dev} = adresse d\'hôte valide de {check[2]} (actuelle : {d["ip"] or "vide"})'
    if kind == 'unique_ips':
        ips = [state['devices'][n]['ip'] for n in check[2] if n in state['devices'] and state['devices'][n]['ip']]
        if len(ips) < len(check[2]):  # pas de point gratuit tant que tout n'est pas adressé
            return False, f'Aucune adresse IP en double (postes adressés : {len(ips)}/{len(check[2])})'
        dup = sorted({ip for ip in ips if ips.count(ip) > 1})
        return not dup, 'Aucune adresse IP en double' + (f' (doublons : {", ".join(dup)})' if dup else '')
    if kind == 'sw_default_gateway':
        gw = next((l.split()[2] for l in d['running'] if l.startswith('ip default-gateway ')), None)
        return gw == check[2], f'{dev} : ip default-gateway {check[2]} (actuelle : {gw or "aucune"})'
    if kind == 'dhcp_default_router':
        v = _dhcp_value(d['running'], 'default-router')
        return bool(v) and v[0] == check[2], f'Pool DHCP de {dev} : passerelle distribuée = {check[2]}'
    if kind == 'dhcp_network':
        v = _dhcp_value(d['running'], 'network')
        ok = bool(v) and len(v) >= 2 and str(ipaddress.IPv4Network(f'{v[0]}/{v[1]}')) == check[2]
        return ok, f'Pool DHCP de {dev} déclaré sur {check[2]}'
    return False, f'Check inconnu : {kind}'


def healthy_checks(topo):
    """Tout ce qui doit être vrai dans un lab sain : sert à détecter les dégâts collatéraux."""
    checks = []
    for name, d in topo['devices'].items():
        checks.append(['power', name, True])
        if d['type'] == 'pc' and not d.get('dhcp') and not d.get('unconfigured'):
            checks += [['pc_ip', name, d['ip']], ['pc_mask', name, d['mask']], ['pc_gateway', name, d['gateway']]]
        for iface, cfg in d.get('interfaces', {}).items():
            checks += [['iface_up', name, iface], ['iface_ip', name, iface, cfg['ip']]]
        if 'mgmt' in d:   # switch administrable : SVI Vlan1 + passerelle par défaut
            m = d['mgmt']
            checks += [['iface_addr', name, 'Vlan1', m['ip'], m['mask']], ['iface_up', name, 'Vlan1'],
                       ['sw_default_gateway', name, m['gateway']]]
        if 'dhcp_pool' in d:
            checks += [['dhcp_default_router', name, d['dhcp_pool']['gateway']],
                       ['dhcp_network', name, d['dhcp_pool']['network']]]
    for link in topo['links']:   # (a, port_a, b, port_b[, type_de_câble])
        checks.append(['link', link[0], link[2]])
    return checks


# ─── Point d'entrée ──────────────────────────────────────────────────────────

def _key(c):
    """Clé de comparaison d'un check : un câble A-B est le même que B-A."""
    if c[0] == 'link':
        return json.dumps(['link'] + sorted(c[1:3]))
    return json.dumps(c)


def check(solution_path, pkt_path=None, reveal=False):
    """Vérifie le lab (une ou plusieurs pannes). Retourne (résultat, compte rendu texte)."""
    with open(solution_path, encoding='utf-8') as f:
        sol = json.load(f)
    topo = sol['topology']
    faults = sol.get('faults') or [sol['fault']]   # compatibilité avec les tickets v1
    mission = sol.get('kind') == 'mission'          # tâches à réaliser plutôt que pannes
    state = read_state(pkt_path or sol['pkt'])

    # 1. Cause racine, panne par panne
    per_fault = []
    root_keys = set()
    for fault in faults:
        results = [(c, *evaluate(c, state)) for c in fault['checks']]
        per_fault.append((fault, results, all(ok for _, ok, _ in results)))
        root_keys |= {_key(c) for c in fault['checks']}
    fixed = sum(1 for *_, ok in per_fault if ok)

    # 2. Dégâts collatéraux : ce qui était sain au départ doit l'être resté
    collateral = [(c, *evaluate(c, state)) for c in healthy_checks(topo)
                  if _key(c) not in root_keys]
    broken = [label for _, ok, label in collateral if not ok]

    # 3. Bonne pratique : panne réparée en live (running) mais encore présente dans la
    # startup-config -> au prochain redémarrage, elle revient.
    # (On ne compare pas running et startup en entier : PT ajoute ses propres
    # lignes par défaut à la running-config, ce qui donnerait des faux positifs.)
    unsaved = []
    for fault in faults:
        for c in fault['checks']:
            if c[0] in ('iface_up', 'iface_ip', 'iface_addr', 'sw_default_gateway',
                        'dhcp_default_router', 'dhcp_network'):
                d = state['devices'].get(c[1])
                if d and d['startup']:
                    startup_state = {'devices': {c[1]: {**d, 'running': d['startup']}}, 'links': []}
                    if evaluate(c, state)[0] and not evaluate(c, startup_state)[0] and c[1] not in unsaved:
                        unsaved.append(c[1])

    success = fixed == len(faults) and not broken
    bar = '─' * 64
    if mission:
        title = '✅ MISSION ACCOMPLIE' if success else '❌ MISSION INCOMPLÈTE'
        out = [bar, f' RÉSULTAT : {title}   ({fixed}/{len(faults)} tâche(s) réalisée(s))', bar]
    else:
        title = '✅ TICKET RÉSOLU' if success else '❌ TICKET NON RÉSOLU'
        out = [bar, f' RÉSULTAT : {title}   ({fixed}/{len(faults)} panne(s) réparée(s))', bar]
    for i, (fault, results, ok) in enumerate(per_fault, 1):
        if mission:
            out.append(f' Tâche {i} — {fault["cause"]} : {"✔ faite" if ok else "✘ à terminer"}')
        else:
            label = f' Panne {i}' if len(faults) > 1 else ' Cause racine'
            out.append(f'{label} : {"réparée" if ok else "non réparée"}')
        out += [f'   {"✔" if r_ok else "✘"} {txt}' for _, r_ok, txt in results]
    if broken:
        out.append(' Dégâts collatéraux (c\'était correct au départ) :')
        out += [f'   ✘ {label}' for label in broken]
    if unsaved:
        out.append(f' ⚠ Config non sauvegardée sur : {", ".join(unsaved)} '
                   f'(pense à "copy running-config startup-config")')
    if (success or reveal) and not mission:
        out.append(bar)
        for i, fault in enumerate(faults, 1):
            prefix = f' [{i}] ' if len(faults) > 1 else ' '
            out += [f'{prefix}La panne : {fault["cause"]}', f'{prefix}Solution : {fault["solution"]}']
    out.append(bar)
    result = {'success': success, 'fixed': fixed, 'total': len(faults),
              'unfixed': [i for i, (*_, ok) in enumerate(per_fault) if not ok],
              'collateral': broken, 'unsaved': unsaved}
    return result, '\n'.join(out)


if __name__ == '__main__':
    # Autotest : panne non réparée -> échec ; lab sain -> succès
    from builder import build
    from faults import inject
    _, topo = build('simple_lan', seed=11, output_dir='/tmp')
    inject(topo, fault_id='router_interface_shutdown', seed=11, output_path='/tmp/chk_panne.pkt')
    print(check('/tmp/chk_panne_solution.json')[1])
    print(check('/tmp/chk_panne_solution.json', pkt_path=topo['pkt_path'])[1])
