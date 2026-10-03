"""Plan d'adressage déterministe partagé par le réseau et le ticket."""
import ipaddress
import random


def private_networks(seed, family='10', octet=None):
    if family not in ('10', '172', '192'):
        raise ValueError('Famille IPv4 privée invalide')
    if octet is None:
        octet = random.Random(seed).randint(20, 180)
    prefix = {'10': f'10.{octet}', '172': f'172.{16 + octet % 16}', '192': '192.168'}[family]
    return {key: ipaddress.IPv4Network(f'{prefix}.{octet + i if family == "192" else i}.0/24')
            for i, key in enumerate(('employees', 'servers', 'guests'), 10)}
