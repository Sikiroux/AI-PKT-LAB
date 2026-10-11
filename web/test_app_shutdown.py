import threading
import unittest
from unittest.mock import Mock
from app_shutdown import prepare_shutdown

class ShutdownTests(unittest.TestCase):
    def test_save_both_before_stop(self):
        c=Mock();c.lock=threading.RLock();t=Mock();t.metadata_lock=threading.RLock();stop=threading.Event()
        c.workspace.save.side_effect=lambda:self.assertFalse(stop.is_set())
        t.save.side_effect=lambda:self.assertFalse(stop.is_set())
        result=prepare_shutdown(c,t,stop)
        self.assertTrue(result['stopping']);self.assertTrue(stop.is_set())
        c.workspace.save.assert_called_once();t.save.assert_called_once()
    def test_failed_save_does_not_stop(self):
        c=Mock();c.lock=threading.RLock();t=Mock();t.metadata_lock=threading.RLock();stop=threading.Event()
        c.workspace.save.side_effect=OSError('disk full')
        with self.assertRaises(OSError):prepare_shutdown(c,t,stop)
        self.assertFalse(stop.is_set());t.save.assert_not_called()
