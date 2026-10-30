import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('foot_activation', ROOT/'scripts/activate-foot.py')
a = importlib.util.module_from_spec(spec)
spec.loader.exec_module(a)
spec = importlib.util.spec_from_file_location('foot_preview', ROOT/'scripts/preview-foot.py')
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)


class FootActivationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.folder = Path(self.tmp.name)
        self.config = self.folder/'foot.ini'
        self.style = self.folder/'rhapsody.ini'
        self.manifest = json.loads((ROOT/'themes/recovery/foot.json').read_text())
        # Independent fixture with bindings, scrollback and terminal behaviour.
        self.original = (b'[main]\nfont=DEjaVu Sans Mono:size=16\nterm=foot\n'
                         b'[scrollback]\nlines=4321\n[key-bindings]\n'
                         b'clipboard-copy=Super+c\nclipboard-paste=Super+v\n')
        self.manifest['original_config_sha256'] = a.digest(self.original)
        self.config.write_bytes(self.original)
        self.config.chmod(0o640)
        self.data = a.candidate(self.manifest)
        self.previous = a.previous(self.manifest)
        self.active = self.original.replace(self.manifest['original_font_line'].encode(), a.include_line(self.style))

    def apply(self, data, verify=None):
        a.versions(self.config, self.style, self.manifest)
        a.transition(self.config, self.style, self.original, self.active, data,
                     verify or (lambda expected: a.native(self.config)))

    @unittest.skipUnless(shutil.which('foot'), 'native Foot unavailable')
    def test_native_activation_idempotence_and_exact_rollback(self):
        self.apply(self.data)
        self.assertEqual(self.config.read_bytes(), self.active)
        self.assertEqual(self.config.stat().st_mode & 0o777, 0o640)
        self.assertEqual(self.style.read_bytes(), self.data)
        inode = self.config.stat().st_ino
        self.apply(self.data)
        self.assertEqual(self.config.stat().st_ino, inode)
        self.apply(self.previous)
        self.apply(None)
        self.assertEqual(self.config.read_bytes(), self.original)
        self.assertFalse(self.style.exists())
        self.assertEqual(list(self.folder.iterdir()), [self.config])

    def test_verification_failure_restores_both_files(self):
        def fail(expected):
            raise RuntimeError('simulated parser failure')
        with self.assertRaisesRegex(RuntimeError, 'simulated'):
            self.apply(self.data, fail)
        self.assertEqual(self.config.read_bytes(), self.original)
        self.assertFalse(self.style.exists())
        self.apply(self.data, lambda _: None)
        with self.assertRaisesRegex(RuntimeError, 'simulated'):
            self.apply(None, fail)
        self.assertEqual(self.config.read_bytes(), self.active)
        self.assertEqual(self.style.read_bytes(), self.data)

    def test_recover_interrupted_states(self):
        # Crash between installing dependency and switching the config.
        self.style.write_bytes(self.data)
        self.apply(None, lambda _: None)
        self.assertFalse(self.style.exists())
        # Missing generated file can be repaired or rolled back.
        self.config.write_bytes(self.active)
        self.apply(self.data, lambda _: None)
        self.style.unlink()
        self.apply(None, lambda _: None)
        self.assertEqual(self.config.read_bytes(), self.original)

    def test_refuse_unknown_config_style_and_symlinks(self):
        self.config.write_bytes(self.original + b'\n# user edit\n')
        with self.assertRaises(RuntimeError):
            a.versions(self.config, self.style, self.manifest)
        self.config.write_bytes(self.original)
        self.style.write_bytes(b'unknown')
        with self.assertRaises(RuntimeError):
            a.versions(self.config, self.style, self.manifest)
        self.style.unlink()
        self.style.symlink_to(self.config)
        with self.assertRaises(RuntimeError):
            a.versions(self.config, self.style, self.manifest)

    def test_approval_pin_and_independent_rollback(self):
        bad = dict(self.manifest, baseline_sha256='0' * 64)
        with self.assertRaises(RuntimeError):
            a.candidate(bad)
        self.apply(self.data, lambda _: None)
        with patch.object(a, 'render', side_effect=RuntimeError('future adapter broken')):
            self.apply(None, lambda _: None)
        self.assertEqual(self.config.read_bytes(), self.original)

    def test_previous_yellow_cursor_is_pinned_and_restorable(self):
        self.assertEqual(a.digest(self.previous), self.manifest['previous_sha256'])
        self.apply(self.data, lambda _: None)
        self.apply(self.previous, lambda _: None)
        self.assertEqual(self.style.read_bytes(), self.previous)
        self.assertEqual(self.config.read_bytes(), self.active)
        self.assertIn(b'cursor=343442 E3BE47', self.style.read_bytes())

    def test_real_cli_stops_before_writes_without_wayland(self):
        # Use fixture's hash to exercise main while all writes are intercepted.
        with patch.dict(os.environ, {'XDG_CONFIG_HOME': str(self.folder)}), \
             patch.object(a, 'versions', return_value=(self.original, None, self.original, self.active)), \
             patch.object(a, 'stage_validate'), \
             patch.object(a, 'require_session', side_effect=RuntimeError('No Wayland')), \
             patch.object(a, 'transition') as transition, \
             patch('sys.argv', ['activate-foot.py', 'activate']):
            with self.assertRaisesRegex(RuntimeError, 'No Wayland'):
                a.main()
            transition.assert_not_called()

    def test_normal_shell_preview_has_no_specimen_or_shell_override(self):
        directory = self.folder/'foot'
        directory.mkdir()
        (directory/'foot.ini').write_bytes(self.original)
        process = unittest.mock.Mock()
        process.wait.return_value = 0
        process.poll.return_value = 0
        real_popen = subprocess.Popen
        def launch_only(argv, *args, **kwargs):
            if '-T' in argv:
                return process
            return real_popen(argv, *args, **kwargs)
        with patch.dict(os.environ, {'XDG_CONFIG_HOME': str(self.folder)}), \
             patch('sys.argv', ['preview-foot.py', '--shell']), \
             patch.object(p.subprocess, 'Popen', side_effect=launch_only) as launch:
            p.main()  # Real native parser still runs against the fixture.
        argv = launch.call_args.args[0]
        self.assertEqual(argv[-2:], ['-T', 'Foot — Rhapsody candidate'])
        self.assertNotIn('--sample', argv)
        self.assertNotIn('shell=', ' '.join(argv))
        self.assertNotIn('key-bindings.', ' '.join(argv))
        self.assertEqual((directory/'foot.ini').read_bytes(), self.original)


if __name__ == '__main__':
    unittest.main()
