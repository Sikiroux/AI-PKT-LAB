import unittest
import tempfile
from pathlib import Path
import xml.etree.ElementTree as ET
from workspace_app import Controller
import enterprise_staff
class PopulationTests(unittest.TestCase):
 def test_roster_replays_and_six_departments(self):
  a=enterprise_staff.generate('staff');self.assertEqual(a,enterprise_staff.generate('staff'))
  self.assertEqual(len(a),30);self.assertEqual(len({r['username'] for r in a}),30)
  self.assertEqual({d:sum(r['department']==d for r in a) for d in enterprise_staff.DEPARTMENTS},dict.fromkeys(enterprise_staff.DEPARTMENTS,5))
 def test_generated_ftp_dependencies_cover_ten_people_and_are_independent(self):
  roster=enterprise_staff.generate('staff')
  self.assertEqual(sum('ftp' in p['service_dependencies'] for p in roster),10)
  self.assertEqual({p['department'] for p in roster if 'ftp' in p['service_dependencies']},{'Commercial','Opérations'})
  roster[0]['service_dependencies'].append('custom')
  self.assertNotIn('custom',roster[1]['service_dependencies'])
 def test_new_environment_has_thirty_connected_distinct_clients(self):
  with tempfile.TemporaryDirectory() as tmp:
   c=Controller(None,tmp);c.new('enterprise-thirty')
   s=c.workspace.state;self.assertEqual(len(s['client_workspaces']),30)
   registry=s['company_registry'];self.assertEqual(sum(p['represented'] for p in registry['people'].values()),30)
   self.assertEqual(len({p['user_id'] for p in s['client_workspaces'].values()}),30)
   root=ET.parse(Path(s['network_file']).with_name('reference.xml')).getroot()
   devices=root.findall('NETWORK/DEVICES/DEVICE')
   names=[d.findtext('ENGINE/NAME') for d in devices];self.assertEqual(len(names),len(set(names)))
   ports=[]
   for link in root.findall('NETWORK/LINKS/LINK/CABLE'):
    refs=[link.findtext('FROM'),link.findtext('TO')]
    ports.extend([(refs[0],link.findall('PORT')[0].text),(refs[1],link.findall('PORT')[1].text)])
   self.assertEqual(len(ports),len(set(ports)))
   ips=[p['device']['ip'] for p in s['client_workspaces'].values()]
   self.assertEqual(len(ips),len(set(ips)));self.assertNotIn(s['devices']['printer']['ip'],ips)
   for serial in s['client_workspaces']:
    i=next(i for i,d in enumerate(devices) if d.findtext('ENGINE/SERIALNUMBER')==serial)
    self.assertTrue(any(str(i) in (c.findtext('FROM'),c.findtext('TO')) for c in root.findall('NETWORK/LINKS/LINK/CABLE')))
