import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('quiet_activation',
                                               ROOT / 'scripts/activate-quiet-bar.py')
activation = importlib.util.module_from_spec(spec)
spec.loader.exec_module(activation)


class QuietActivationTest(unittest.TestCase):
    def test_activation_and_rollback_restore_exact_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            upstream = root / 'upstream/mangobar'
            launcher = root / 'bin/limux-bar'
            config = root / 'config.jsonc'
            css = root / 'style.css'
            mango = root / 'mango.conf'
            patched = root / 'libexec/quiet/mangobar'
            state = root / 'state/quiet'
            old = {'launcher': ("BINARY = HOME / '.local/bin/mangobar'\n").encode(),
                   'config': b'{"modules-left":["workspaces","layout","window"]}\n',
                   'css': b'old-style\n'}
            new = {'config': b'{"modules-left":["workspaces","window"]}\n',
                   'css': b'new-style\n'}
            binary = b'patched-native-binary'
            for path, data in ((upstream, b'upstream-native-binary'),
                               (launcher, old['launcher']), (config, old['config']),
                               (css, old['css']), (mango, b'one startup entry')):
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(data)
            expected = {
                'upstream': activation.digest(upstream.read_bytes()),
                'launcher': activation.digest(old['launcher']),
                'config': activation.digest(old['config']),
                'css': activation.digest(old['css']),
                'mango': activation.digest(mango.read_bytes()),
            }
            with patch.multiple(activation, UPSTREAM=upstream, LAUNCHER=launcher,
                                CONFIG=config, CSS=css, MANGO=mango, PATCHED=patched,
                                STATE=state, EXPECTED=expected), \
                 patch.object(activation, 'startup_entry'), \
                 patch.object(activation, 'require_session'), \
                 patch.object(activation, 'managed_bar'), \
                 patch.object(activation, 'existing_bar_or_none'), \
                 patch.object(activation, 'generate_candidate', return_value=(new['config'], new['css'], binary)), \
                 patch.object(activation, 'refresh_and_verify'):
                activation.activate()
                self.assertEqual(config.read_bytes(), new['config'])
                self.assertEqual(css.read_bytes(), new['css'])
                self.assertEqual(patched.read_bytes(), binary)
                self.assertTrue(state.exists())
                activation.rollback()
                self.assertEqual(config.read_bytes(), old['config'])
                self.assertEqual(css.read_bytes(), old['css'])
                self.assertEqual(launcher.read_bytes(), old['launcher'])
                self.assertFalse(state.exists())
                self.assertFalse(patched.exists())
                with patch.object(activation, 'refresh_and_verify',
                                  side_effect=[RuntimeError('restart failed'), None]):
                    with self.assertRaisesRegex(RuntimeError, 'original bar restored'):
                        activation.activate()
                self.assertEqual(config.read_bytes(), old['config'])
                self.assertEqual(css.read_bytes(), old['css'])
                self.assertEqual(launcher.read_bytes(), old['launcher'])
                self.assertFalse(state.exists())
                self.assertFalse(patched.exists())


if __name__ == '__main__':
    unittest.main()
