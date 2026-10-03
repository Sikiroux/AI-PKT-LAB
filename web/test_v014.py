"""Contrôles de fichiers et de gardes ; aucune simulation réseau prétendue."""
import copy,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import xml.etree.ElementTree as ET
sys.path.insert(0,str(Path(__file__).parent/'lab_engine'))
sys.path.append(str(Path(__file__).resolve().parents[1]))
import organization,web_worker,service_api,site_services
from diagnostic import checks
from tickets_app import Tickets
from test_tickets import Fake

class BlockTests(unittest.TestCase):
 def test_names_and_boundaries(self):
  names=organization.mapping(['R1','SW1','PC-ADMIN'],'LY1')
  self.assertEqual(names['PC-ADMIN'],'LY1-PC-IT-01')
  self.assertEqual(organization.replace('R1 R10',names),'LY1-RTR-01 R10')
  for code in ('../A','A','1AA','A B'):
   with self.assertRaises(ValueError):organization.prefix(code)
 def test_wifi_observed_evidence(self):
  device=dict(name='NEW',serial='NEW',ports=[dict(wireless=True,up=True,protocol_up=True,ip='192.168.50.51',ssid='Agence-Lab',peer=dict(device='AP1'))])
  def status():return next(c['status'] for c in checks({'devices':[device]},{'devices':[]},'NEW','wifi','192.168.50.0/24') if c['label']=='SSID et point d acces attendus')
  self.assertEqual(status(),'valide');device['ports'][0]['ssid']='Autre';self.assertEqual(status(),'non satisfait')
 def test_unsupported_probe_never_writes(self):
  class Engine:
   def call(self,code):self.code=code;return '{}'
  engine=Engine();self.assertFalse(service_api.probe(engine,'S','X','http')['supported'])
  self.assertNotIn('p[v.writer](v.expected)',engine.code)
 def test_service_restoration_and_manual_close(self):
  with tempfile.TemporaryDirectory() as tmp:
   t=Tickets(Fake(),Path(tmp)/'state.json');t.register();states={k:True for k in service_api.SERVICES}
   def probe(engine,name,serial,kind):return dict(supported=True,enabled=states[kind],device=name,serial=serial,service=kind,process=service_api.SERVICES[kind]['processes'][0],reader='isEnabled',writer='setEnabled')
   def write(engine,adapter,enabled):states[adapter['service']]=enabled;return dict(enabled=enabled)
   with patch.object(service_api,'probe',side_effect=probe),patch.object(service_api,'write',side_effect=write):
    site_services.create(t,'http','SRV-WEB');ticket=t.state['tickets'][0];self.assertFalse(states['http'])
    with self.assertRaises(ValueError):t.action(ticket['id'],'close',{'manual_tests':True})
    site_services.restore(t,ticket);self.assertTrue(ticket['configuration_complete']);self.assertFalse(ticket['complete'])
    ticket['notes']='Tests HTTP réussis depuis deux clients ; DNS et DHCP préservés.'
    states['dns']=False
    with self.assertRaises(ValueError):t.action(ticket['id'],'close',{'manual_tests':True})
    states['dns']=True;t.action(ticket['id'],'close',{'manual_tests':True});self.assertEqual(ticket['status'],'clos');self.assertFalse(ticket['complete'])
 def test_generated_names_rooms_and_activity(self):
  with tempfile.TemporaryDirectory() as tmp:
   # XML assertions isolate serialization from slow encryption, covered by the core suite.
   def encode(source,target):Path(target).write_bytes(b'encoding-covered-by-core-tests')
   with patch.object(web_worker.ptexplorer,'ptfile_encode',side_effect=encode):
    result=web_worker.generate(dict(folder=tmp,scenario='mixed:3',seed=42,level=5,count=1,site_code='LY1'))
   self.assertIn('implantation.json',result['files'])
   root=ET.parse(Path(tmp)/'initial.xml').getroot();devices=root.findall('NETWORK/DEVICES/DEVICE')
   self.assertTrue(all(d.findtext('ENGINE/NAME').startswith('LY1-') for d in devices))
   nodes=root.findall('.//PHYSICALWORKSPACE//NODE');ids=[n.findtext('UUID_STR') for n in nodes];self.assertEqual(len(ids),len(set(ids)))
   self.assertIn('Baie LY1-01',[n.findtext('NAME') for n in nodes]);self.assertIn('Bureau IT',[n.findtext('NAME') for n in nodes])
   devnodes=[n for n in nodes if n.findtext('TYPE')=='6'];self.assertEqual(len(devnodes),len(devices))
   self.assertTrue(all(n.find('PATH') is not None for n in devnodes))
   for d in devices:self.assertTrue(all(x in ids for x in d.findtext('WORKSPACE/PHYSICAL').split(',')))
   plan=json.loads((Path(tmp)/'implantation.json').read_text());self.assertEqual(len(plan['placements']),len(devices))
   self.assertEqual(next(x['location'] for x in plan['placements'] if x['device']=='LY1-PC-IT-01'),'Bureau IT')
   worksheet=(Path(tmp)/'consignes.html').read_text();self.assertIn('Implantation physique',worksheet)
   activity=ET.parse(Path(tmp)/'activity.xml').getroot();self.assertTrue(any(n.text and 'Implantation physique' in n.text for n in activity.iter()))
   self.assertEqual(len(activity.findall('PACKETTRACER5')),3)
 def test_new_server_has_a_real_completed_topology(self):
  for scenario in ('add_web_server','mixed:6'):
   with self.subTest(scenario=scenario),tempfile.TemporaryDirectory() as tmp:
    def encode(source,target):Path(target).write_bytes(b'encoding-covered-by-core-tests')
    with patch.object(web_worker.ptexplorer,'ptfile_encode',side_effect=encode):
     result=web_worker.generate(dict(folder=tmp,scenario=scenario,seed=7,level=5,count=1,site_code='LY1'))
    initial=ET.parse(Path(tmp)/'initial.xml').getroot()
    complete=ET.parse(Path(tmp)/'reference.xml').getroot()
    def devices(root):return {d.findtext('ENGINE/NAME'):d.find('ENGINE') for d in root.findall('NETWORK/DEVICES/DEVICE')}
    before,after=devices(initial),devices(complete)
    self.assertEqual(set(after)-set(before),{'LY1-SRV-WEB-02'})
    new=after['LY1-SRV-WEB-02'];self.assertTrue(new.findtext('.//PORT/IP').endswith('.50'))
    self.assertEqual(new.findtext('HTTP_SERVER/ENABLED'),'1')
    self.assertIn('Support entreprise',next(f.findtext('FILE_CONTENT/TEXT') for f in new.iter('FILE') if f.findtext('NAME')=='index.html'))
    dns=after['LY1-SRV-INF-01'].find('DNS_SERVER/NAMESERVER-DATABASE')
    record=next(r for r in dns if r.findtext('NAME')=='support.entreprise.test')
    self.assertEqual(record.findtext('IPADDRESS'),new.findtext('.//PORT/IP'))
    self.assertEqual(len(complete.findall('NETWORK/LINKS/LINK')),len(initial.findall('NETWORK/LINKS/LINK'))+1)
    self.assertEqual(len(complete.findall('.//PHYSICALWORKSPACE//NODE[TYPE="6"]')),len(after))
    self.assertEqual(result['correction_label'],'Topologie complétée (exemple)')
    self.assertIn('LY1-SRV-WEB-02',(Path(tmp)/'consignes.html').read_text())
    if scenario=='mixed:6':
     self.assertEqual(before['LY1-SRV-WEB-01'].findtext('HTTP_SERVER/ENABLED'),'0')
     self.assertEqual(after['LY1-SRV-WEB-01'].findtext('HTTP_SERVER/ENABLED'),'1')
 def test_firewall_reference_targets_only_requested_traffic(self):
  for scenario,number in (('guest_firewall','130'),('ban_one_device','131')):
   with self.subTest(scenario=scenario),tempfile.TemporaryDirectory() as tmp:
    with patch.object(web_worker.ptexplorer,'ptfile_encode',side_effect=lambda source,target:Path(target).write_bytes(b'pkt')):
     result=web_worker.generate(dict(folder=tmp,scenario=scenario,seed=9,level=2,count=1,site_code='LY1',address_family='192'))
    def config(filename):
     root=ET.parse(Path(tmp)/filename).getroot()
     router=next(d.find('ENGINE') for d in root.findall('NETWORK/DEVICES/DEVICE') if d.findtext('ENGINE/NAME')=='LY1-RTR-01')
     return [line.text or '' for line in router.findall('RUNNINGCONFIG/LINE')]
    before,after=config('initial.xml'),config('reference.xml')
    self.assertEqual(result['correction_label'],'Topologie complétée (exemple)')
    self.assertFalse(any('ip access-group' in line for line in before))
    self.assertIn(' ip access-group '+number+' in',after)
    self.assertIn('access-list '+number+' permit ip any any',after)
    deny=next(line for line in after if line.startswith('access-list '+number+' deny '))
    if scenario=='guest_firewall':
     self.assertIn('deny ip 192.168.',deny)
     self.assertIn('0.0.0.255',deny)
    else:
     self.assertIn('deny tcp host 192.168.',deny)
     self.assertIn(' eq 80',deny)
    self.assertLess(after.index(deny),after.index('access-list '+number+' permit ip any any'))
    self.assertEqual(after.count(' ip access-group '+number+' in'),1)
