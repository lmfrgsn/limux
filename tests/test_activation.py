import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
spec = importlib.util.spec_from_file_location('activation', ROOT/'scripts/activate-mangobar.py')
activation = importlib.util.module_from_spec(spec)
spec.loader.exec_module(activation)


class ActivationTests(unittest.TestCase):
    def test_success_and_idempotence(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)/'style.css'
            p.write_bytes(b'old')
            calls = []
            activation.transition(p, b'new', lambda: calls.append('refresh'), lambda: calls.append('verify'))
            activation.transition(p, b'new', lambda: calls.append('refresh'), lambda: calls.append('verify'))
            self.assertEqual(p.read_bytes(), b'new')
            self.assertEqual(calls, ['refresh', 'verify', 'verify'])
            self.assertEqual(list(Path(d).iterdir()), [p])

    def test_failed_restart_restores_prior_style_and_restarts(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)/'style.css'
            p.write_bytes(b'old')
            attempts = []
            def refresh():
                attempts.append(p.read_bytes())
                if len(attempts) == 1:
                    raise RuntimeError('simulated restart failure')
            with self.assertRaisesRegex(RuntimeError, 'prior CSS and managed bar restored'):
                activation.transition(p, b'new', refresh, lambda: None)
            self.assertEqual(attempts, [b'new', b'old'])
            self.assertEqual(p.read_bytes(), b'old')

    def test_failed_verification_rolls_back(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)/'style.css'
            p.write_bytes(b'old')
            def verify():
                if p.read_bytes() == b'new':
                    raise RuntimeError('duplicate process')
            with self.assertRaisesRegex(RuntimeError, 'prior CSS and managed bar restored'):
                activation.transition(p, b'new', lambda: None, verify)
            self.assertEqual(p.read_bytes(), b'old')

    def test_refuses_symlink(self):
        with tempfile.TemporaryDirectory() as d:
            target = Path(d)/'target'
            target.write_bytes(b'old')
            link = Path(d)/'style.css'
            link.symlink_to(target)
            with self.assertRaisesRegex(RuntimeError, 'regular owned file'):
                activation.atomic_write(link, b'new')
            self.assertEqual(target.read_bytes(), b'old')
