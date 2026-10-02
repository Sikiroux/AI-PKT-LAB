"""Régressions des ateliers manuels. Ne prétend pas simuler le réseau PT."""
import contextlib
import copy
import io
import json
from pathlib import Path
import random
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import workshops as w
import checker
import ptexplorer

class Workshops(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory()
        cls.baselines={}
        for i,name in enumerate(w.TOPOLOGIES):
            cls.baselines[name]=w.make_topology(name,123,Path(cls.tmp.name)/name)

    @classmethod
    def tearDownClass(cls):cls.tmp.cleanup()

    def test_all_specs_mutate_and_render(self):
        for fid,spec in w.CATALOGUE.items():
            with self.subTest(scenario=fid):
                original,topo=self.baselines[spec['topology']]
                root=copy.deepcopy(original.getroot())
                before=ET.tostring(root)
                spec['mutate'](root,topo)
                if spec['kind']=='fault':self.assertNotEqual(before,ET.tostring(root))
                text=w.render(topo,dict(spec,id=fid))
                self.assertIn('Indices progressifs',text)
                self.assertIn('Correction — à consulter à la fin',text)
                self.assertIn('Tests et résultats attendus',text)
                self.assertGreaterEqual(text.count('<details>'),3)
                for raw in [spec['statement'],spec['solution'],*spec['tests']]:
                    self.assertNotIn('{',w.describe(raw,topo))
                # Le socle partagé ne doit jamais être modifié par le test.
                self.assertEqual(before,ET.tostring(original.getroot()))

    def test_server_baseline_and_relay(self):
        tree,t=self.baselines['enterprise_services'];es=w.engines(tree.getroot())
        db=es['SRV-INFRA'].findall('DNS_SERVER/NAMESERVER-DATABASE/RESOURCE-RECORD')
        self.assertEqual({r.findtext('NAME'):r.findtext('IPADDRESS') for r in db},t['records'])
        pools=w.dhcp_node(es['SRV-INFRA']).findall('POOLS/POOL')
        self.assertEqual({p.findtext('NAME') for p in pools},{'serverPool','EMPLOYEES','GUESTS'})
        for pool in pools[1:]:
            self.assertEqual(pool.findtext('MASK'),'255.255.255.0')
            self.assertEqual(pool.findtext('MAX_USERS'),'50')
            self.assertEqual(pool.findtext('DNS_SERVER'),t['devices']['SRV-INFRA']['ip'])
        lines=[x.text for x in es['R1'].findall('RUNNINGCONFIG/LINE')]
        self.assertEqual(sum('ip helper-address' in x for x in lines),2)
        self.assertEqual(es['SRV-WEB'].findtext('HTTP_SERVER/ENABLED'),'1')
        accounts=es['SRV-FTP'].findall('FTP_SERVER/USER_ACCOUNT_MNGR/ACCOUNT')
        self.assertEqual({a.findtext('USERNAME'):a.findtext('PERMISSIONS') for a in accounts},{'lecteur':'RL','depot':'RWNL'})

    def test_dhcp_clients_have_no_old_lease(self):
        tree,t=self.baselines['enterprise_services']
        for fid in [x for x in w.CATALOGUE if x.startswith('dhcp_')]:
            root=copy.deepcopy(tree.getroot());w.CATALOGUE[fid]['mutate'](root,t)
            p=w.port(w.engines(root)['PC-ALICE'])
            self.assertEqual(p.findtext('PORT_DHCP_ENABLE'),'true',fid)
            self.assertEqual(p.findtext('IP'),'0.0.0.0',fid)

    def test_relay_mutation_preserves_other_network(self):
        tree,t=self.baselines['enterprise_services']
        root=copy.deepcopy(tree.getroot());w.CATALOGUE['dhcp_relay_missing']['mutate'](root,t)
        lines=[x.text for x in w.engines(root)['R1'].findall('RUNNINGCONFIG/LINE')]
        self.assertEqual(sum('ip helper-address' in x for x in lines),1)
        index=lines.index('interface GigabitEthernet0/2')
        self.assertIn(' ip helper-address '+t['devices']['SRV-INFRA']['ip'],lines[index:index+6])

    def test_meraki_remote_target_and_uncabled_mx(self):
        tree,t=self.baselines['meraki_branch']
        self.assertEqual(t['devices']['WEB-PUBLIC']['gateway'],'198.51.100.1')
        self.assertEqual(t['devices']['WEB-PUBLIC']['ip'],'198.51.100.10')
        self.assertFalse(any('MX1' in (x[0],x[2]) for x in t['links']))
        self.assertIn('GigabitEthernet0/1',t['devices']['ISP']['interfaces'])
        es=w.engines(tree.getroot())
        self.assertIsNotNone(es['MERAKI-CLOUD'].find('MERAKI_SERVER'))
        self.assertTrue(t['serial'])

    def test_manual_checker_never_awards_success(self):
        path=Path(self.tmp.name)/'manual.json'
        path.write_text(json.dumps({'validation':'manual','pkt':'does-not-exist.pkt'}))
        result,text=checker.check(str(path))
        self.assertIsNone(result['success'])
        self.assertTrue(result['manual'])
        self.assertIn('manuelle',text)

    def test_generation_and_encrypted_snapshots(self):
        import instructions
        for fid in ('dhcp_relay_missing','wifi_add_client','meraki_commission'):
            with self.subTest(scenario=fid):
                folder=Path(self.tmp.name)/fid
                meta=w.generate(fid,seed=5,output_dir=folder)
                out=folder/'decoded.xml'
                with contextlib.redirect_stdout(io.StringIO()):ptexplorer.ptfile_decode(str(folder/'lab.pka'),str(out))
                root=ET.parse(out).getroot()
                self.assertEqual(root.tag,'PACKETTRACER5_ACTIVITY')
                self.assertEqual(len(root.findall('PACKETTRACER5')),3)
                content=root.findtext('ACTIVITY/INSTRUCTIONS/PAGE')
                self.assertIn('Mise en situation',content)
                self.assertNotIn('Afficher une méthode',content)
                self.assertNotIn('Indice 1',content)
                text=(folder/'consignes.html').read_text()
                self.assertIn('Afficher une méthode',text)
                self.assertEqual(meta['validation'],'manual')

    def test_cli_menu_integration(self):
        import main
        from unittest.mock import patch
        folder=Path(self.tmp.name)/'menu_labs';folder.mkdir()
        with patch.object(main,'LABS',str(folder)), patch('builtins.input',side_effect=['1','1','123']), contextlib.redirect_stdout(io.StringIO()):
            main.new_workshop()
        lab=next(folder.iterdir());meta=main.load_meta(str(lab))
        self.assertEqual(meta['validation'],'manual')
        self.assertEqual(meta['scenario'],'dns_service_off')
        with patch.object(main,'LABS',str(folder)), patch('builtins.input',side_effect=['1','2']), contextlib.redirect_stdout(io.StringIO()):
            main.validate()
        self.assertEqual(main.load_meta(str(lab))['status'],'vérifié manuellement')

if __name__=='__main__':unittest.main(verbosity=2)
