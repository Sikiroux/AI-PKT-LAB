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
  self.assertEqual({x['has_it'] for x in plans},{True,False})
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
  self.assertIn(site+f"-PC-CPT-{plan['target_employee']:02d}",t['description'])
  self.assertEqual(calls[0]['site_code'],site)
  self.assertTrue(calls[0]['business_names'])
  self.assertEqual(calls[0]['employee_count'],plan['employee_count'])
  self.assertEqual(calls[0]['has_it'],plan['has_it'])
  with tempfile.TemporaryDirectory() as folder:
   request=dict(calls[0],folder=folder)
   with patch.object(web_worker.ptexplorer,'ptfile_encode',side_effect=lambda source,target:Path(target).write_bytes(b'pkt')):
    web_worker.generate(request)
   root=ET.parse(Path(folder)/'initial.xml').getroot()
   devices={d.findtext('ENGINE/NAME'):d.find('ENGINE') for d in root.findall('NETWORK/DEVICES/DEVICE')}
   self.assertIn(site+'-PC-CPT-01',devices)
   self.assertIn(site+'-RTR-01',devices)
   self.assertEqual(site+'-PC-IT-01' in devices,plan['has_it'])
   self.assertEqual(sum('-PC-CPT-' in name for name in devices),plan['employee_count'])
   self.assertEqual(len(root.findall('.//PHYSICALWORKSPACE//NODE[TYPE="6"]')),len(devices))
   self.assertEqual(any(n.findtext('NAME')=='Bureau IT' for n in root.findall('.//PHYSICALWORKSPACE//NODE')),plan['has_it'])
   control='02' if plan['target_employee']==1 else '01'
   address=devices[site+'-PC-CPT-'+control].findtext('.//PORT/IP')
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
  self.assertEqual(received[0]['has_it'],t['procedural']['has_it'])
  self.assertEqual(received[0]['target_employee'],t['procedural']['target_employee'])
  self.assertEqual(received[0]['employee_layout'],t['procedural']['employee_layout'])
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

class OptionalIT(unittest.TestCase):
 def test_no_it_host_or_cable_and_fault_still_applies(self):
  with tempfile.TemporaryDirectory() as folder:
   tree,topo=workshops.make_topology('enterprise_services',7,folder,employee_count=6,has_it=False)
   self.assertNotIn('PC-ADMIN',topo['devices'])
   self.assertNotIn('PC-ADMIN',workshops.engines(tree.getroot()))
   self.assertNotIn('PC-ADMIN',str(topo['links']))
   self.assertEqual(topo['has_it'],False)
   workshops.CATALOGUE['dhcp_relay_missing']['mutate'](tree.getroot(),topo)
 def test_reject_invalid_presence(self):
  with tempfile.TemporaryDirectory() as folder:
   for value in (None,0,'false'):
    with self.assertRaises(ValueError):workshops.make_topology('enterprise_services',7,folder,has_it=value)
   with self.assertRaises(ValueError):workshops.make_topology('wifi_deployment',7,folder,has_it=False)

class VariableTargets(unittest.TestCase):
 def test_every_employee_can_be_dhcp_target_without_touching_others(self):
  for index in range(1,7):
   with tempfile.TemporaryDirectory() as folder:
    tree,topo=workshops.make_topology('enterprise_services',7,folder,employee_count=6,has_it=False,target_employee=index,employee_layout='split')
    topo['vary_dhcp_target']=True
    before={n:workshops.port(e).findtext('IP') for n,e in workshops.engines(tree.getroot()).items() if n.startswith('PC')}
    workshops.CATALOGUE['dhcp_relay_missing']['mutate'](tree.getroot(),topo)
    engines=workshops.engines(tree.getroot())
    for name,ip in before.items():
     self.assertEqual(workshops.port(engines[name]).findtext('IP'),'0.0.0.0' if name==topo['dhcp_target'] else ip)
    text=workshops.describe(workshops.CATALOGUE['dhcp_relay_missing']['statement'],topo)
    self.assertIn(topo['dhcp_target'],text)
    workshops.dhcp_client_reference(tree.getroot(),topo['dhcp_target'])
    self.assertEqual(workshops.port(engines[topo['dhcp_target']]).findtext('PORT_DHCP_ENABLE'),'true')
 def test_split_network_has_unique_ports_and_same_subnet(self):
  with tempfile.TemporaryDirectory() as folder:
   tree,topo=workshops.make_topology('enterprise_services',7,folder,employee_count=6,employee_layout='split')
   self.assertIn('SW-EMP2',topo['devices'])
   self.assertIn(ipaddress.ip_address(topo['devices']['SW-EMP2']['mgmt']['ip']),ipaddress.ip_network(topo['networks']['employees']))
   endpoints=[(device,interface) for a,ap,b,bp in topo['links'] for device,interface in ((a,ap),(b,bp))]
   self.assertEqual(len(endpoints),len(set(endpoints)))
   self.assertIn(('SW-EMP','FastEthernet0/24','SW-EMP2','FastEthernet0/24'),topo['links'])
   self.assertTrue(any(a=='SW-EMP2' and b=='PC-BOB' for a,ap,b,bp in topo['links']))
 def test_profiles_vary_targets_and_layout(self):
  plans=[procedural.choose(i,'lease') for i in range(200)]
  self.assertEqual({p['employee_layout'] for p in plans},{'single','split'})
  self.assertEqual({p['target_employee'] for p in plans},set(range(1,7)))
  self.assertTrue(all(p['target_employee']<=p['employee_count'] for p in plans))

