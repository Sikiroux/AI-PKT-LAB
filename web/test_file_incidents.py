import copy
import time
import unittest
import directory_adapter as ad
import directory_incidents
import files_adapter as fa
import file_incidents as fi
from workspace_model import generate, evaluate

class FileIncidentTests(unittest.TestCase):
    def state(self):
        s=generate('incident-files');s['environment_id']='env'
        s['devices']={k:dict(name=k,ip=ip,serial=k) for k,ip in [('client','192.168.1.2'),('server','192.168.1.10'),('technician','192.168.1.20')]}
        ad.ensure(s);fa.ensure(s)
        return s
    def authenticate(self,s):
        now=time.time();s['directory_auth']=dict(user_id=s['directory_user_id'],status='authenticated',environment_id='env',source_device_id='client',expires_at=now+1000)
        s['observation']={'probes':{'share':dict(at=now,status='passed',source_device='client',target='192.168.1.10')}}
    def incidents(self):
        s=self.state()
        for _ in fi.FAMILIES:
            s=fi.prepare(s,time.time());self.authenticate(s)
            yield s
            s['validated']=True
    def repair(self,s):
        fs=s['file_service'];share=fs['shares'][s['documents_share_id']];uid=s['directory_user_id']
        fs['service_status']='running';fs['firewall_tcp445_allowed']=True;share['enabled']=True
        share['quota']=dict(mode='off',limit_bytes=None);fs['volume']['capacity_bytes']=1000000
        fs['files'][s['file_incident']['target_file_id']]['read_only']=False
        for layer in ('share_acl','folder_acl'):
            for action in ('read','write'):
                grant=share[layer][action]
                if uid not in grant['user_ids']:grant['user_ids'].append(uid)
    def test_all_eight_families_occur_once(self):
        self.assertEqual({s['file_incident']['family'] for s in self.incidents()},set(fi.FAMILIES))
    def test_injection_blocks_intended_action(self):
        for s in self.incidents():
            with self.subTest(family=s['file_incident']['family']):
                self.assertFalse(fi.access(s,s['file_incident']['goal'],time.time())['allowed'])
    def test_repair_restores_target(self):
        for s in self.incidents():
            with self.subTest(family=s['file_incident']['family']):
                self.repair(s)
                self.assertTrue(fi.access(s,'read',time.time())['allowed'])
                self.assertTrue(fi.access(s,'write',time.time())['allowed'])
    def test_deterministic_without_mutating_input(self):
        s=self.state();before=copy.deepcopy(s)
        self.assertEqual(fi.prepare(s,100),fi.prepare(s,100));self.assertEqual(s,before)
    def test_unresolved_incident_blocks_both_generators(self):
        s=fi.prepare(self.state(),time.time())
        for prepare in (fi.prepare,directory_incidents.prepare):
            with self.assertRaises(ValueError):prepare(s,time.time())
    def test_public_hides_fault_and_baseline(self):
        i=fi.public_incident(fi.prepare(self.state(),time.time()))
        self.assertNotIn('family',i);self.assertNotIn('baseline',i)
    def test_deleted_target_cannot_pass(self):
        s=next(self.incidents());self.repair(s)
        del s['file_service']['files'][s['file_incident']['target_file_id']]
        self.assertFalse(evaluate(s,'read')['allowed'])
        self.assertEqual(fi.checks(s,time.time())[-1]['status'],'non satisfait')
    def test_missing_network_is_unknown(self):
        s=next(self.incidents());self.repair(s);s['observation']=None
        self.assertEqual(fi.access(s,'read',time.time())['status'],'unknown')
    def test_other_file_change_is_rejected(self):
        s=self.state();fs=s['file_service'];f=copy.deepcopy(next(iter(fs['files'].values())))
        f.update(id='sentinel',name='Autre.txt');fs['files']['sentinel']=f
        s=fi.prepare(s,time.time());self.authenticate(s);self.repair(s)
        fs=s['file_service'];fs['files']['sentinel']['content']='altéré'
        self.assertEqual(fi.checks(s,time.time())[-1]['status'],'non satisfait')

if __name__=='__main__':unittest.main()
