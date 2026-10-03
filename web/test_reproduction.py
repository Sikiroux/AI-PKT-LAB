import sys,unittest,xml.etree.ElementTree as ET
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent/'lab_engine'))
import reproduction,workshops
class TestReproduction(unittest.TestCase):
 def test_starts_without_injected_fault(self):
  for ident in reproduction.SCENARIOS:
   mutate=reproduction.install(ident);root=ET.fromstring('<NETWORK><unchanged>yes</unchanged></NETWORK>');before=ET.tostring(root)
   workshops.CATALOGUE[ident]['mutate'](root,{})
   self.assertEqual(ET.tostring(root),before)
   self.assertIs(mutate,workshops.CATALOGUE[reproduction.SCENARIOS[ident]['source']]['mutate'])
 def test_has_preservation_tests_and_restoration(self):
  for spec in reproduction.SCENARIOS.values():
   self.assertGreaterEqual(len(spec['tests']),4)
   self.assertGreaterEqual(len(spec['hints']),2)
   self.assertIn('sain',spec['statement'])
if __name__=='__main__':unittest.main()
