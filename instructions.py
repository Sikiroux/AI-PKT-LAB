"""
instructions.py — Construit le bloc <ACTIVITY>/<INSTRUCTIONS> natif de Packet
Tracer (l'onglet "Instructions" visible dans l'appli), bilingue FR/EN.

Structure XML reproduite depuis l'analyse de 2 vrais labs NetAcad (voir
docs/RULES_TOPOLOGIES.md §7) :

    <ACTIVITY ENABLED="no">
     <INSTRUCTIONS>
      <PAGE translate="true">...html...</PAGE>
     </INSTRUCTIONS>
    </ACTIVITY>

ENABLED="no" désactive la notation automatique native de PT (Activity Wizard,
réseau-réponse caché) : la correction reste faite par checker.py, comme pour
le reste du projet. Absent du template vide actuel
(templates/packettracer/emptysavefile.xml) : c'est un bloc à ajouter, pas à
modifier, inséré juste après <OPTIONS> (ordre observé dans les vrais fichiers).
"""

import xml.etree.ElementTree as ET

TEXT = {
    'fr': {
        'title_fault': "Dépannage réseau — {n} panne(s) à corriger",
        'title_mission': "Mission réseau — plan d'adressage à déployer",
        'objectives_header': "Objectifs",
        'objectives_fault': [
            "Diagnostiquer un problème de connectivité réseau à l'aide des outils disponibles "
            "(ping, commandes show...).",
            "Identifier la ou les causes racines sans se fier aux apparences.",
            "Corriger la configuration pour rétablir le fonctionnement normal.",
            "Sauvegarder la configuration corrigée sur l'équipement "
            "(copy running-config startup-config).",
        ],
        'objectives_mission': [
            "Concevoir un plan d'adressage IP valide (VLSM).",
            "Déployer ce plan sur les équipements du réseau.",
            "Vérifier la connectivité entre tous les postes.",
        ],
        'background_header': "Mise en situation",
        'addressing_header': "Table d'adressage (état attendu)",
        'col_device': "Appareil", 'col_interface': "Interface", 'col_type': "Type",
        'col_ip': "Adresse IP", 'col_mask': "Masque", 'col_gateway': "Passerelle",
        'footer': "Dépannez dans Packet Tracer, sauvegardez (Ctrl+S), puis validez depuis pkt_lab.",
    },
    'en': {
        'title_fault': "Network Troubleshooting — {n} issue(s) to fix",
        'title_mission': "Network Mission — addressing plan to deploy",
        'objectives_header': "Objectives",
        'objectives_fault': [
            "Diagnose a network connectivity issue using the available tools (ping, show commands...).",
            "Identify the root cause(s) without trusting appearances.",
            "Fix the configuration to restore normal operation.",
            "Save the corrected configuration on the device (copy running-config startup-config).",
        ],
        'objectives_mission': [
            "Design a valid IP addressing plan (VLSM).",
            "Deploy this plan on the network devices.",
            "Verify connectivity between all hosts.",
        ],
        'background_header': "Background / Scenario",
        'addressing_header': "Addressing Table (expected state)",
        'col_device': "Device", 'col_interface': "Interface", 'col_type': "Device Type",
        'col_ip': "IP Address", 'col_mask': "Subnet Mask", 'col_gateway': "Default Gateway",
        'footer': "Troubleshoot in Packet Tracer, save (Ctrl+S), then validate from pkt_lab.",
    },
}


