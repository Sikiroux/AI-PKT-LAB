"""Adaptateur du générateur existant vers le modèle du prototype."""
import copy
import hashlib
import sys
from pathlib import Path
import xml.etree.ElementTree as ET

sys.path.append(str(Path(__file__).resolve().parents[1]))
import workshops
import ptexplorer
from lab_engine import organization
from workspace_model import generate


def build(seed, folder):
    state = generate(seed)
    folder = Path(folder)
    tree, topo = workshops.make_topology('enterprise_services', state['network_seed'], folder,
                                        state['address_family'], has_it=True)
    root = tree.getroot()
    names = organization.mapping(topo['devices'], state['site'])
    organization.rename_tree(root, names)
    # Les modèles clonés partagent parfois le numéro de série d'origine.
    # Attribuer une identité distincte et reproductible à chaque appareil.
    for d in root.findall('NETWORK/DEVICES/DEVICE'):
        e = d.find('ENGINE')
        serial = e.find('SERIALNUMBER')
        if serial is not None:
            serial.text = 'PTT' + hashlib.sha256((state['seed'] + ':' + e.findtext('NAME')).encode()).hexdigest()[:8].upper()
    selected = {'client': 'PC-ALICE', 'technician': 'PC-ADMIN', 'server': 'SRV-FTP'}
    for role, old in selected.items():
        engine = next(d.find('ENGINE') for d in root.findall('NETWORK/DEVICES/DEVICE')
                      if d.findtext('ENGINE/NAME') == names[old])
        state['devices'][role] = dict(id=role, name=names[old], ip=topo['devices'][old]['ip'],
                                      serial=engine.findtext('SERIALNUMBER'))
    state['network_file'] = str((folder / 'entreprise.pkt').resolve())
    state['expected_cable'] = dict(device=names['PC-ALICE'], port='FastEthernet0',
                                    peer=names['SW-EMP'], peer_port='FastEthernet0/1')
    ET.indent(tree, space=' ')
    tree.write(folder / 'reference.xml', encoding='utf-8', short_empty_elements=False)
    ptexplorer.ptfile_encode(str(folder / 'reference.xml'), str(folder / 'reference.pkt'))
    # Retirer uniquement la liaison du poste concerné. L'apprenant la rétablit dans PT.
    initial = copy.deepcopy(tree)
    devices = initial.getroot().findall('NETWORK/DEVICES/DEVICE')
    index = next(i for i, d in enumerate(devices) if d.findtext('ENGINE/NAME') == names['PC-ALICE'])
    links = initial.getroot().find('NETWORK/LINKS')
    removed = []
    for link in list(links):
        cable = link.find('CABLE')
        if cable is not None and str(index) in (cable.findtext('FROM'), cable.findtext('TO')):
            links.remove(link)
            removed.append(link)
    if len(removed) != 1:
        raise ValueError('Impossible d’isoler la liaison du poste client.')
    initial.write(folder / 'initial.xml', encoding='utf-8', short_empty_elements=False)
    ptexplorer.ptfile_encode(str(folder / 'initial.xml'), state['network_file'])
    (folder / 'entreprise.json').write_text(__import__('json').dumps(state, ensure_ascii=False, indent=2), encoding='utf-8')
    return state
