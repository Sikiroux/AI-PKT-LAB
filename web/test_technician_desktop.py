import tempfile
import threading
import unittest
from unittest.mock import Mock
from workspace_app import Controller
from workspace_routes import WorkspaceRoutes

class TechnicianTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.engine=Mock();self.engine.lock=threading.RLock()
        self.c=Controller(self.engine,self.temp.name)
        self.c.workspace.state={'environment_id':'current'}
        self.c.identities=Mock(return_value={'client':{'name':'Client'},'technician':{'name':'Tech'}})
        self.routes=WorkspaceRoutes(self.c,'token');self.handler=Mock()

    def test_technician_deep_link_serves_desktop(self):
        self.handler.path='/workspace/technician?app=deployment'
        self.assertTrue(self.routes.get(self.handler))
        self.assertIn('const technician=true',self.handler.send.call_args.args[1])
    def test_source_is_actual_technician_even_without_remote_session(self):
        self.c.ping('192.168.1.1',source='technician')
        self.engine.ping.assert_called_once_with('Tech','192.168.1.1')
        self.c.identities.assert_called_once()

    def test_old_client_source_preserved(self):
        self.c.ping('192.168.1.1')
        self.engine.ping.assert_called_once_with('Client','192.168.1.1')

    def test_invalid_source_and_target_rejected(self):
        for target,source in [('192.168.1.1','server'),('echo hi','technician')]:
            with self.assertRaises(ValueError):self.c.ping(target,source)
        self.engine.ping.assert_not_called()

    def test_stale_desktop_cannot_ping_new_environment(self):
        self.handler.path='/workspace/ping'
        with self.assertRaises(ValueError):self.routes.post(self.handler,{'environment_id':'old','source':'technician','target':'192.168.1.1'})
        self.engine.ping.assert_not_called()

    def test_mode_only_assigned_by_route(self):
        for path,value in [('/workspace/desktop','false'),('/workspace/technician','true')]:
            self.handler.path=path;self.routes.get(self.handler)
            html=self.handler.send.call_args.args[1]
            self.assertIn('const technician='+value,html)
            self.assertNotIn('__TECHNICIAN__',html)

if __name__=='__main__':unittest.main()
