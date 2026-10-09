"""Présentation des nouvelles entreprises, indépendante des tirages de pannes."""
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
    return dict(version=1, convention=convention, zones=zones, names=names,
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
