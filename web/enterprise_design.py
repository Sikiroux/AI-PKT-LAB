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
        positions['R1']=(1950,250)
        positions.update({'SW-EMP':(950,600),'SW-EMP2':(950,1650),'SW-SRV':(2750,600),'SW-GUEST':(2750,1650)})
        members=['PC-ALICE','PC-BOB']+[f'PC-CPT-{i:02d}' for i in range(3,31)]
        for index,name in enumerate(members):
            group=index//5;positions[name]=(400+(index%5)*250,850+group*330)
        for index,name in enumerate(('SRV-INFRA','SRV-WEB','SRV-FTP','SRV-MAIL')):
            positions[name]=(2450+(index%2)*420,950+(index//2)*330)
        positions.update({'PC-ADMIN':(1850,600),'PRN-OFFICE':(1850,1050),'PC-GUEST':(2750,1950)})
        if rng.choice((False,True)):positions={name:(3900-x,y) for name,(x,y) in positions.items()}
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
