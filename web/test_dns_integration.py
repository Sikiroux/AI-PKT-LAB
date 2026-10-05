import copy
import tempfile
import time
import unittest
from pathlib import Path
import json
from unittest.mock import Mock
import directory_adapter as ad
import files_adapter as fa
import dns_adapter as da
import dns_incidents as di
import directory_incidents
import file_incidents
import sim_dns
from workspace_model import generate, evaluate
from workspace_app import Controller
from workspace_routes import WorkspaceRoutes

class DNSIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.c=Controller(None,self.tmp.name);self.s=generate('dns-integration');self.s['environment_id']='env'
        self.s['devices']={k:dict(name=k,ip=ip,serial=k) for k,ip in [('client','192.168.1.2'),('server','192.168.1.10'),('technician','192.168.1.20')]}
        ad.ensure(self.s);fa.ensure(self.s);da.ensure(self.s);self.auth(self.s);self.c.workspace.state=self.s
    def auth(self,s):
        now=time.time();s['remote_session']=True
        s['directory_auth']=dict(user_id=s['directory_user_id'],status='authenticated',environment_id='env',source_device_id='client',expires_at=now+1000)
        s['observation']={'probes':{key:dict(at=now,status='passed',source_device=source,target=target) for key,source,target in [('remote','technician','192.168.1.2'),('share','client','192.168.1.10'),('directory','technician','192.168.1.10')]}}
    def query(self):return self.c.dns('resolve',dict(query=dict(name=self.s['documents_dns_name'],type='A')))
    def test_ensure_is_idempotent_and_uses_existing_addresses(self):
        before=copy.deepcopy(self.s);self.assertFalse(da.ensure(self.s));self.assertEqual(before,self.s)
        self.assertEqual(self.query()['result']['addresses'],['192.168.1.10'])
    def test_cache_persists_and_can_answer_without_network(self):
        self.query();self.s['observation']['probes']['share']['status']='failed'
        r=self.query()['result'];self.assertTrue(r['cache_hit']);self.assertEqual(r['code'],'OK')
        self.c.dns('flush',{});self.assertEqual(self.query()['result']['code'],'NETWORK_DOWN')
    def test_admin_requires_fresh_technician_proof(self):
        self.s['observation']['probes']['directory']['at']=0
        with self.assertRaises(ValueError):self.c.dns('admin',{})
    def test_route_rejects_missing_or_other_environment(self):
        h=Mock();h.path='/workspace/dns/resolve'
        for data in ({},{'environment_id':'other'}):
            with self.assertRaises(ValueError):WorkspaceRoutes(self.c,'token').post(h,data)
    def test_client_requires_remote_session(self):
        self.s['remote_session']=False
        with self.assertRaises(ValueError):self.query()
    def test_all_incidents_fail_and_repair_with_preservation(self):
        s=self.s;families=set()
        for _ in di.FAMILIES:
            s=di.prepare(s,time.time());self.auth(s);families.add(s['dns_incident']['family'])
            self.assertFalse(evaluate(s,'read')['allowed'],s['dns_incident']['family'])
            dns=s['dns_service'];dns.update(service_status='running',transport_allowed=True)
            dns['clients']['client']['dns_server_ip']=dns['server']['ip']
            for r in dns['records'].values():
                if r['name']==s['documents_dns_name'] and r['type']=='A':r.update(value=dns['server']['ip'],enabled=True)
            dns['cache']['client']={}
            self.assertTrue(all(c['status']=='valide' for c in di.checks(s,time.time())),di.checks(s,time.time()))
            s['validated']=True
        self.assertEqual(families,set(di.FAMILIES))
    def test_unresolved_dns_blocks_other_generators(self):
        s=di.prepare(self.s,time.time())
        for fn in (di.prepare,file_incidents.prepare,directory_incidents.prepare):
            with self.assertRaises(ValueError):fn(s,time.time())
    def test_public_incident_contains_no_family_or_baseline(self):
        p=di.public_incident(di.prepare(self.s,time.time()));self.assertNotIn('family',p);self.assertNotIn('baseline',p)
    def test_negative_response_does_not_authorize_files(self):
        s=self.s
        s['dns_incident']={}
        for r in s['dns_service']['records'].values():r['enabled']=False
        proof,result=da.resolution(s,time.time());self.assertEqual(result['status'],'resolved');self.assertEqual(proof['status'],'failed')
    def test_seed_is_reproducible_without_mutation(self):
        before=copy.deepcopy(self.s)
        self.assertEqual(di.prepare(self.s,123),di.prepare(self.s,123));self.assertEqual(self.s,before)
    def test_resolve_saves_cache_to_session(self):
        self.query()
        stored=json.loads(self.c.workspace.path.read_text())
        self.assertTrue(stored['dns_service']['cache']['client'])
    def test_unrelated_record_change_blocks_validation(self):
        s=di.prepare(self.s,time.time());self.auth(s)
        r=next(iter(s['dns_incident']['baseline']['records']))
        s['dns_service']['records'][r]['ttl']+=1
        self.assertEqual(di.checks(s,time.time())[-1]['status'],'non satisfait')
    def test_migration_backup_is_original_bytes(self):
        old=copy.deepcopy(self.s);old.pop('dns_service');old.pop('documents_dns_name')
        folder=Path(self.tmp.name)/'old';folder.mkdir();p=folder/'session.json';p.write_text(json.dumps(old));raw=p.read_bytes()
        c=Controller(None,folder);self.assertEqual(p.with_suffix('.before-dns.json').read_bytes(),raw);self.assertIn('dns_service',c.workspace.state)

if __name__=='__main__':unittest.main()
