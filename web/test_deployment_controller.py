import copy
import threading
import unittest
from unittest.mock import Mock, patch
import desktop_controller as dc

class ControllerTests(unittest.TestCase):
    def setUp(self):
        self.state={'seed':'controller','environment_id':'env','desktop_services':{},'devices':{'client':{'name':'CLIENT'}},'remote_session':False}
        self.c=Mock();self.c.lock=threading.RLock();self.c.workspace.state=self.state
    def call(self,action,data=None):
        with patch.object(dc.ds,'ensure',return_value=False):return dc.handle(self.c,'deployment/'+action,data or {})
    def test_lazy_save(self):
        first=self.call('state');self.c.workspace.save.assert_called_once();self.assertEqual(first,self.call('state'))
    def test_requires_admin(self):
        self.call('state')
        with patch.object(dc,'admin',side_effect=ValueError('Network')):
            with self.assertRaises(ValueError):self.call('operation',dict(operation='start',expected_revision=0))
        self.assertEqual(self.state['desktop_services']['deployment']['stage'],'idle')
    def test_isolated_and_persisted(self):
        original=copy.deepcopy(self.state['devices']);self.call('state')
        with patch.object(dc,'admin'):self.call('operation',dict(operation='start',expected_revision=0))
        self.assertEqual(self.state['devices'],original);self.assertFalse(self.state['remote_session']);self.assertEqual(self.call('state')['service']['stage'],'media');self.c.workspace.event.assert_called_once()
    def test_reset_monotonic(self):
        self.call('state')
        with patch.object(dc,'admin'):
            self.call('operation',dict(operation='start',expected_revision=0));r=self.call('operation',dict(operation='reset',expected_revision=1))
            self.assertEqual(r['service']['revision'],2);self.assertEqual(r['service']['attempt'],2);self.assertEqual(r['service']['stage'],'idle')
            with self.assertRaises(ValueError):self.call('operation',dict(operation='reset',expected_revision=1))

if __name__=='__main__':unittest.main()
