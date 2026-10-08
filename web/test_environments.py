import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from workspace_app import Controller
from workspace_model import Workspace, generate


def fake_build(seed, folder, initial_fault=True):
    s = generate(seed)
    s['network_file'] = str(Path(folder) / 'entreprise.pkt')
    return s

class EnvironmentTests(unittest.TestCase):
    @patch('workspace_app.build', side_effect=fake_build)
    def test_switch_preserves_rights_and_closes_old_session(self, _):
        with tempfile.TemporaryDirectory() as d:
            c = Controller(None, d)
            c.new('first'); first = c.environments.data['active']
            c.workspace.state.update(read_allowed=True, remote_session=True)
            c.new('second'); second = c.environments.data['active']
            self.assertNotEqual(first, second)
            self.assertNotEqual(c.workspace.state['network_file'], fake_build('first', c.environments.path(first).parent / 'network')['network_file'])
            c.select(first)
            self.assertTrue(c.workspace.state['read_allowed'])
            self.assertFalse(c.workspace.state['remote_session'])
            self.assertIsNone(c.workspace.state['observation'])
            restarted = Controller(None, d)
            self.assertEqual(restarted.workspace.state['seed'], 'first')
            self.assertEqual(len(restarted.environments.public()['items']), 2)

    def test_legacy_is_kept_at_original_location(self):
        with tempfile.TemporaryDirectory() as d:
            w = Workspace(Path(d) / 'session.json');w.state = generate('old');w.save()
            c = Controller(None, d)
            self.assertEqual(c.environments.data['active'], 'legacy')
            self.assertEqual(c.workspace.path, w.path)
            self.assertEqual(c.workspace.state['seed'], 'old')
            with self.assertRaises(ValueError): c.select('../../elsewhere')

    @patch('workspace_app.build', side_effect=fake_build)
    def test_failed_creation_leaves_active_environment(self, _):
        with tempfile.TemporaryDirectory() as d:
            c = Controller(None, d);c.new('first');ident = c.environments.data['active']
            with patch('workspace_app.build', side_effect=ValueError('generation failed')):
                with self.assertRaises(ValueError): c.new('second')
            self.assertEqual(c.environments.data['active'], ident)
            self.assertEqual(c.workspace.state['seed'], 'first')
