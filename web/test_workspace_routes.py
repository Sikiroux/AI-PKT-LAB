import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock
from workspace_app import Controller
from workspace_model import generate
from workspace_routes import WorkspaceRoutes

class RouteTests(unittest.TestCase):
    def setUp(self):
        self.folder=tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.controller=Controller(None,self.folder.name)
        self.controller.workspace.state=generate('routes')
        self.routes=WorkspaceRoutes(self.controller,'test-token')
        self.handler=Mock()

    def test_namespace_and_token(self):
        for path in ('/workspace','/workspace/desktop'):
            self.handler.path=path
            self.assertTrue(self.routes.get(self.handler))
            html=self.handler.send.call_args.args[1]
            self.assertNotIn('__TOKEN__',html)
            self.assertNotIn('__API_BASE__',html)
            self.assertIn('test-token',html)
        self.handler.path='/state'
        self.assertFalse(self.routes.get(self.handler))

    def test_static_traversal_rejected(self):
        self.handler.path='/osjs/../../workspace-session/session.json'
        self.routes.get(self.handler)
        self.assertEqual(self.handler.send.call_args.args[0],404)

    def test_action_and_refresh(self):
        self.handler.path='/workspace/action'
        self.routes.post(self.handler,{'action':'grant_read'})
        self.assertTrue(self.controller.workspace.state['read_allowed'])
        self.controller.observe=Mock()
        self.handler.path='/workspace/refresh'
        self.routes.post(self.handler,{})
        self.controller.observe.assert_called_once_with(blocking=True)

    def test_assets_present(self):
        root=Path(__file__).parent
        self.assertTrue((root/'vendor/osjs/main.js').stat().st_size>100000)
        self.assertIn('osjsClient',(root/'desktop.html').read_text())

if __name__=='__main__': unittest.main()
