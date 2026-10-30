import copy
import re
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import tomllib
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
from rofi import render, THEME_CONFIGURATION
from mangobar import render as render_bar
import hashlib
import json


class RofiTests(unittest.TestCase):
    def setUp(self):
        self.theme = tomllib.loads((ROOT/'themes/rhapsody.toml').read_text())

    def test_visual_only_and_shared_selection(self):
        rasi = render(self.theme)
        configuration = re.search(r'configuration \{\n(.*?)\n\}', rasi, re.S).group(1)
        keys = {line.strip().split(':', 1)[0] for line in configuration.splitlines() if line.strip()}
        self.assertEqual(keys, set(THEME_CONFIGURATION))
        for forbidden in ('kb-', 'matching:', 'terminal:', 'modi:', 'exec:', 'element-icon'):
            self.assertNotIn(forbidden, rasi)
        # Selection is the graphite inset shared with Thunar, not the old yellow edge.
        self.assertIn('background-color: #343442;', re.search(r'element selected.normal \{([^}]+)', rasi).group(1))
        self.assertNotIn('#E3BE47', rasi)
        self.assertIn('tab-stops: [ 430px ];', rasi)
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
            self.assertNotIn('textbox-heading', result.stdout)
            self.assertIn('box-search', result.stdout)
            self.assertNotIn('Parser error', result.stderr)
            # Exit code alone missed the installed lexer's greedy string rule.
            blocks = dict(re.findall(r'(?m)^([\w*-]+) \{([^}]+)\}', result.stdout))
            def prop(widget, key):
                match = re.search(r'(?m)^\s*' + re.escape(key) + r':\s*(.*);\s*$', blocks[widget])
                self.assertIsNotNone(match, (widget, key))
                return match.group(1).strip()
            self.assertEqual(prop('entry', 'placeholder'), '"Search applications"')
            self.assertEqual(prop('entry', 'font'), '"Inter 11"')
            self.assertNotIn('RHAPSODY /', result.stdout)
            self.assertNotIn('textbox-edition', result.stdout)
            for widget in ('box-search', 'inputbar', 'message'):
                self.assertEqual(prop(widget, 'expand'), 'false')
            self.assertEqual(prop('inputbar', 'orientation'), 'horizontal')
            self.assertEqual(prop('box-search', 'orientation'), 'vertical')
            self.assertEqual(prop('entry', 'expand'), 'true')
            self.assertEqual(prop('listview', 'fixed-height'), 'false')
            self.assertEqual(prop('listview', 'dynamic'), 'true')
            self.assertEqual(prop('listview', 'cycle'), 'true')

    def test_one_property_per_line(self):
        # Prevent a second quoted value from being swallowed into a string.
        for line in render(self.theme).splitlines():
            self.assertLessEqual(line.count(';'), 1, line)
