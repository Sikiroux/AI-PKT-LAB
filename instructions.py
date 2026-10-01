"""
instructions.py — Contenu (titre, objectifs, mise en situation, table
d'adressage) de la page Instructions d'un lab pkt_lab, bilingue FR/EN.

L'assemblage XML réel (bloc <ACTIVITY>, <COMPARISONS>, <INITIALSETUP>, racine
<PACKETTRACER5_ACTIVITY>...) est délégué à activity.py (module du fork
TeodorPetrovic/tracketpacin, déjà présent dans ce dépôt mais jusque-là jamais
branché) : une tentative d'ajouter <ACTIVITY> "à la main" (version précédente
de ce fichier) faisait planter Packet Tracer au chargement — la vraie
structure d'un .pka avec Instructions est un wrapper complet à 3 instantanés
(initial/working/answer) + des arbres COMPARISONS/INITIALSETUP générés à
partir d'un vrai template PT (templates/activities/subnetting_activity.xml),
pas quelques balises ajoutées à un .pkt existant. Voir docs/RULES_TOPOLOGIES.md §7.
"""

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


def build_title(lang, n=1, is_mission=False):
    t = TEXT[lang]
    return t['title_mission'] if is_mission else t['title_fault'].format(n=n)


def build_html(lang, topo, scenario_paragraphs=(), is_mission=False):
    """Page HTML (titre, objectifs, mise en situation, table d'adressage),
    passée telle quelle à activity.assemble_activity() comme contenu de page
    d'instructions (détectée comme HTML déjà formaté, pas re-convertie)."""
    t = TEXT[lang]
    title = build_title(lang, len(scenario_paragraphs), is_mission=is_mission)
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


if __name__ == '__main__':
    demo_topo = {'devices': {
        'R1': {'type': 'router', 'interfaces': {'GigabitEthernet0/0': {'ip': '10.1.1.1', 'mask': '255.255.255.0'}}},
        'PC1': {'type': 'pc', 'ip': '10.1.1.10', 'mask': '255.255.255.0', 'gateway': '10.1.1.1'},
    }}
    print(build_html('fr', demo_topo, ['Plus de réseau sur PC1 depuis ce matin.']))
