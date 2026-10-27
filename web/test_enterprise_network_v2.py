import copy
import ipaddress
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from unittest.mock import patch
import workshops
import enterprise_network_v2 as v2
import workspace_network


class EnterpriseNetworkTests(unittest.TestCase):
    def build(self, family='10'):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        tree, topo = workshops.make_topology('enterprise_services', 63, folder.name, family,
                                             employee_count=30, employee_layout='split', network_printer=True)
        return tree.getroot(), topo

    def test_native_vlan_database_matches_each_switch_configuration(self):
        root, topo = self.build()
        v2.apply(root, topo)
        engines = workshops.engines(root)
        for switch, required in [('SW-EMP',{10,15,99}),('SW-EMP2',{10,15,99}),('SW-SRV',{20}),('SW-GUEST',{40})]:
            database = engines[switch].find('VLANS')
            actual = {int(v.get('number')) for v in database.findall('VLAN')}
            self.assertTrue(required <= actual, (switch, actual))
            self.assertIn(1, actual)
            self.assertEqual(len(database.findall('VLAN')), len(actual))
        v2.apply(root, topo)
        for switch in ('SW-EMP','SW-EMP2','SW-SRV','SW-GUEST'):
            ids=[v.get('number') for v in engines[switch].findall('VLANS/VLAN')]
            self.assertEqual(len(ids), len(set(ids)))

    def test_segmentation_preserves_links_and_serials(self):
        root, topo = self.build()
        links = ET.tostring(root.find('NETWORK/LINKS'))
        serials = [d.findtext('ENGINE/SERIALNUMBER') for d in root.findall('NETWORK/DEVICES/DEVICE')]
        result = v2.apply(root, topo)
        self.assertEqual(ET.tostring(root.find('NETWORK/LINKS')), links)
        self.assertEqual([d.findtext('ENGINE/SERIALNUMBER') for d in root.findall('NETWORK/DEVICES/DEVICE')], serials)
        self.assertEqual(set(result['vlans'].values()), {10,15,20,40,99})

    def test_private_nonoverlapping_subnets_and_consistent_hosts(self):
        for family in ('10','172','192'):
            root, topo = self.build(family)
            result = v2.apply(root, topo)
            nets = {key:ipaddress.IPv4Network(net) for key,net in result['networks'].items()}
            self.assertTrue(all(net.is_private for net in nets.values()))
            self.assertEqual(len(set(nets.values())), 5)
            addresses=[]
            for d in topo['devices'].values():
                if d.get('type') != 'pc':continue
                key = next(k for k,v in result['vlans'].items() if v==d['vlan'])
                self.assertIn(ipaddress.IPv4Address(d['ip']), nets[key])
                self.assertEqual(d['gateway'], str(nets[key][1]))
                addresses.append(d['ip'])
            self.assertEqual(len(set(addresses)), len(addresses))

    def test_sensitive_accounts_have_their_vlan_on_both_switches(self):
        root, topo = self.build()
        v2.apply(root,topo)
        for i in range(3,31):
            self.assertEqual(topo['devices'][f'PC-CPT-{i:02d}']['vlan'], 15 if 11<=i<=20 else 10)
        engines=workshops.engines(root)
        for switch in ('SW-EMP','SW-EMP2'):
            config='\n'.join(e.text or '' for e in engines[switch].findall('RUNNINGCONFIG/LINE'))
            self.assertIn('switchport trunk allowed vlan 10,15,99',config)
            self.assertIn('switchport access vlan 15',config)
            self.assertIn('interface Vlan99',config)
            self.assertEqual(ET.tostring(engines[switch].find('RUNNINGCONFIG')).replace(b'RUNNINGCONFIG',b'CONFIG'),
                             ET.tostring(engines[switch].find('STARTUPCONFIG')).replace(b'STARTUPCONFIG',b'CONFIG'))

    def test_each_host_access_port_matches_its_vlan(self):
        root, topo=self.build();v2.apply(root,topo);engines=workshops.engines(root)
        for left,lp,right,rp in topo['links']:
            if topo['devices'][left]['type']!='switch' or topo['devices'][right]['type']!='pc':continue
            lines=[e.text or '' for e in engines[left].findall('RUNNINGCONFIG/LINE')]
            index=lines.index('interface '+lp)
            end=lines.index('!',index)
            self.assertIn(' switchport access vlan '+str(topo['devices'][right]['vlan']),lines[index:end])

    def test_dhcp_does_not_overlap_static_reference_addresses(self):
        root,topo=self.build();v2.apply(root,topo)
        for pool in workshops.dhcp_node(workshops.engines(root)['SRV-INFRA']).findall('POOLS/POOL'):
            if pool.findtext('NAME')=='serverPool':continue
            start=ipaddress.IPv4Address(pool.findtext('START_IP'));end=ipaddress.IPv4Address(pool.findtext('END_IP'))
            for device in topo['devices'].values():
                if device.get('ip'):self.assertFalse(start<=ipaddress.IPv4Address(device['ip'])<=end)
            self.assertEqual(int(end)-int(start)+1,int(pool.findtext('MAX_USERS')))

    def test_manifest_and_technician_destinations_match_xml(self):
        with tempfile.TemporaryDirectory() as folder,patch.object(workspace_network.ptexplorer,'ptfile_encode'):
            state=workspace_network.build('v2-integration',folder,initial_fault=False)
            root=ET.parse(Path(folder)/'reference.xml').getroot();engines=workshops.engines(root)
            self.assertEqual(state['network_architecture']['version'],2)
            for device in state['devices'].values():
                self.assertEqual(workshops.port(engines[device['name']]).findtext('IP'),device['ip'])
            for key,destination in state['technician_locations'].items():
                lines=[e.text or '' for e in engines[destination['device']].findall('RUNNINGCONFIG/LINE')]
                index=lines.index('interface '+destination['port']);end=lines.index('!',index)
                self.assertIn(' switchport access vlan '+str({'office':99,'server_room':20,'outside':40}[key]),lines[index:end])

    def test_small_enterprise_remains_legacy(self):
        with tempfile.TemporaryDirectory() as folder,patch.object(workspace_network.ptexplorer,'ptfile_encode'):
            self.assertNotIn('network_architecture',workspace_network.build('small',folder,initial_fault=False,staff_size=2))