class TargetFiles(unittest.TestCase):
 def test_target_in_initial_reference_and_embedded_instructions(self):
  with tempfile.TemporaryDirectory() as folder:
   req=dict(folder=folder,scenario='dhcp_relay_missing',seed=7,level=5,count=1,site_code='TLS42',employee_count=6,has_it=False,target_employee=6,employee_layout='split')
   with patch.object(web_worker.ptexplorer,'ptfile_encode',side_effect=lambda source,target:Path(target).write_bytes(b'pkt')):
    web_worker.generate(req)
   initial=ET.parse(Path(folder)/'initial.xml').getroot()
   reference=ET.parse(Path(folder)/'baseline.xml').getroot()
   def by_name(root):return {d.findtext('ENGINE/NAME'):d.find('ENGINE') for d in root.findall('NETWORK/DEVICES/DEVICE')}
   initial_devices=by_name(initial);ref_devices=by_name(reference)
   self.assertEqual(workshops.port(initial_devices['TLS42-PC-CPT-06']).findtext('PORT_DHCP_ENABLE'),'true')
   self.assertNotEqual(workshops.port(initial_devices['TLS42-PC-CPT-01']).findtext('IP'),'0.0.0.0')
   self.assertNotIn('TLS42-PC-IT-01',initial_devices)
   self.assertIn('TLS42-SW-EMP2',initial_devices)
   self.assertEqual(set(initial_devices),set(ref_devices))
   html=(Path(folder)/'consignes.html').read_text()
   self.assertIn('TLS42-PC-CPT-06 démarre en DHCP sans bail',html)
   self.assertNotIn('TLS42-PC-CPT-01 démarre en DHCP sans bail',html)
   activity=(Path(folder)/'activity.xml').read_text()
   self.assertIn('TLS42-PC-CPT-06',activity)

class LocalInterventions(unittest.TestCase):
 def test_only_selected_pc_changes_and_text_matches(self):
  for fid in ('local_wrong_ip','local_wrong_mask','local_wrong_gateway','local_wrong_dns'):
   with tempfile.TemporaryDirectory() as folder:
    tree,topo=workshops.make_topology('enterprise_services',12,folder,employee_count=6,target_employee=5,has_it=False,employee_layout='split')
    topo['vary_dhcp_target']=True
    before={n:ET.tostring(e) for n,e in workshops.engines(tree.getroot()).items()}
    workshops.CATALOGUE[fid]['mutate'](tree.getroot(),topo)
    after={n:ET.tostring(e) for n,e in workshops.engines(tree.getroot()).items()}
    self.assertEqual([n for n in before if before[n]!=after[n]],['PC-CPT-05'])
    self.assertIn('PC-CPT-05',workshops.describe(workshops.CATALOGUE[fid]['statement'],topo))
 def test_employee_request_starts_without_pc_and_has_complete_reference(self):
  with tempfile.TemporaryDirectory() as folder:
   with patch.object(web_worker.ptexplorer,'ptfile_encode',side_effect=lambda source,target:Path(target).write_bytes(b'pkt')):
    web_worker.generate(dict(folder=folder,scenario='add_employee',seed=12,level=5,count=1,site_code='ALB12',employee_count=6,has_it=False,employee_layout='split'))
   start=ET.parse(Path(folder)/'initial.xml').getroot()
   reference=ET.parse(Path(folder)/'reference.xml').getroot()
   def names(root):return {d.findtext('ENGINE/NAME') for d in root.findall('NETWORK/DEVICES/DEVICE')}
   self.assertNotIn('ALB12-PC-NEW',names(start))
   self.assertEqual(names(reference)-names(start),{'ALB12-PC-NEW'})
   engines=workshops.engines(reference)
   pc=engines['ALB12-PC-NEW']
   self.assertTrue(workshops.port(pc).findtext('IP').endswith('.60'))
   self.assertTrue((Path(folder)/'correction.pkt').exists())
 def test_new_employee_is_generated_as_workshop_and_retry_keeps_mode(self):
  case=PublicPlan();case.setUp()
  try:
   calls=[];original=case.g.start
   def capture(data):calls.append(data);return original(data)
   case.g.start=capture
   case.d.create('new_employee')
   ticket=case.t.state['tickets'][0]
   self.assertEqual(calls[0]['mode'],'atelier')
   self.assertIn(ticket['procedural']['site_code']+'-PC-NEW',ticket['description'])
   case.g.items[0]['status']='failed'
   case.t.action(ticket['id'],'retry_service',{})
   self.assertEqual(calls[1]['mode'],'atelier')
   self.assertEqual(calls[0]['seed'],calls[1]['seed'])
  finally:case.tearDown()
