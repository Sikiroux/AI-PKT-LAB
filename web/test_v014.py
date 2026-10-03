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
