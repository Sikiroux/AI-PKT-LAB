import unittest,sys,tempfile,ipaddress,xml.etree.ElementTree as ET
from pathlib import Path
from unittest.mock import patch
import procedural
sys.path.insert(0,str(Path(__file__).parent/'lab_engine'))
sys.path.append(str(Path(__file__).resolve().parents[1]))
import workshops
from addressing import private_networks
import web_worker
import test_service_desk
class Procedural(unittest.TestCase):
 def test_reproducible_and_real_variety(self):
  self.assertEqual(procedural.choose(0,'lease'),procedural.choose(0,'lease'))
  plans=[procedural.choose(n,'lease') for n in range(100)]
  self.assertEqual({x['cause'] for x in plans},{'dhcp_server_off','dhcp_relay_missing','dhcp_relay_wrong'})
  self.assertEqual({x['address_family'] for x in plans},{'10','172','192'})
  self.assertGreater(len({x['site_code'] for x in plans}),30)
  self.assertGreater(len({x['requester'] for x in plans}),3)
  self.assertEqual({x['employee_count'] for x in plans},set(range(2,7)))
 def test_recent_causes_avoided_and_open_family_blocked(self):
  history=[{'service_scenario':'dns_record_delete'}]
  self.assertEqual(procedural.choose(1,'intranet_name',history)['cause'],'dns_record_wrong')
  with self.assertRaises(ValueError):procedural.choose(1,'lease',opened=[{'procedural':{'family':'lease'}}])
 def test_all_rules_have_real_mutations(self):
  for _,_,causes in procedural.FAMILIES:
   for cause in causes:self.assertEqual(workshops.CATALOGUE[cause]['topology'],'enterprise_services')
 def test_private_address_plans_and_dns_mutation(self):
  for family,network in [('10','10.0.0.0/8'),('172','172.16.0.0/12'),('192','192.168.0.0/16')]:
   with tempfile.TemporaryDirectory() as folder:
    tree,topo=workshops.make_topology('enterprise_services',7,folder,family)
    for subnet in topo['networks'].values():self.assertTrue(ipaddress.ip_network(subnet).subnet_of(ipaddress.ip_network(network)))
    roots=workshops.engines(tree.getroot())
    db=roots['SRV-INFRA'].find('DNS_SERVER/NAMESERVER-DATABASE')
    before={r.findtext('NAME'):r.findtext('IPADDRESS') for r in db}
    workshops.CATALOGUE['dns_record_wrong']['mutate'](tree.getroot(),topo)
    after={r.findtext('NAME'):r.findtext('IPADDRESS') for r in db}
    self.assertNotEqual(before['intranet.entreprise.test'],after['intranet.entreprise.test'])
    self.assertEqual(before['ftp.entreprise.test'],after['ftp.entreprise.test'])
class PublicPlan(unittest.TestCase):
 setUp=test_service_desk.TestServiceDesk.setUp
 tearDown=test_service_desk.TestServiceDesk.tearDown
 def test_private_plan_and_seed_kept(self):
  calls=[];original=self.g.start
  def capture(data):calls.append(data);return original(data)
  self.g.start=capture
  self.d.create('lease');t=self.t.state['tickets'][0]
  self.assertIn('procedural',t)
  plan=t['procedural'];site=plan['site_code']
  self.assertIn('Agence '+site,t['description'])
  self.assertIn(plan['requester'],t['description'])
  self.assertIn(str(private_networks(plan['seed'],plan['address_family'])['employees']),t['description'])
  self.assertIn(site+'-PC-CPT-01',t['description'])
  self.assertEqual(calls[0]['site_code'],site)
  self.assertTrue(calls[0]['business_names'])
  self.assertEqual(calls[0]['employee_count'],plan['employee_count'])
  with tempfile.TemporaryDirectory() as folder:
   request=dict(calls[0],folder=folder)
   with patch.object(web_worker.ptexplorer,'ptfile_encode',side_effect=lambda source,target:Path(target).write_bytes(b'pkt')):
    web_worker.generate(request)
   root=ET.parse(Path(folder)/'initial.xml').getroot()
   devices={d.findtext('ENGINE/NAME'):d.find('ENGINE') for d in root.findall('NETWORK/DEVICES/DEVICE')}
   self.assertIn(site+'-PC-CPT-01',devices)
   self.assertIn(site+'-RTR-01',devices)
   self.assertEqual(sum('-PC-CPT-' in name for name in devices),plan['employee_count'])
   self.assertEqual(len(root.findall('.//PHYSICALWORKSPACE//NODE[TYPE="6"]')),len(devices))
   address=devices[site+'-PC-CPT-02'].findtext('.//PORT/IP')
   self.assertIn(ipaddress.ip_address(address),private_networks(plan['seed'],plan['address_family'])['employees'])
   worksheet=(Path(folder)/'consignes.html').read_text(encoding='utf-8')
   self.assertIn(site+'-PC-CPT-01',worksheet)
   self.assertIn(address,worksheet)
  shown=self.t.public()['tickets'][0]
  self.assertNotIn('procedural',shown);self.assertNotIn('service_scenario',shown)

class RetryPlan(unittest.TestCase):
 setUp=test_service_desk.TestServiceDesk.setUp
 tearDown=test_service_desk.TestServiceDesk.tearDown
 def test_retry_preserves_cause_seed_and_addresses(self):
  self.d.create('intranet_name');t=self.t.state['tickets'][0]
  self.g.items[0]['status']='failed';received=[]
  original=self.g.start
  def capture(data):received.append(data);return original(data)
  self.g.start=capture
  self.t.action(t['id'],'retry_service',{})
  self.assertEqual(received[0]['seed'],t['procedural']['seed'])
  self.assertEqual(received[0]['address_family'],t['procedural']['address_family'])
  self.assertEqual(received[0]['site_code'],t['procedural']['site_code'])
  self.assertTrue(received[0]['business_names'])
  self.assertEqual(received[0]['employee_count'],t['procedural']['employee_count'])
  self.assertEqual(received[0]['scenario'],t['service_scenario'])

class VariableSite(unittest.TestCase):
 def test_maximum_site_has_unique_addresses_and_cables(self):
  with tempfile.TemporaryDirectory() as folder:
   tree,topo=workshops.make_topology('enterprise_services',14,folder,'192',employee_count=6)
   clients=[d for n,d in topo['devices'].items() if n in ('PC-ALICE','PC-BOB') or n.startswith('PC-CPT-')]
   self.assertEqual(len(clients),6)
   self.assertEqual(len({d['ip'] for d in clients}),6)
   cables=[link for link in topo['links'] if link[0]=='SW-EMP']
   self.assertEqual(len(cables),7)
   self.assertEqual(len({link[1] for link in cables}),7)
   self.assertEqual(topo['employee_count'],6)
   workshops.CATALOGUE['dhcp_server_off']['mutate'](tree.getroot(),topo)
   engines=workshops.engines(tree.getroot())
   self.assertEqual(workshops.port(engines['PC-ALICE']).findtext('IP'),'0.0.0.0')
   for i in range(3,7):
    name=f'PC-CPT-{i:02d}'
    self.assertEqual(workshops.port(engines[name]).findtext('IP'),topo['devices'][name]['ip'])
 def test_invalid_site_sizes_rejected(self):
  with tempfile.TemporaryDirectory() as folder:
   for count in (1,7,True,2.5,'3'):
    with self.assertRaises(ValueError):workshops.make_topology('enterprise_services',1,folder,employee_count=count)
   with self.assertRaises(ValueError):workshops.make_topology('wifi_deployment',1,folder,employee_count=3)
