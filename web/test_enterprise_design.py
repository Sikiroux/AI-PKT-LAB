import unittest
import xml.etree.ElementTree as ET
import tempfile
from pathlib import Path
from unittest.mock import patch
import enterprise_design as design

NAMES = ('R1', 'SW-EMP', 'SW-SRV', 'SW-GUEST', 'PC-ALICE', 'PC-BOB',
         'PC-ADMIN', 'PC-GUEST', 'PRN-OFFICE', 'SRV-INFRA', 'SRV-WEB', 'SRV-FTP', 'SRV-MAIL')


class DesignTests(unittest.TestCase):
    def test_legacy_generation_preserves_site_names(self):
        import workspace_network
        with tempfile.TemporaryDirectory() as folder, patch.object(workspace_network.ptexplorer, 'ptfile_encode'):
            state = workspace_network.build('old-session', folder, initial_fault=False, presentation_version=0)
            self.assertNotIn('network_design', state)
            self.assertEqual(state['devices']['client']['name'], state['site']+'-PC-CPT-01')
            self.assertEqual(state['devices']['technician']['name'], state['site']+'-LT-TECH-01')
            root = ET.parse(Path(folder)/'reference.xml').getroot()
            router = next(d for d in root.findall('NETWORK/DEVICES/DEVICE') if d.findtext('ENGINE/NAME') == state['site']+'-RTR-01')
            self.assertEqual(float(router.findtext('WORKSPACE/LOGICAL/X')), 600)
            self.assertEqual(float(router.findtext('WORKSPACE/LOGICAL/Y')), 120)

    def test_reproducible_and_varied(self):
        self.assertEqual(design.plan('same', NAMES), design.plan('same', reversed(NAMES)))
        plans = [design.plan(str(i), NAMES) for i in range(30)]
        self.assertEqual({p['convention'] for p in plans}, {'department', 'inventory'})
        self.assertGreater(len({tuple(p['zones']) for p in plans}), 1)

    def test_large_layout_compact_and_labels_separated(self):
        names = NAMES + ('SW-EMP2',) + tuple(f'PC-CPT-{i:02d}' for i in range(3, 31))
        for seed in range(30):
            points = design.plan(seed, names)['positions']
            self.assertEqual(set(points), set(names))
            self.assertLessEqual(max(x for x, y in points.values()) - min(x for x, y in points.values()), 2000)
            self.assertLessEqual(max(y for x, y in points.values()) - min(y for x, y in points.values()), 1000)
            items = list(points.items())
            for index, (name, (x, y)) in enumerate(items):
                for other, (ox, oy) in items[index+1:]:
                    self.assertTrue(abs(x-ox) >= 110 or abs(y-oy) >= 80, (name, other))

    def test_large_clients_stay_with_their_actual_access_switch(self):
        names = NAMES + ('SW-EMP2',) + tuple(f'PC-CPT-{i:02d}' for i in range(3, 31))
        points = design.plan('ownership', names)['positions']
        for number in range(1, 31):
            name = 'PC-ALICE' if number == 1 else 'PC-BOB' if number == 2 else f'PC-CPT-{number:02d}'
            own = points['SW-EMP' if number % 2 else 'SW-EMP2']
            other = points['SW-EMP2' if number % 2 else 'SW-EMP']
            distance = lambda center: sum((a-b)**2 for a, b in zip(points[name], center))
            self.assertLess(distance(own), distance(other))

    def test_no_person_or_site_in_names(self):
        for i in range(30):
            p = design.plan(str(i), NAMES)
            self.assertEqual(len(set(p['names'].values())), len(NAMES))
            self.assertFalse(any('ALICE' in name or 'BOB' in name or 'ALB' in name for name in p['names'].values()))
            coords = list(p['positions'].values())
            self.assertEqual(len(set(coords)), len(coords))
            self.assertTrue(all(100 <= x <= 3800 and 100 <= y <= 3800 for x, y in coords))

    def test_only_logical_positions_change(self):
        root = ET.fromstring('<ROOT><NETWORK><DEVICES><DEVICE><ENGINE><NAME>R1</NAME><IP>10.0.0.1</IP></ENGINE><WORKSPACE><LOGICAL><X>0</X><Y>0</Y></LOGICAL><PHYSICAL>keep</PHYSICAL></WORKSPACE></DEVICE></DEVICES></NETWORK></ROOT>')
        design.apply_positions(root, {'R1': (900, 180)})
        self.assertEqual(root.findtext('.//LOGICAL/X'), '900')
        self.assertEqual(root.findtext('.//ENGINE/IP'), '10.0.0.1')
        self.assertEqual(root.findtext('.//PHYSICAL'), 'keep')

    def test_reject_out_of_canvas(self):
        root = ET.fromstring('<ROOT><NETWORK><DEVICES><DEVICE><ENGINE><NAME>R1</NAME></ENGINE><WORKSPACE><LOGICAL><X>0</X><Y>0</Y></LOGICAL></WORKSPACE></DEVICE></DEVICES></NETWORK></ROOT>')
        with self.assertRaises(ValueError):
            design.apply_positions(root, {'R1': (4000, 100)})

    def test_network_manifest_matches_initial_and_reference(self):
        import workspace_network
        with tempfile.TemporaryDirectory() as folder, patch.object(workspace_network.ptexplorer, 'ptfile_encode'):
            state = workspace_network.build('presentation-integration', folder, initial_fault=False)
            roots = [ET.parse(Path(folder)/name).getroot() for name in ('initial.xml', 'reference.xml')]
            for root in roots:
                devices = {d.findtext('ENGINE/NAME'): d for d in root.findall('NETWORK/DEVICES/DEVICE')}
                for role in state['devices'].values():
                    self.assertIn(role['name'], devices)
                    self.assertEqual(devices[role['name']].findtext('ENGINE/SERIALNUMBER'), role['serial'])
                for old, point in state['network_design']['positions'].items():
                    d = devices[state['network_design']['names'][old]]
                    self.assertEqual((int(d.findtext('WORKSPACE/LOGICAL/X')), int(d.findtext('WORKSPACE/LOGICAL/Y'))), point)
            self.assertEqual(len(roots[0].findall('NETWORK/LINKS/LINK')), len(roots[1].findall('NETWORK/LINKS/LINK')))
