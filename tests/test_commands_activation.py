import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('activate_commands', Path(__file__).resolve().parents[1] / 'scripts/activate-commands.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class ActivationTest(unittest.TestCase):
    def test_round_trip_and_preserve_launcher(self):
        with tempfile.TemporaryDirectory() as folder:
            config = Path(folder) / 'config.conf'
            original = 'other=keep\n' + module.LAUNCHER + '\n'
            config.write_text(original)
            with patch.object(module, 'CONFIG', config), patch.object(module, 'run'):
                module.change('activate')
                self.assertIn(module.BINDING, config.read_text())
                self.assertEqual(config.read_text().count(module.LAUNCHER), 1)
                module.change('activate')
                module.change('rollback')
                self.assertEqual(config.read_text(), original)

    def test_conflict_and_failed_preflight_leave_file_intact(self):
        with tempfile.TemporaryDirectory() as folder:
            config = Path(folder) / 'config.conf'
            config.write_text(module.LAUNCHER + '\n' + 'bind=SUPER,k,spawn,other\n')
            with patch.object(module, 'CONFIG', config), patch.object(module, 'run'):
                with self.assertRaises(RuntimeError):
                    module.change('activate')
            self.assertIn('spawn,other', config.read_text())
            config.write_text(module.LAUNCHER + '\n')
            before = config.read_bytes()
            with patch.object(module, 'CONFIG', config), patch.object(module, 'run', side_effect=RuntimeError('IPC unavailable')):
                with self.assertRaises(RuntimeError):
                    module.change('activate')
            self.assertEqual(config.read_bytes(), before)
