import copy
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import tomllib
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
from rofi import render
from mangobar import render as render_bar
import hashlib
import json


class RofiTests(unittest.TestCase):
    def setUp(self):
        self.theme = tomllib.loads((ROOT/'themes/rhapsody.toml').read_text())

    def test_visual_only_and_shared_signals(self):
        rasi = render(self.theme)
        self.assertNotIn('configuration {', rasi)
        for forbidden in ('kb-', 'matching:', 'terminal:', 'modi:', 'exec:'):
            self.assertNotIn(forbidden, rasi)
        other = copy.deepcopy(self.theme)
        other['colors']['signal_yellow'] = '#E8C64E'
        changed = render(other)
        self.assertIn('#E8C64E', changed)
        self.assertNotIn('#E3BE47', changed)
        self.assertIn('box-search', rasi)
        self.assertIn('highlight: bold;', rasi)

    def test_invalid_tokens_and_low_contrast(self):
        for section, key, value in [('rofi', 'width', -1), ('colors', 'canvas', '#343442'),
                                    ('colors', 'metal', 'invalid'), ('typography', 'sans', 'a";')]:
            other = copy.deepcopy(self.theme)
            other[section][key] = value
            with self.assertRaises(ValueError):
                render(other)

    def test_mangobar_approval_pin_unchanged(self):
        manifest = json.loads((ROOT/'themes/recovery/mangobar.json').read_text())
        self.assertEqual(hashlib.sha256(render_bar(self.theme).encode()).hexdigest(), manifest['baseline_sha256'])
        recovery = ROOT/'themes/recovery/mangobar-before-rhapsody.css'
        self.assertEqual(hashlib.sha256(recovery.read_bytes()).hexdigest(), manifest['rollback_sha256'])

    @unittest.skipUnless(shutil.which('rofi'), 'Rofi is not installed')
    def test_native_theme_parser(self):
        with tempfile.TemporaryDirectory() as d:
            theme = Path(d)/'theme.rasi'
            theme.write_text(render(self.theme))
            result = subprocess.run(['rofi', '-no-config', '-theme', str(theme), '-dump-theme'],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('textbox-heading', result.stdout)
            self.assertIn('box-search', result.stdout)
            self.assertNotIn('Parser error', result.stderr)
