import copy
import threading
import unittest
from types import SimpleNamespace
from unittest.mock import Mock
import network_observer
import network_proofs
import test_client_workspaces as fixtures

class CollectionTests(unittest.TestCase):
    def setUp(self):
        self.state={'devices':{r:{'name':r,'ip':ip} for r,ip in [('technician','192.0.2.1'),('client','192.0.2.2'),('server','192.0.2.3'),('printer','192.0.2.4')]},
                    'desktop_services':{'printing':{'printer':{'device_role':'printer'}}}}
        self.found=copy.deepcopy(self.state['devices'])

    def collect(self,found=None,engine=None):
        return network_observer.collect(engine or SimpleNamespace(ping=Mock(return_value={'status':'valide'})),self.state,self.found if found is None else found,lambda:100)

    def test_missing_printer_does_not_hide_directory_or_remote(self):
        self.found.pop('printer');rows=self.collect()
        self.assertEqual(rows['printing']['status'],'unknown')
        self.assertEqual(rows['directory']['status'],'passed')
        self.assertEqual(rows['remote']['status'],'passed')

    def test_missing_client_still_allows_technician_server_measurement(self):
        self.found.pop('client');rows=self.collect()
        self.assertEqual(rows['directory']['status'],'passed')
        for key in ('remote','share','printing'):self.assertEqual(rows[key]['status'],'unknown')

    def test_missing_server_does_not_hide_remote(self):
        self.found.pop('server');rows=self.collect()
        self.assertEqual(rows['remote']['status'],'passed')
        self.assertEqual(rows['directory']['status'],'unknown')
        self.assertEqual(rows['share']['status'],'unknown')

    def test_legacy_ping_exception_isolated_and_no_configuration_calls(self):
        def ping(source,target):
            if source=='client':raise TimeoutError('source unavailable')
            return {'status':'valide'}
        engine=SimpleNamespace(ping=Mock(side_effect=ping));rows=self.collect(engine=engine)
        self.assertEqual(rows['directory']['status'],'passed')
        self.assertEqual(rows['share']['status'],'unknown')
        self.assertEqual(engine.ping.call_count,4)

    def test_batch_one_failure_does_not_validate_or_hide_other_rows(self):
        class Engine:
            def quiet_pings(self,pairs,accelerate=False):
                self.pairs=pairs;self.accelerate=accelerate
                return [{'status':'valide'}, {'status':'non satisfait'}, {'status':'valide'}, None]
        engine=Engine();rows=self.collect(engine=engine)
        self.assertFalse(engine.accelerate)
        self.assertEqual([rows[k]['status'] for k in ('remote','share','directory','printing')],['passed','failed','passed','unknown'])

    def test_bad_batch_count_cannot_create_positive_proof(self):
        class Engine:
            def quiet_pings(self,pairs,accelerate=False):return [{'status':'valide'}]
        self.assertTrue(all(r['status']=='unknown' for r in self.collect(engine=Engine()).values()))

    def test_gateway_in_same_batch_and_explicit_acceleration_forwarded(self):
        self.state.update(technician_locations={'outside':{'gateway':'198.51.100.1'}},technician_session={'location':'outside'})
        class Engine:
            def quiet_pings(self,pairs,accelerate=False):
                self.pairs=pairs;self.accelerate=accelerate
                return [{'status':'valide'} for _ in pairs]
        engine=Engine();rows=network_observer.collect(engine,self.state,self.found,lambda:100,True)
        self.assertTrue(engine.accelerate);self.assertEqual(engine.pairs[-1],('technician','198.51.100.1'))
        self.assertEqual(rows['vpn_gateway']['target'],'198.51.100.1')

class PartialIdentityTests(unittest.TestCase):
    setUp=fixtures.ClientWorkspacesTests.setUp
    proofs=fixtures.ClientWorkspacesTests.proofs

    def test_strict_mutations_remain_strict_and_wrong_file_blocks_observation(self):
        self.s['network_file']='C:/company/entreprise.pkt'
        devices=[dict(d,ports=[]) for k,d in self.s['devices'].items() if k!='client2']
        snapshot={'saved_filename':self.s['network_file'],'devices':devices}
        with self.assertRaises(ValueError):self.c.identities(snapshot)
        self.assertNotIn('client2',self.c.identities(snapshot,partial=True))
        snapshot['saved_filename']='C:/other.pkt'
        with self.assertRaises(ValueError):self.c.identities(snapshot,partial=True)

    def test_controller_observes_directory_even_when_other_station_missing(self):
        self.s['network_file']='C:/company/entreprise.pkt'
        snapshot={'saved_filename':self.s['network_file'],'devices':[dict(d,ports=[]) for k,d in self.s['devices'].items() if k!='client2']}
        engine=SimpleNamespace(lock=threading.RLock(),snapshot=lambda:snapshot,ping=Mock(return_value={'status':'valide'}))
        self.c.engine=engine;self.c._observe_one(blocking=True)
        self.assertEqual(network_proofs.proof(self.s,'directory','technician',self.s['devices']['server']['ip'],__import__('time').time())['status'],'passed')
        snapshot['saved_filename']='C:/other.pkt';engine.ping.reset_mock();self.c._observe_one(blocking=True)
        engine.ping.assert_not_called()
        self.assertEqual(self.s['observation']['status'],'unknown')

if __name__=='__main__':unittest.main()
