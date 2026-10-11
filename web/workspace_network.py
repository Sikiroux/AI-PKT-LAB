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
import enterprise_design
import enterprise_staff
import enterprise_network_v2
from lab_engine import organization
from workspace_model import generate


def build(seed, folder, initial_fault=True, presentation_version=1, staff_size=30):
    if presentation_version not in (0, 1):
        raise ValueError('Version de présentation inconnue.')
    state = generate(seed)
    if staff_size not in (2,30):raise ValueError('Effectif inconnu.')
    thirty=presentation_version==1 and staff_size==30
    if thirty:
        state['staff']=enterprise_staff.generate(seed)
        state['requester']=state['staff'][0]['display_name']
    folder = Path(folder)
    tree, topo = workshops.make_topology('enterprise_services', state['network_seed'], folder,
                                        state['address_family'], has_it=True, network_printer=True, employee_count=30 if thirty else 2, employee_layout='split' if thirty else 'single')
    root = tree.getroot()
    if thirty:
        state['network_architecture'] = enterprise_network_v2.apply(root, topo)
        ET.indent(tree, space=' ')
        tree.write(folder / 'baseline.xml', encoding='utf-8', short_empty_elements=False)
    if presentation_version == 0:
        names = organization.mapping(topo['devices'], state['site'])
        names['PRN-OFFICE'] = state['site']+'-PRN-USR-01'
    else:
        design = enterprise_design.plan(seed, topo['devices'])
        names = design['names']
        enterprise_design.apply_positions(root, design['positions'])
        state['network_design'] = design
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
    tech_name=state['site']+'-LT-TECH-01' if presentation_version == 0 else names['PC-ADMIN']
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
    for number in range(3,31):
        old=f'PC-CPT-{number:02d}'
        if old in topo['devices']:selected['employee'+str(number)]=old
    for role, old in selected.items():
        engine = next(d.find('ENGINE') for d in root.findall('NETWORK/DEVICES/DEVICE')
                      if d.findtext('ENGINE/NAME') == names[old])
        state['devices'][role] = dict(id=role, name=names[old], ip=topo['devices'][old]['ip'],
                                      serial=engine.findtext('SERIALNUMBER'))
    state['staff_size']=30 if thirty else 2
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
    if not initial_fault:
        state.update(arrival_queue_version=1,read_allowed=True,write_allowed=True,ticket='Demandes procédurales de l’entreprise : choisir un ticket et le prendre en charge.')
        tree.write(folder / 'initial.xml', encoding='utf-8', short_empty_elements=False)
        ptexplorer.ptfile_encode(str(folder / 'initial.xml'), state['network_file'])
        (folder / 'entreprise.json').write_text(__import__('json').dumps(state,ensure_ascii=False,indent=2),encoding='utf-8')
        return state
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
