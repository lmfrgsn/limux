import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('portals_activation', ROOT/'scripts/activate-portals.py')
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)
CHOOSER = ROOT/'machine/home/.local/bin/limux-screen-chooser'


class PortalTests(unittest.TestCase):
    def test_pins_match_sources(self):
        p.candidate(json.loads(p.MANIFEST.read_text()))

    def test_only_the_limux_rule_is_accepted(self):
        self.assertFalse(p.has_rule('tag_rule=id:1\n'))
        self.assertTrue(p.has_rule(f'{p.RULE}\n'))
        with self.assertRaises(RuntimeError):
            p.has_rule('window_rule=is_floating:0,app_id:xdg-desktop-portal-gtk\n')

    def test_chooser_names_displays_and_returns_the_portal_line(self):
        source = CHOOSER.read_text()
        namespace = {}
        exec(source.split('\n\n\nlines =')[0], namespace)  # label() only; no Rofi
        self.assertEqual(namespace['label']('Monitor: eDP-1'), ('Built-in display', 'Screen'))
        self.assertEqual(namespace['label']('Monitor: HDMI-A-1'), ('Display HDMI-A-1', 'Screen'))
        self.assertEqual(namespace['label']('Monitor: DP-2 Dell Inc. DELL U2720Q'), ('Dell Inc. DELL U2720Q', 'Screen'))
        self.assertEqual(namespace['label']('eDP-1'), ('Built-in display', 'Screen'))
        self.assertEqual(namespace['label']('Monitor: eDP-1 Apple Computer Inc Color LCD'), ('Built-in display', 'Screen'))
        self.assertEqual(namespace['label']('Window: gUM Test Page — Mozilla Firefox (b97954d6786c229ba94f00dd88669112)'),
                         ('gUM Test Page — Mozilla Firefox', 'Window'))

    def test_chooser_cancels_on_empty_input(self):
        result = subprocess.run([sys.executable, str(CHOOSER)], input='', capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, '')


if __name__ == '__main__':
    unittest.main()
