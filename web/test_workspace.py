import json
import tempfile
import time
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET
from pathlib import Path
from workspace_model import generate, evaluate, Workspace
from workspace_app import Controller
from workspace_network import build


class ModelTests(unittest.TestCase):
    def test_manual_refresh_waits_and_preserves_session_on_unknown_transport(self):
        import threading
        class Broken:
            lock = threading.Lock()
            def snapshot(self): raise RuntimeError('offline')
        with tempfile.TemporaryDirectory() as d:
            c = Controller(Broken(), d)
            c.workspace.state = generate('abc')
            c.workspace.state['remote_session'] = True
            entered = threading.Event()
            done = threading.Event()
            def refresh():
                entered.set()
                c.observe(blocking=True)
                done.set()
            with c.lock:
                worker = threading.Thread(target=refresh)
                worker.start()
                self.assertTrue(entered.wait(1))
                self.assertFalse(done.wait(.05))
            worker.join(2)
            self.assertTrue(done.is_set())
            self.assertTrue(c.workspace.public()['remote_session'])

    def test_unknown_read_blocks_action_without_destroying_transport(self):
        with tempfile.TemporaryDirectory() as folder:
            w=Workspace(Path(folder)/'session.json');w.state=generate('abc')
            w.state['remote_session']=True
            with self.assertRaises(ValueError):w.action('read')
            self.assertTrue(w.state['remote_session'])

    def test_failed_remote_read_refuses_action_but_preserves_transport(self):
        with tempfile.TemporaryDirectory() as folder:
            w=Workspace(Path(folder)/'session.json');w.state=generate('abc')
            w.state['remote_session']=True
            w.state['observation']={'probes':{'remote':dict(at=time.time(),status='failed')}}
            with self.assertRaises(ValueError):w.action('read')
            self.assertTrue(w.state['remote_session'])

    def test_seed_and_separate_draws(self):
        self.assertEqual(generate('abc'), generate('abc'))
        self.assertNotEqual(generate('abc'), generate('other'))
        self.assertIn(generate('abc')['address_family'], ('10', '172', '192'))

    def test_blocked_not_failed_and_stale(self):
        s = generate('abc')
        c = evaluate(s, 'read', at=100)
        self.assertEqual(c['tree']['status'], 'unknown')
        self.assertEqual(c['tree']['children'][0]['status'], 'blocked')
        s['observation'] = dict(at=100, status='passed')
        self.assertFalse(evaluate(s, 'read', at=101)['allowed'])
        self.assertTrue(evaluate(s, 'remote', at=101)['allowed'])
        self.assertEqual(evaluate(s, 'read', at=146)['status'], 'unknown')

    def test_repair_does_not_grant_permissions(self):
        with tempfile.TemporaryDirectory() as d:
            w = Workspace(Path(d) / 'state.json')
            w.state = generate('abc')
            w.state['observation'] = dict(at=time.time(), status='failed')
            with self.assertRaises(ValueError): w.action('connect')
            w.state['observation'] = dict(at=time.time(), status='passed')
            w.action('connect')
            with self.assertRaises(ValueError): w.action('read')
            w.action('grant_read')
            w.action('read')
            with self.assertRaises(ValueError): w.action('write')
            w.action('validate')
            self.assertTrue(w.state['validated'])
            w.action('grant_write')
            w.action('write')
            self.assertIn('Test.txt', w.state['files'])
            restored = Workspace(w.path)
            self.assertTrue(restored.state['read_allowed'])
            self.assertIsNone(restored.state['observation'])

    def test_remote_and_share_have_distinct_paths(self):
        s = generate('abc')
        s['read_allowed'] = True
        s['observation'] = {'probes': {'remote': dict(at=100, status='failed'),
                                      'share': dict(at=100, status='passed')}}
        self.assertFalse(evaluate(s, 'remote', at=101)['allowed'])
        self.assertTrue(evaluate(s, 'read', at=101)['allowed'])

    def test_offline_bridge_becomes_unknown(self):
        class Broken:
            import threading
            lock = threading.Lock()
            def snapshot(self): raise RuntimeError('offline')
        with tempfile.TemporaryDirectory() as d:
            c = Controller(Broken(), d)
            c.workspace.state = generate('abc')
            c.workspace.state['remote_session'] = True
            c.observe()
            self.assertEqual(c.workspace.state['observation']['status'], 'unknown')
            self.assertTrue(c.workspace.state['remote_session'])

    def test_identity_survives_rename_and_rejects_wrong_file(self):
        with tempfile.TemporaryDirectory() as d:
            c = Controller(None, d)
            c.workspace.state = generate('abc')
            c.workspace.state['network_file'] = 'C:/lab/entreprise.pkt'
            c.workspace.state['devices'] = {'client': dict(serial='SERIAL', name='OLD')}
            snapshot = dict(saved_filename='C:/lab/entreprise.pkt', devices=[dict(serial='SERIAL', name='NEW')])
            self.assertEqual(c.identities(snapshot)['client']['name'], 'NEW')
            snapshot['saved_filename'] = 'C:/other.pkt'
            with self.assertRaises(ValueError): c.identities(snapshot)

    def test_common_manifest_matches_both_networks(self):
        with tempfile.TemporaryDirectory() as d, patch('workspace_network.ptexplorer.ptfile_encode'):
            s = build('structural', d)
            reference = ET.parse(Path(d) / 'reference.xml').getroot()
            initial = ET.parse(Path(d) / 'initial.xml').getroot()
            engines = reference.findall('NETWORK/DEVICES/DEVICE/ENGINE')
            serials = [e.findtext('SERIALNUMBER') for e in engines if e.findtext('SERIALNUMBER')]
            self.assertEqual(len(serials), len(set(serials)))
            tech=next(e for e in engines if e.findtext('NAME')==s['devices']['technician']['name'])
            self.assertEqual(tech.find('TYPE').get('model'),'Laptop-PT')
            self.assertIn('-LT-TECH-',tech.findtext('NAME'))
            self.assertEqual(set(s['technician_locations']),{'office','server_room','outside'})
            self.assertEqual(s['technician_session']['location'],'office')
            for role, expected in s['devices'].items():
                engine = next(e for e in engines if e.findtext('NAME') == expected['name'])
                self.assertEqual(engine.findtext('SERIALNUMBER'), expected['serial'])
                self.assertIn(expected['ip'], ET.tostring(engine, encoding='unicode'))
            self.assertEqual(len(reference.findall('NETWORK/LINKS/LINK')),
                             len(initial.findall('NETWORK/LINKS/LINK')) + 1)
            self.assertEqual(len(reference.findall('NETWORK/DEVICES/DEVICE')),
                             len(initial.findall('NETWORK/DEVICES/DEVICE')))


if __name__ == '__main__': unittest.main()
