import tempfile
import time
import unittest
from pathlib import Path
from workspace_model import Workspace, generate, evaluate

class DiagnosticPrerequisites(unittest.TestCase):
    def state(self):
        s=generate('diagnostic-test')
        s['observation']={'probes':{'remote':{'at':time.time(),'status':'passed','detail':'ICMP : 2 / 2 réponses'}}}
        return s

    def test_successful_ping_does_not_hide_disabled_remote_service(self):
        with tempfile.TemporaryDirectory() as d:
            w=Workspace(Path(d)/'session.json');w.state=self.state();w.state['remote_service']=False
            with self.assertRaisesRegex(ValueError,'Service de prise en main') as error:w.action('connect')
            self.assertNotIn('2 / 2',str(error.exception))
            self.assertEqual(evaluate(w.state,'remote')['tree']['status'],'passed')

    def test_technician_refusal_is_separate_from_observed_network(self):
        s=self.state();s['technician_session']={'connection':'console','location':'office','pending':None}
        r=evaluate(s,'remote')
        self.assertFalse(r['allowed']);self.assertEqual(r['tree']['status'],'passed')
        self.assertEqual(r['tree']['children'][0]['id'],'technician')
        self.assertEqual(r['tree']['children'][0]['status'],'failed')

    def test_pending_technician_is_unknown_not_network_failure(self):
        s=self.state();s['technician_session']={'pending':{'location':'office'}}
        r=evaluate(s,'remote');self.assertEqual(r['status'],'unknown')
        self.assertEqual(r['tree']['status'],'passed')

    def test_expired_network_blocks_lower_prerequisites(self):
        s=self.state();s['observation']['probes']['remote']['at']=time.time()-60
        r=evaluate(s,'remote');self.assertEqual(r['tree']['status'],'unknown')
        self.assertEqual(r['tree']['children'][0]['status'],'blocked')
