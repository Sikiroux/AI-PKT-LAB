"""Postes explicites et lectures non bloquantes pendant les pings."""
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch
from workspace_app import Controller
from workspace_model import Workspace, generate

class WorkstationsTests(unittest.TestCase):
    def state(self):
        s=generate('postes-28')
        s['environment_id']='env-a'
        s['devices']={'client':dict(serial='client-a',name='PC-ALICE',ip='192.168.1.20'),
                      'technician':dict(serial='tech-a',name='LT-TECH',ip='192.168.1.30')}
        return s

    def test_list_distinguishes_simulated_and_observed(self):
        w=Workspace.__new__(Workspace);w.state=self.state()
        w.state['observed_workstations']=[dict(serial='client-a',name='PC-ALICE',ports=[]),
             dict(serial='extra-b',name='PC-BOB',ports=[dict(ip='192.168.1.21')])]
        rows=w.workstations()
        self.assertEqual(len(rows),3)
        self.assertEqual([r['name'] for r in rows if r['remote_supported']],['PC-ALICE'])
        self.assertTrue(rows[0]['ticket_target'])
        self.assertFalse(rows[1]['remote_supported'])
        self.assertFalse(rows[2]['simulated'])
        self.assertEqual(rows[2]['status'],'unknown')

    def test_reject_other_target_without_opening_wrong_desktop(self):
        with tempfile.TemporaryDirectory() as tmp:
            c=Controller(None,tmp);c.workspace.state=self.state()
            for target in ('extra-b','tech-a',''):
                with self.assertRaises(ValueError):c.action('connect',target_serial=target)
            self.assertFalse(c.workspace.state['remote_session'])

    def test_cached_read_does_not_wait_for_controller_lock(self):
        with tempfile.TemporaryDirectory() as tmp:
            c=Controller(None,tmp);c.workspace.state=self.state()
            c.public_snapshot()
            started=threading.Event();done=threading.Event();result=[]
            def read():
                started.set();result.append(c.public_snapshot());done.set()
            with c.lock:
                t=threading.Thread(target=read);t.start()
                self.assertTrue(started.wait(1));self.assertTrue(done.wait(1))
            t.join();self.assertEqual(result[0]['environment_id'],'env-a')
            result[0]['devices']['client']['name']='changed'
            self.assertEqual(c.workspace.state['devices']['client']['name'],'PC-ALICE')

    def test_expired_cached_proof_never_authorizes_remote(self):
        with tempfile.TemporaryDirectory() as tmp:
            c=Controller(None,tmp);c.workspace.state=self.state()
            c.workspace.state['observation']=dict(at=100,status='passed')
            with patch('workspace_model.time.time',return_value=101):
                self.assertTrue(c.public_snapshot()['checks']['remote']['allowed'])
            c._read_state['observation']['at']=time.time()-100
            result=[]
            with c.lock:
                t=threading.Thread(target=lambda:result.append(c.public_snapshot()));t.start();t.join(1)
                self.assertFalse(t.is_alive())
            self.assertFalse(result[0]['checks']['remote']['allowed'])

    def test_cached_read_cannot_cross_environment(self):
        with tempfile.TemporaryDirectory() as tmp:
            c=Controller(None,tmp);c.workspace.state=self.state();c.public_snapshot()
            c.workspace.state['environment_id']='env-b'
            result=[]
            with c.lock:
                t=threading.Thread(target=lambda:result.append(c.public_snapshot()));t.start();t.join(1)
            self.assertEqual(result,[None])

if __name__=='__main__':unittest.main()
