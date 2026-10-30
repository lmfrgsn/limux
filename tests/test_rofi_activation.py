import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
spec = importlib.util.spec_from_file_location('rofi_activation', ROOT/'scripts/activate-rofi.py')
activation = importlib.util.module_from_spec(spec)
spec.loader.exec_module(activation)


class RofiActivationTests(unittest.TestCase):
    def test_failed_verification_restores_exact_bytes_and_mode(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)/'theme.rasi'
            p.write_bytes(b'previous')
            p.chmod(0o640)
            def fail():
                raise RuntimeError('native verification failed')
            with self.assertRaisesRegex(RuntimeError, 'prior live theme restored'):
                activation.transition(p, b'new', fail)
            self.assertEqual(p.read_bytes(), b'previous')
            self.assertEqual(p.stat().st_mode & 0o777, 0o640)
            self.assertEqual(list(Path(d).iterdir()), [p])

    def test_idempotent_does_not_replace_file(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)/'theme.rasi'
            p.write_bytes(b'same')
            inode = p.stat().st_ino
            self.assertFalse(activation.transition(p, b'same', lambda: None))
            self.assertEqual(p.stat().st_ino, inode)

    def test_refuses_symlink(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)/'theme.rasi'
            p.write_bytes(b'original')
            link = Path(d)/'link'
            link.symlink_to(p)
            with self.assertRaises(RuntimeError):
                activation.transition(link, b'new', lambda: None)
            self.assertEqual(p.read_bytes(), b'original')

    def test_approved_output_is_unchanged_and_recovery_ignores_future_drift(self):
        manifest = json.loads((ROOT/'themes/recovery/rofi.json').read_text())
        self.assertEqual(activation.digest(activation.payload('activate', manifest)), manifest['baseline_sha256'])
        with patch.object(activation, 'render', return_value='unapproved future design'):
            with self.assertRaisesRegex(RuntimeError, 'differs from the approved picker'):
                activation.payload('activate', manifest)
            self.assertEqual(activation.digest(activation.payload('rollback', manifest)), manifest['previous_sha256'])
            self.assertEqual(activation.digest(activation.payload('restore-original', manifest)), manifest['rollback_sha256'])

    @unittest.skipUnless(shutil.which('rofi'), 'Rofi not installed')
    def test_real_parser_default_launcher_activation_and_rollback_in_isolated_home(self):
        # Real Rofi parsing and default config resolution, but no compositor,
        # no user files and no application launch/input simulation.
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            repo = home/'repo'
            (repo/'themes/recovery').mkdir(parents=True)
            for file in ('rofi-before-rhapsody.rasi', 'rofi-rhapsody-yellow-edge.rasi', 'rofi-search.svg', 'rofi.json'):
                shutil.copyfile(ROOT/'themes/recovery'/file, repo/'themes/recovery'/file)
            shutil.copyfile(ROOT/'themes/rhapsody.toml', repo/'themes/rhapsody.toml')
            config = home/'.config/rofi/config.rasi'
            config.parent.mkdir(parents=True)
            live = config.parent/'charcoal.rasi'
            old = (repo/'themes/recovery/rofi-before-rhapsody.rasi').read_bytes()
            live.write_bytes(old)
            icon = config.parent/'assets/search.svg'
            icon.parent.mkdir()
            icon.write_bytes((repo/'themes/recovery/rofi-search.svg').read_bytes())
            config.write_text('configuration {\n modi: "drun";\n matching: "fuzzy";\n kb-cancel: "Escape";\n kb-accept-entry: "Return,KP_Enter";\n kb-row-up: "Up,Control+p";\n kb-row-down: "Down,Control+n";\n}\n@theme "'+str(live)+'"\n')
            mango = home/'.config/mango/config.conf'
            mango.parent.mkdir()
            mango.write_text('bind=SUPER,space,spawn,rofi -show drun\n')
            for filename in ('.config/mangobar/style.css', '.config/mangobar/config.jsonc', '.config/foot/foot.ini'):
                p = home/filename
                p.parent.mkdir(exist_ok=True)
                p.write_text('untouched fixture')
            manifest_path = repo/'themes/recovery/rofi.json'
            manifest = json.loads(manifest_path.read_text())
            manifest['config_sha256'] = activation.digest(config.read_bytes())
            manifest_path.write_text(json.dumps(manifest))
            runtime = home/'runtime'
            runtime.mkdir(mode=0o700)
            with patch.object(activation, 'ROOT', repo), patch.object(Path, 'home', return_value=home), \
                 patch.dict(os.environ, {'HOME': str(home), 'XDG_CONFIG_HOME': str(home/'.config'), 'XDG_RUNTIME_DIR': str(runtime)}), \
                 patch.object(activation, 'require_session'), patch.object(activation, 'require_closed'):
                before = activation.functional_config(activation.dump(['-dump-config']))
                expected = {'activate': 'baseline_sha256', 'check': 'baseline_sha256',
                            'rollback': 'previous_sha256', 'restore-original': 'rollback_sha256'}
                for action in ('activate', 'activate', 'check', 'rollback', 'activate', 'restore-original'):
                    with patch.object(sys, 'argv', ['activate-rofi.py', action]):
                        activation.main()
                    self.assertEqual(activation.functional_config(activation.dump(['-dump-config'])), before)
                    self.assertEqual(activation.digest(live.read_bytes()), manifest[expected[action]])
                self.assertEqual(live.read_bytes(), old)
                live.write_bytes(b'unknown user edits')
                with patch.object(sys, 'argv', ['activate-rofi.py', 'activate']):
                    with self.assertRaisesRegex(RuntimeError, 'Unknown live theme'):
                        activation.main()
                self.assertEqual(live.read_bytes(), b'unknown user edits')
