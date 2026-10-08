"""Échecs du lanceur, sans génération Packet Tracer."""
import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch
from subprocess import CompletedProcess
spec = importlib.util.spec_from_file_location('recipe_runner', Path(__file__).with_name('run_tests.py'))
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)

class RunnerTests(unittest.TestCase):
    def test_missing_node(self):
        with patch.object(runner.shutil, 'which', return_value=None), patch.object(runner.subprocess, 'run') as run:
            self.assertEqual(runner.main(), 2)
            run.assert_not_called()

    def test_failure_keeps_running(self):
        calls = []
        def execute(command, **kwargs):
            calls.append(command)
            self.assertEqual(kwargs['cwd'], runner.ROOT)
            return CompletedProcess(command, 1 if len(calls) == 1 else 0)
        with patch.object(runner.shutil, 'which', return_value='node'), patch.object(runner.subprocess, 'run', side_effect=execute):
            self.assertEqual(runner.main(), 1)
        self.assertEqual(len(calls), 4 + len(list((runner.ROOT / 'web').glob('test_*.js'))))
        self.assertEqual(calls[3][-3:], ['web', '-p', 'test_*.py'])

if __name__ == '__main__':
    unittest.main()
