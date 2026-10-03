import unittest,sys,tempfile,ipaddress
from pathlib import Path
import procedural
sys.path.insert(0,str(Path(__file__).parent/'lab_engine'))
sys.path.append(str(Path(__file__).resolve().parents[1]))
import workshops
import test_service_desk
class Procedural(unittest.TestCase):
 def test_reproducible_and_real_variety(self):
  self.assertEqual(procedural.choose(0,'lease'),procedural.choose(0,'lease'))
  plans=[procedural.choose(n,'lease') for n in range(100)]
  self.assertEqual({x['cause'] for x in plans},{'dhcp_server_off','dhcp_relay_missing','dhcp_relay_wrong'})
  self.assertEqual({x['address_family'] for x in plans},{'10','172','192'})
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
  self.d.create('lease');t=self.t.state['tickets'][0]
  self.assertIn('procedural',t)
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
  self.assertEqual(received[0]['scenario'],t['service_scenario'])
