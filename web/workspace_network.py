"""Adaptateur du générateur existant vers le modèle du prototype."""
import copy
import hashlib
import sys
from pathlib import Path
import xml.etree.ElementTree as ET

sys.path.append(str(Path(__file__).resolve().parents[1]))
import workshops
import ptexplorer
import technician_model
from lab_engine import organization
from workspace_model import generate


def build(seed, folder):
    state = generate(seed)
    folder = Path(folder)
    tree, topo = workshops.make_topology('enterprise_services', state['network_seed'], folder,
                                        state['address_family'], has_it=True, network_printer=True)
    root = tree.getroot()
    names = organization.mapping(topo['devices'], state['site'])
    names['PRN-OFFICE'] = state['site']+'-PRN-USR-01'
    organization.rename_tree(root, names)
    # Les modèles clonés partagent parfois le numéro de série d'origine.
    # Attribuer une identité distincte et reproductible à chaque appareil.
    for d in root.findall('NETWORK/DEVICES/DEVICE'):
        e = d.find('ENGINE')
        serial = e.find('SERIALNUMBER')
        if serial is not None:
            serial.text = 'PTT' + hashlib.sha256((state['seed'] + ':' + e.findtext('NAME')).encode()).hexdigest()[:8].upper()
    # Portable d'intervention fourni par le prestataire, pas un poste IT résident.
    admin=next(d for d in root.findall('NETWORK/DEVICES/DEVICE') if d.findtext('ENGINE/NAME')==names['PC-ADMIN'])
    old=admin.find('ENGINE');catalogue=ET.parse(Path(__file__).resolve().parents[1]/'templates/packettracer/catalogue_source.xml').getroot()
    portable=copy.deepcopy(next(d.find('ENGINE') for d in catalogue.findall('.//DEVICE') if d.find('ENGINE/TYPE') is not None and d.find('ENGINE/TYPE').get('model')=='Laptop-PT'))
    tech_name=state['site']+'-LT-TECH-01'
    for key in ('SERIALNUMBER','GATEWAY','DNS_SERVER'):
        value=old.findtext(key)
        if value is not None:workshops.put(portable,key,value)
    workshops.put(portable,'NAME',tech_name)
    port=workshops.port(portable)
    for key in ('IP','SUBNET','PORT_GATEWAY','PORT_DNS','PORT_DHCP_ENABLE'):
        value=workshops.port(old).findtext(key)
        if value is not None:workshops.put(port,key,value)
    admin.remove(old);admin.insert(0,portable)
    organization.rename_tree(root,{names['PC-ADMIN']:tech_name})
    names['PC-ADMIN']=tech_name
    selected = {'client': 'PC-ALICE', 'technician': 'PC-ADMIN', 'server': 'SRV-FTP','printer':'PRN-OFFICE','client2':'PC-BOB'}
    for role, old in selected.items():
        engine = next(d.find('ENGINE') for d in root.findall('NETWORK/DEVICES/DEVICE')
                      if d.findtext('ENGINE/NAME') == names[old])
        state['devices'][role] = dict(id=role, name=names[old], ip=topo['devices'][old]['ip'],
                                      serial=engine.findtext('SERIALNUMBER'))
    state['organization_has_it']=bool(int(hashlib.sha256((state['seed']+':resident-it').encode()).hexdigest()[:2],16)%2)
    state['technician_locations']={}
    for key,old,host in [('office','SW-EMP','PC-ADMIN'),('server_room','SW-SRV','SRV-FTP'),('outside','SW-GUEST','PC-GUEST')]:
        ip=topo['devices'][host]['ip'].rsplit('.',1)[0]+'.23'
        engine=next(d.find('ENGINE') for d in root.findall('NETWORK/DEVICES/DEVICE') if d.findtext('ENGINE/NAME')==names[old])
        state['technician_locations'][key]=dict(label=technician_model.LOCATIONS[key],device=names[old],serial=engine.findtext('SERIALNUMBER'),port='FastEthernet0/20',ip=ip,mask='255.255.255.0',gateway=ip.rsplit('.',1)[0]+'.1')
    # Le portable démarre sur son raccordement existant ; les ports 20 sont réservés aux déplacements.
    technician_model.ensure(state)
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
