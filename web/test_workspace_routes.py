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

    def test_old_remote_tab_cannot_mutate_new_environment(self):
        self.controller.workspace.state['environment_id'] = 'current'
        self.handler.path = '/workspace/action'
        with self.assertRaises(ValueError):
            self.routes.post(self.handler, {'action': 'grant_read', 'environment_id': 'old'})
        self.assertFalse(self.controller.workspace.state['read_allowed'])

    def test_create_first_environment_accepts_null_context(self):
        self.controller.workspace.state = None
        self.controller.new = Mock(return_value={'created': True})
        self.handler.path = '/workspace/new'
        self.routes.post(self.handler, {'seed': 'first', 'environment_id': None})
        self.controller.new.assert_called_once_with('first')
        self.assertEqual(self.handler.send.call_args.args, (200, {'created': True}))

    def test_create_and_select_deliberately_change_context(self):
        self.controller.workspace.state['environment_id'] = 'current'
        self.controller.new = Mock(return_value={})
        self.controller.select = Mock(return_value={})
        self.handler.path = '/workspace/new'
        self.routes.post(self.handler, {'seed': 'next', 'environment_id': 'old'})
        self.controller.new.assert_called_once_with('next')
        self.handler.path = '/workspace/select'
        self.routes.post(self.handler, {'id': 'saved', 'environment_id': 'old'})
        self.controller.select.assert_called_once_with('saved')

    def test_assets_present(self):
        root=Path(__file__).parent
        self.assertTrue((root/'vendor/osjs/main.js').stat().st_size>100000)
        self.assertIn('osjsClient',(root/'desktop.html').read_text())

if __name__=='__main__': unittest.main()