def _esc(s):
    return (str(s) if s is not None else '').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def _addressing_rows(topo):
    """Lignes (device, interface, type, ip, masque, gateway) à partir de topology_info."""
    rows = []
    for name, d in sorted(topo['devices'].items()):
        if d['type'] == 'pc':
            if d.get('unconfigured'):
                rows.append((name, 'NIC', 'Host', '-', '-', '-'))
            else:
                ip = d.get('ip') or ('DHCP' if d.get('dhcp') else '-')
                rows.append((name, 'NIC', 'Host', ip, d.get('mask', '-'), d.get('gateway', '-')))
        elif d['type'] == 'router':
            for iface, cfg in d.get('interfaces', {}).items():
                rows.append((name, iface, 'Router', cfg['ip'], cfg['mask'], '-'))
        elif d['type'] == 'switch' and 'mgmt' in d:
            m = d['mgmt']
            rows.append((name, 'Vlan1', 'Switch', m['ip'], m['mask'], m['gateway']))
    return rows


def build_html(lang, topo, scenario_paragraphs=(), is_mission=False):
    """Page HTML pour <PAGE> : titre, objectifs, mise en situation, table d'adressage."""
    t = TEXT[lang]
    title = t['title_mission'] if is_mission else t['title_fault'].format(n=len(scenario_paragraphs))
    objectives = t['objectives_mission'] if is_mission else t['objectives_fault']
    rows = _addressing_rows(topo)
    cols = ('col_device', 'col_interface', 'col_type', 'col_ip', 'col_mask', 'col_gateway')

    parts = [
        '<html><head><meta charset="utf-8"></head><body>',
        f'<h1>{_esc(title)}</h1>',
        f'<h2>{_esc(t["objectives_header"])}</h2><ul>',
    ]
    parts += [f'<li>{_esc(o)}</li>' for o in objectives]
    parts.append('</ul>')
    if scenario_paragraphs:
        parts.append(f'<h2>{_esc(t["background_header"])}</h2>')
        parts += [f'<p>{_esc(p)}</p>' for p in scenario_paragraphs]
    parts.append(f'<h2>{_esc(t["addressing_header"])}</h2>')
    parts.append('<table border="1" cellspacing="0" cellpadding="4">')
    parts.append('<tr>' + ''.join(f'<th>{_esc(t[c])}</th>' for c in cols) + '</tr>')
    for row in rows:
        parts.append('<tr>' + ''.join(f'<td>{_esc(v)}</td>' for v in row) + '</tr>')
    parts.append('</table>')
    parts.append(f'<p><i>{_esc(t["footer"])}</i></p>')
    parts.append('</body></html>')
    return ''.join(parts)


def build_activity_element(html):
    activity = ET.Element('ACTIVITY', {'ENABLED': 'no'})
    instr = ET.SubElement(activity, 'INSTRUCTIONS')
    page = ET.SubElement(instr, 'PAGE', {'translate': 'true'})
    page.text = html
    return activity


def insert_into(root, activity_elem):
    """Insère <ACTIVITY> juste après <OPTIONS>, comme observé dans les vrais fichiers PT.
    Remplace un <ACTIVITY> déjà présent plutôt que d'en empiler un second."""
    children = list(root)
    tags = [c.tag for c in children]
    if 'ACTIVITY' in tags:
        root.remove(children[tags.index('ACTIVITY')])
        children = list(root)
        tags = [c.tag for c in children]
    idx = tags.index('OPTIONS') + 1 if 'OPTIONS' in tags else len(children)
    root.insert(idx, activity_elem)


def add_instructions(root, topo, lang='fr', scenario_paragraphs=(), is_mission=False):
    """Construit la page et l'insère dans l'arbre XML. Fonction d'entrée unique
    utilisée par faults.py / missions.py."""
    html = build_html(lang, topo, scenario_paragraphs, is_mission=is_mission)
    insert_into(root, build_activity_element(html))


if __name__ == '__main__':
    demo_topo = {'devices': {
        'R1': {'type': 'router', 'interfaces': {'GigabitEthernet0/0': {'ip': '10.1.1.1', 'mask': '255.255.255.0'}}},
        'PC1': {'type': 'pc', 'ip': '10.1.1.10', 'mask': '255.255.255.0', 'gateway': '10.1.1.1'},
    }}
    print(build_html('fr', demo_topo, ['Plus de réseau sur PC1 depuis ce matin.']))
