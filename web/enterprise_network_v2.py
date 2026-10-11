"""Segmentation IOS du nouveau socle entreprise, sans changer les liens physiques."""
import ipaddress
import workshops


def apply(root, topo):
    if topo['name'] != 'enterprise_services' or topo.get('employee_count') != 30:
        raise ValueError('Le réseau V2 exige le socle entreprise de trente postes.')
    engines = workshops.engines(root)
    nets = {key: ipaddress.IPv4Network(value) for key, value in topo['networks'].items()}
    last = max(int(net.network_address) for net in nets.values())
    nets['sensitive'] = ipaddress.IPv4Network((last + 256, 24))
    nets['management'] = ipaddress.IPv4Network((last + 512, 24))
    vlans = {'employees': 10, 'sensitive': 15, 'servers': 20, 'guests': 40, 'management': 99}
    infra = topo['devices']['SRV-INFRA']['ip']
    interfaces = {}
    lines = ['hostname R1', '!']
    for physical, keys in [('GigabitEthernet0/0', ('employees', 'sensitive', 'management')),
                           ('GigabitEthernet0/1', ('servers',)),
                           ('GigabitEthernet0/2', ('guests',))]:
        lines += ['interface '+physical, ' no ip address', ' no shutdown', '!']
        for key in keys:
            interface = physical+'.'+str(vlans[key])
            gateway = str(nets[key][1])
            lines += ['interface '+interface, ' encapsulation dot1Q '+str(vlans[key]),
                      ' ip address '+gateway+' 255.255.255.0']
            if key != 'servers':
                lines += [' ip helper-address '+infra]
            lines += ['!']
            interfaces[interface] = dict(ip=gateway, mask='255.255.255.0', vlan=vlans[key])
    lines += ['ntp server '+infra, 'logging '+infra, 'logging trap informational', 'end']
    workshops.configs(engines['R1'], lines)
    topo['devices']['R1']['interfaces'] = interfaces
    memberships = {}
    for name, device in topo['devices'].items():
        if device.get('type') != 'pc':
            continue
        sensitive = name.startswith('PC-CPT-') and 11 <= int(name.rsplit('-', 1)[1]) <= 20
        key = 'management' if name == 'PC-ADMIN' else 'sensitive' if sensitive else 'servers' if name.startswith('SRV-') else 'guests' if name == 'PC-GUEST' else 'employees'
        memberships[name] = vlans[key]
        host = int(device['ip'].rsplit('.', 1)[1])
        device.update(ip=str(nets[key][host]), gateway=str(nets[key][1]), vlan=vlans[key])
        engine = engines[name]
        workshops.put(engine, 'GATEWAY', device['gateway'])
        port = workshops.port(engine)
        workshops.put(port, 'IP', device['ip'])
        workshops.put(port, 'PORT_GATEWAY', device['gateway'])
    for switch, key, host in [('SW-EMP', 'management', 2), ('SW-EMP2', 'management', 3),
                               ('SW-SRV', 'servers', 2), ('SW-GUEST', 'guests', 2)]:
        allowed = [10, 15, 99] if key == 'management' else [vlans[key]]
        config = ['hostname '+switch, '!']
        for vlan in allowed:
            config += ['vlan '+str(vlan), ' name '+next(k.upper() for k, v in vlans.items() if v == vlan), '!']
        trunk_ports = ['GigabitEthernet0/1'] if switch != 'SW-EMP2' else []
        if key == 'management':
            trunk_ports += ['FastEthernet0/24']
        for interface in trunk_ports:
            config += ['interface '+interface, ' switchport mode trunk',
                       ' switchport trunk allowed vlan '+','.join(map(str, allowed)), ' no shutdown', '!']
        access = {}
        for left, left_port, right, right_port in topo['links']:
            peer, interface = (right, left_port) if left == switch else (left, right_port) if right == switch else (None, None)
            if peer in memberships:
                access[interface] = memberships[peer]
        access['FastEthernet0/20'] = vlans[key]
        for interface, vlan in sorted(access.items()):
            config += ['interface '+interface, ' switchport mode access', ' switchport access vlan '+str(vlan),
                       ' spanning-tree portfast', ' no shutdown', '!']
        mgmt = dict(ip=str(nets[key][host]), mask='255.255.255.0', gateway=str(nets[key][1]), vlan=vlans[key])
        topo['devices'][switch]['mgmt'] = mgmt
        config += ['interface Vlan'+str(vlans[key]), ' ip address '+mgmt['ip']+' 255.255.255.0',
                   ' no shutdown', '!', 'ip default-gateway '+mgmt['gateway'], 'end']
        workshops.configs(engines[switch], config)
    workshops.dhcp(engines['SRV-INFRA'], [dict(name=key.upper(), network=str(nets[key]), gateway=str(nets[key][1]), dns=infra)
                                       for key in ('employees', 'sensitive', 'guests', 'management')])
    # Static reference hosts occupy .21-.130. Keep the optional DHCP range disjoint.
    for pool in workshops.dhcp_node(engines['SRV-INFRA']).findall('POOLS/POOL'):
        if pool.findtext('NAME') == 'serverPool':
            continue
        net = ipaddress.IPv4Network(pool.findtext('NETWORK')+'/24')
        workshops.put(pool, 'START_IP', str(net[150]))
        workshops.put(pool, 'END_IP', str(net[199]))
    topo['networks'] = {key: str(net) for key, net in nets.items()}
    return dict(version=2, vlans=vlans, networks=topo['networks'], client_addressing='static',
                dhcp_range='150-199', validation='À tester dans Packet Tracer 9',
                policy='Segmentation de diffusion ; routage autorisé entre VLAN, aucune ACL ajoutée.')
