import importlib.util
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    'commands_appearance_activation', ROOT / 'scripts/activate-commands-appearance.py')
activation = importlib.util.module_from_spec(spec)
spec.loader.exec_module(activation)


class CommandsAppearanceActivationTest(unittest.TestCase):
    def test_marker_activation_and_rollback_are_exact_and_idempotent(self):
        with tempfile.TemporaryDirectory() as folder:
            state = Path(folder) / 'limux' / 'commands-appearance'
            lock = Path(folder) / 'picker.lock'
            with patch.object(activation, 'preflight'), \
                 patch.object(activation.commands, 'picker_lock',
                              side_effect=lambda: os.open(lock, os.O_CREAT | os.O_RDWR, 0o600)):
                activation.change('activate', state)
                self.assertEqual(state.read_bytes(), activation.MARKER)
                self.assertEqual(state.stat().st_mode & 0o777, 0o600)
                self.assertTrue(activation.commands.appearance_active(state))
                activation.change('activate', state)
                activation.change('rollback', state)
                self.assertFalse(state.exists())
                activation.change('rollback', state)

    def test_reject_unknown_marker_and_preserve_rollback_after_source_drift(self):
        with tempfile.TemporaryDirectory() as folder:
            state = Path(folder) / 'marker'
            lock = Path(folder) / 'picker.lock'
            state.write_bytes(b'unknown\n')
            state.chmod(0o600)
            with self.assertRaises(RuntimeError):
                activation.marker(state)
            state.write_bytes(b'neutral-v1 ' + b'0' * 64 + b'\n')
            with self.assertRaises(RuntimeError):
                activation.commands.appearance_active(state)
            with patch.object(activation.commands, 'picker_lock',
                              side_effect=lambda: os.open(lock, os.O_CREAT | os.O_RDWR, 0o600)):
                activation.change('rollback', state)
            self.assertFalse(state.exists())

    def test_failed_preflight_does_not_write_marker(self):
        with tempfile.TemporaryDirectory() as folder:
            state = Path(folder) / 'marker'
            lock = Path(folder) / 'picker.lock'
            with patch.object(activation, 'preflight', side_effect=RuntimeError('drift')), \
                 patch.object(activation.commands, 'picker_lock',
                              side_effect=lambda: os.open(lock, os.O_CREAT | os.O_RDWR, 0o600)):
                with self.assertRaisesRegex(RuntimeError, 'drift'):
                    activation.change('activate', state)
            self.assertFalse(state.exists())
