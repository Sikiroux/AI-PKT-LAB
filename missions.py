"""
missions.py — Missions : des tâches à réaliser sur un réseau (et non des pannes).

Première mission : déployer dans Packet Tracer un plan d'adressage VLSM
conçu dans l'exercice papier. Si le plan de l'apprenant est valide, c'est
LUI qui est déployé et vérifié ; sinon, c'est le corrigé.

Une mission produit le même type de fichier solution qu'un ticket de panne
(kind='mission', une entrée par tâche avec ses checks), donc checker.py et le
menu 'Valider un ticket' la gèrent sans code supplémentaire.
"""

import json
import os

import builder


def vlsm_deploy(plan, seed=None, output_dir='.'):
    """
    plan : liste de (service, 'réseau/préfixe').
    Construit le lab vierge et écrit la solution. Retourne (chemin_pkt, énoncé).
    """
    pkt_raw, topo = builder.build_vlsm_deploy(plan, seed=seed, output_dir=output_dir)
    pkt = os.path.join(output_dir, 'lab.pkt')
    os.replace(pkt_raw, pkt)
    if os.path.exists(topo['xml_path']):
        os.remove(topo['xml_path'])
    topo['pkt_path'] = pkt

    tasks, all_pcs = [], []
    for service, s in topo['services'].items():
        tasks.append({
            'id': 'vlsm_router', 'device': 'R1',
            'cause': f'{service} : interface {s["router_iface"]} de R1',
            'solution': f'R1 : interface {s["router_iface"]} → ip address {s["gateway"]} {s["mask"]} + no shutdown',
            'checks': [['iface_addr', 'R1', s['router_iface'], s['gateway'], s['mask']],
                       ['iface_up', 'R1', s['router_iface']]]})
        checks = []
        for pc in s['pcs']:
            checks += [['pc_host_in', pc, s['network']], ['pc_mask', pc, s['mask']],
                       ['pc_gateway', pc, s['gateway']]]
        tasks.append({
            'id': 'vlsm_hosts', 'device': s['pcs'][0],
            'cause': f'{service} : postes {", ".join(s["pcs"])}',
            'solution': f'IP libre dans {s["network"]}, masque {s["mask"]}, passerelle {s["gateway"]}',
            'checks': checks})
        all_pcs += s['pcs']
    tasks.append({'id': 'vlsm_unique', 'device': all_pcs[0], 'cause': 'Pas d\'adresse en double',
                  'solution': 'Chaque poste doit avoir sa propre adresse', 'checks': [['unique_ips', '*', all_pcs]]})

    solution = {'kind': 'mission', 'topology': {k: v for k, v in topo.items() if k != 'xml_path'},
                'faults': tasks, 'pkt': pkt}
    with open(os.path.join(output_dir, 'lab_solution.json'), 'w', encoding='utf-8') as f:
        json.dump(solution, f, ensure_ascii=False, indent=2)

    bar = '─' * 64
    first = next(iter(topo['services'].values()))
    ex_net = first['network']
    lines = [bar, ' MISSION : déployer le plan d\'adressage', bar,
             ' Contexte : le matériel est installé et câblé, mais RIEN n\'est configuré.',
             f' Tu dois mettre en service les {len(topo["services"])} services ci-dessous, en adressage',
             ' STATIQUE (saisie manuelle, pas de DHCP dans ce lab).', '',
             ' Plan à déployer :']
    for service, s in topo['services'].items():
        lines.append(f'   {service:14} réseau {s["network"]:18}  R1 {s["router_iface"]:20} → {s["switch"]} '
                     f'→ {", ".join(s["pcs"])}')
    lines += ['',
              ' À faire, pour CHAQUE service :',
              '   1. Sur R1 : sur l\'interface qui dessert le service, mettre la 1re adresse',
              f'      utilisable du réseau (ex. pour {ex_net} → {first["gateway"]}) avec le bon',
              '      masque, puis l\'activer (no shutdown).',
              '   2. Sur les 2 PC du service (Desktop > IP Configuration > Static) :',
              '      une adresse libre du réseau, le masque correspondant au préfixe,',
              '      et l\'adresse de R1 sur ce réseau comme passerelle (Default Gateway).',
              '   Les switchs n\'ont rien à configurer.', '',
              ' Objectif final : chaque PC joint sa passerelle ET les PC des autres services.',
              ' Enfin : copy running-config startup-config sur R1.', '',
              f' Fichier : {pkt}',
              ' Configure dans Packet Tracer, sauvegarde (Ctrl+S), puis valide.', bar]
    return pkt, '\n'.join(lines)
