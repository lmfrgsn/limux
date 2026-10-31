import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys
import tomllib
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
from gtk import ICONS, gsettings, render_css, render_icons, thunar_settings

spec = importlib.util.spec_from_file_location('activate_gtk', ROOT/'scripts/activate-gtk.py')
activation = importlib.util.module_from_spec(spec)
spec.loader.exec_module(activation)


class GtkAdapterTests(unittest.TestCase):
    def setUp(self):
        self.theme = tomllib.loads((ROOT/'themes/rhapsody.toml').read_text())

    def test_every_colour_is_a_rhapsody_token(self):
        css = render_css(self.theme)
        tokens = {value.upper() for value in self.theme['colors'].values()}
        for colour in re.findall(r'#[0-9A-Fa-f]{6}', css):
            self.assertIn(colour.upper(), tokens)
        for svg in render_icons(self.theme)[0].values():
            for colour in re.findall(rb'#[0-9A-Fa-f]{6}', svg):
                self.assertIn(colour.decode().upper(), tokens)

    def test_layout_and_font_are_scoped_to_thunar_and_file_choosers(self):
        css = render_css(self.theme)
        rules = [line for line in css.splitlines() if '{' in line and not line.startswith('@')]
        for rule in rules:
            self.assertTrue(rule.startswith(('.thunar', 'window.thunar', 'filechooser', 'dialog headerbar')), rule)
        self.assertIn('window.thunar { font-family: "Inter"; font-size: 10pt; }', css)

    def test_selection_contrast_is_enforced(self):
        t = copy.deepcopy(self.theme)
        t['thunar']['on_selected'] = 'text_quiet'
        with self.assertRaisesRegex(ValueError, 'contrast'):
            render_css(t)

    def test_icon_aliases_point_at_drawn_icons(self):
        files, links = render_icons(self.theme)
        for rel, target in links.items():
            self.assertIn(str(Path(rel).parent/target), files)
        for directory in ('16', 'scalable'):
            for base, (context, _, _) in ICONS.items():
                self.assertIn(f'{directory}/{context}/{base}.svg', files)
        names = [alias for _, _, aliases in ICONS.values() for alias in aliases]
        self.assertEqual(len(names), len(set(names)))
        self.assertIn(b'Inherits=Adwaita,hicolor', files['index.theme'])

    def test_thunar_settings_are_presentation_only(self):
        names = set(thunar_settings(self.theme))
        self.assertFalse({n for n in names if 'accel' in n or 'shortcut-' in n or 'misc-single-click' in n})
        self.assertEqual(gsettings(self.theme), {'font-name': 'Inter 10', 'icon-theme': 'Limux-Rhapsody',
                                                 'gtk-theme': 'adw-gtk3'})
        self.assertEqual(list(gsettings(self.theme))[-1], 'gtk-theme')

    def test_generated_output_matches_approval_pin(self):
        manifest = json.loads((ROOT/'themes/recovery/gtk.json').read_text())
        self.assertEqual(hashlib.sha256(render_css(self.theme).encode()).hexdigest(), manifest['css_sha256'])
        self.assertEqual(activation.tree_digest(*render_icons(self.theme)), manifest['icons_sha256'])
        activation.candidate(manifest)


if __name__ == '__main__':
    unittest.main()
