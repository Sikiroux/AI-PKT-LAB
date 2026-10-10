"""Présentation des nouvelles entreprises, indépendante des tirages de pannes."""
import math
import hashlib
import random
from lab_engine import organization


def plan(seed, device_names):
    rng = random.Random(hashlib.sha256((str(seed) + ':presentation:v1').encode()).hexdigest())
    convention = rng.choice(('department', 'inventory'))
    names = {name: organization.KNOWN.get(name, name) for name in device_names}
    if convention == 'inventory':
        for index, old in enumerate(('PC-ALICE', 'PC-BOB', 'PC-GUEST'), 1):
            if old in names:
                names[old] = 'PC-' + str(index).zfill(3)
    if 'PC-ADMIN' in names:
        names['PC-ADMIN'] = 'IT-LT-TECH-01'
    if 'PRN-OFFICE' in names:
        names['PRN-OFFICE'] = 'PRN-USR-01'
    if 'PC-CPT-30' in names and 'PC-GUEST' in names:names['PC-GUEST']='PC-VIS-01'
    departments=('CPT','COM','RH','DIR','ACC','OPS')
    for number in range(3,31):
        old=f'PC-CPT-{number:02d}'
        if old in names:names[old]=f'PC-{departments[(number-1)//5]}-{(number-1)%5+1:02d}'
    if len(set(names.values())) != len(names):
        raise ValueError('Noms de présentation non uniques.')
    zones = ['employees', 'servers', 'guests']
    rng.shuffle(zones)
    spacing = rng.choice((500, 600))
    centers = {zone: 350 + index * spacing for index, zone in enumerate(zones)}
    positions = {'R1': (350 + spacing, 180)}
    for zone, switch in [('employees', 'SW-EMP'), ('servers', 'SW-SRV'), ('guests', 'SW-GUEST')]:
        positions[switch] = (centers[zone], 380)
    for zone, members in [('employees', ('PC-ALICE', 'PC-BOB', 'PC-ADMIN', 'PRN-OFFICE')),
                          ('servers', ('SRV-INFRA', 'SRV-WEB', 'SRV-FTP', 'SRV-MAIL')),
                          ('guests', ('PC-GUEST',))]:
        for index, name in enumerate(members):
            positions[name] = (centers[zone] + round((index - (len(members)-1)/2) * 140), 620)
    if 'PC-CPT-30' in names:
        # [pkt_lab] Each switch owns a radial fan: straight PT links do not
        # cross another switch's clients. Radius includes label clearance;
        # these are conservative logical units, not measured PT icon pixels.
        positions = {'R1': (1120, 130), 'SW-EMP': (480, 640),
                     'SW-EMP2': (1300, 640), 'SW-SRV': (1920, 340),
                     'SW-GUEST': (1920, 920), 'PC-GUEST': (1920, 1120),
                     'PC-ADMIN': (480, 1120), 'PRN-OFFICE': (680, 1120)}
        members = ['PC-ALICE', 'PC-BOB'] + [f'PC-CPT-{i:02d}' for i in range(3, 31)]
        for parity, center in enumerate((480, 1300)):
            clients = members[parity::2]
            for index, name in enumerate(clients):
                angle = -math.pi / 2 + index * 2 * math.pi / len(clients)
                positions[name] = (round(center + 340 * math.cos(angle)),
                                   round(640 + 340 * math.sin(angle)))
        for index, name in enumerate(('SRV-INFRA', 'SRV-WEB', 'SRV-FTP', 'SRV-MAIL')):
            positions[name] = (1740 + index * 120, 590)
    positions = {name: point for name, point in positions.items() if name in names}
    return dict(version=2, convention=convention, zones=zones, names=names,
                positions=positions, canvas_limit=3900)


def apply_positions(root, positions):
    for device in root.findall('NETWORK/DEVICES/DEVICE'):
        name = device.findtext('ENGINE/NAME')
        if name not in positions:
            continue
        logical = device.find('WORKSPACE/LOGICAL')
        if logical is None or logical.find('X') is None or logical.find('Y') is None:
            raise ValueError('Position logique absente : ' + name)
        x, y = positions[name]
        if not (100 <= x <= 3800 and 100 <= y <= 3800):
            raise ValueError('Position hors canevas : ' + name)
        logical.find('X').text = str(x)
        logical.find('Y').text = str(y)
