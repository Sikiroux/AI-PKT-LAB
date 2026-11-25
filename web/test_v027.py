"""Contrats de parcours et identité des deux exports d'un dépannage."""
import re
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import xml.etree.ElementTree as ET
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import builder
import faults

class NavigationContract(unittest.TestCase):
    def test_literal_controls_exist(self):
        for name in ('tickets', 'workspace'):
            html = (ROOT / 'web' / (name + '.html')).read_text()
            ids = re.findall(r'id="([^"]+)"', html)
            dynamic = re.findall(r"\.id\s*=\s*'([^']+)'", html)
            dynamic += re.findall(r"ticketCenterDialog\('([^']+)'", html)
            self.assertEqual(len(ids), len(set(ids)), name)
            for ref in re.findall(r"\$\('([^']+)'\)", html):
                self.assertIn(ref, ids + dynamic, (name, ref))

    def test_enterprise_network_shortcuts_share_one_target(self):
        html = (ROOT / 'web/tickets.html').read_text()
        self.assertEqual(len(re.findall(r'<button[^>]*class="[^"]*openNetwork', html)), 3)
        self.assertIn("document.querySelectorAll('.openNetwork').forEach(b=>b.onclick=openNetwork)", html)
        self.assertIn("request('/open',{})", html)
        self.assertIn('id="openActiveNetwork"', html)
        self.assertIn("if(!state.site?.environment_id)", html)

    def test_desktop_does_not_manage_environment_or_tickets(self):
        html = (ROOT / 'web/workspace.html').read_text()
        for obsolete in ('environmentChoice', 'nextMixed', 'grant_read', 'Correction du premier exercice', 'data-call="open"'):
            self.assertNotIn(obsolete, html)
        self.assertIn('expandDesktop', html)
        self.assertIn("!target||!connected", html)
        self.assertNotIn("!target||!connected||target.status==='failed'", html)

    def test_tickets_have_only_active_enterprise_source(self):
        html = (ROOT / 'web/tickets.html').read_text()
        self.assertNotIn('<option value="independent">', html)
        self.assertIn("source:'site'", html)
        self.assertIn("state.site?.environment_id?state.tickets:[]", html)

class FaultExportContract(unittest.TestCase):
    def test_pkt_and_pka_have_same_faulty_initial_network(self):
        # Capture the XML entering encryption, while building a real topology and
        # assembling the real activity. Core tests cover the encryption itself.
        captured = {}
        def encode(source, target):
            captured[Path(target).name] = ET.parse(source).getroot()
            Path(target).write_bytes(b'encoded-test-placeholder')
        with tempfile.TemporaryDirectory() as tmp, patch('ptexplorer.ptfile_encode', side_effect=encode):
            _, topo = builder.build('simple_lan', seed=27, output_dir=tmp)
            reports = faults.inject(topo, fault_id='cable_missing', count=1, seed=27,
                                    output_path=str(Path(tmp)/'lab.pka'),
                                    pkt_output_path=str(Path(tmp)/'lab.pkt'))
            self.assertEqual(reports[0]['id'], 'cable_missing')
            pkt = captured['lab.pkt']
            initial = captured['lab.pka'].find('PACKETTRACER5')
            self.assertIsNotNone(initial)
            def normalize(node):
                return (node.tag, sorted(node.attrib.items()), (node.text or '').strip(),
                        tuple(normalize(child) for child in node))
            self.assertEqual(normalize(pkt), normalize(initial))
            self.assertNotEqual(normalize(pkt), normalize(ET.parse(topo['xml_path']).getroot()))

if __name__ == '__main__':
    unittest.main()
