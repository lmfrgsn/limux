import copy
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import tomllib
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
import btop  # noqa: E402

spec = importlib.util.spec_from_file_location('btop_activation', ROOT/'scripts/activate-btop.py')
a = importlib.util.module_from_spec(spec)
spec.loader.exec_module(a)
THEME = tomllib.loads((ROOT/'themes/rhapsody.toml').read_text())
MANIFEST = json.loads(a.MANIFEST.read_text())
CONF = '#? Config file for btop\ncolor_theme = "Default"\ntheme_background = true\ntruecolor = true\nrounded_corners = true\nupdate_ms = 1500\nproc_sorting = "memory"\n'


class BtopTests(unittest.TestCase):
    def test_theme_roles(self):
        t = btop.render(THEME)
        self.assertIn('theme[main_bg]="#2F303B"', t)
        self.assertIn('theme[selected_bg]="#D46A43"', t)
        self.assertIn('theme[selected_fg]="#141810"', t)   # dark ink, like the Foot cursor
        self.assertIn('theme[cpu_end]="#C88C8B"', t)       # load ends in terminal red
        self.assertNotIn('C88C8B', ''.join(l for l in t.splitlines() if l.startswith(('theme[free', 'theme[download'))))
        self.assertEqual(len({l.split('=')[1] for l in t.splitlines() if '_box]' in l or 'div_line' in l}), 1)

    def test_low_contrast_is_refused(self):
        theme = copy.deepcopy(THEME)
        theme['btop']['on_selected'] = 'pure_white'   # the picker exception does not extend here
        with self.assertRaises(ValueError):
            btop.render(theme)
        theme = copy.deepcopy(THEME)
        theme['btop']['title'] = 'btop_hairline'
        with self.assertRaises(ValueError):
            btop.render(theme)

    def test_pin_matches_render(self):
        a.candidate(MANIFEST)

    def test_activate_and_rollback_keep_other_settings(self):
        with tempfile.TemporaryDirectory() as folder, patch.dict(os.environ, {'XDG_CONFIG_HOME': folder}):
            conf, theme = a.paths()
            conf.parent.mkdir()
            conf.write_text(CONF)
            self.assertEqual(a.state(MANIFEST, MANIFEST['settings']), 'original')
            a.activate(MANIFEST)
            a.activate(MANIFEST)
            self.assertEqual(a.state(MANIFEST, MANIFEST['settings']), 'active')
            text = conf.read_text()
            self.assertIn('color_theme = "limux-rhapsody"', text)
            self.assertIn('rounded_corners = false', text)
            self.assertIn('update_ms = 1500', text)
            self.assertIn('proc_sorting = "memory"', text)
            a.rollback(MANIFEST)
            self.assertEqual(conf.read_text(), CONF)
            self.assertFalse(theme.exists())

    def test_missing_config_starts_from_btop_defaults(self):
        with tempfile.TemporaryDirectory() as folder, patch.dict(os.environ, {'XDG_CONFIG_HOME': folder}), \
                patch.object(a.subprocess, 'run', return_value=type('R', (), {'stdout': CONF})()):
            a.activate(MANIFEST)
            self.assertEqual(a.state(MANIFEST, MANIFEST['settings']), 'active')

    def test_hand_chosen_theme_is_refused(self):
        with tempfile.TemporaryDirectory() as folder, patch.dict(os.environ, {'XDG_CONFIG_HOME': folder}):
            conf, _ = a.paths()
            conf.parent.mkdir()
            conf.write_text(CONF.replace('"Default"', '"nord"'))
            with self.assertRaisesRegex(RuntimeError, 'by hand'):
                a.activate(MANIFEST)
            self.assertIn('"nord"', conf.read_text())

    def test_refuses_while_btop_runs(self):
        with patch.object(a, 'btop_running', return_value=True), patch('sys.argv', ['x', 'activate']):
            with self.assertRaisesRegex(RuntimeError, 'close every btop'):
                a.main()


if __name__ == '__main__':
    unittest.main()
