import copy
import re
import subprocess
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from mangobar import render, contrast

class ThemeTests(unittest.TestCase):
    def setUp(self):
        self.theme = tomllib.loads((ROOT / 'themes/rhapsody.toml').read_text())

    def test_invalid_color_and_font(self):
        for section, key, bad in [('colors', 'accent', 'red'), ('typography', 'sans', 'bad; font')]:
            t = copy.deepcopy(self.theme)
            t[section][key] = bad
            with self.assertRaises(ValueError):
                render(t)

    def test_css_supported_and_uses_tokens(self):
        css = render(self.theme)
        self.assertIn(self.theme['colors']['signal_yellow'], css)
        self.assertIn('#tags.active', css)
        self.assertIn('#custom-wifi', css)
        properties = re.findall(r'(?:\{|;)\s*([a-z-]+)\s*:', css)
        self.assertLessEqual(set(properties), {'font-family','font-size','font-weight','color','background','background-color','padding','margin','border-radius','min-width','border-color'})
        self.assertNotIn('border-width:', css)

    def test_deterministic_and_theme_independent(self):
        self.assertEqual(render(self.theme), render(copy.deepcopy(self.theme)))
        t = copy.deepcopy(self.theme)
        t['colors']['signal_yellow'] = '#E8C64E'
        self.assertIn('#E8C64E', render(t))
        self.assertNotEqual(render(t), render(self.theme))

    def test_semantic_contrast_and_foundations(self):
        c = self.theme['colors']
        for key, value in dict(canvas='#DADAE3', surface='#F8F8FA', chrome='#EAE9F0',
                               accent='#77768F', text='#343442', dark_terminal='#2F303B').items():
            self.assertEqual(c[key], value)
        for state in ('selected', 'success', 'urgent'):
            semantic = self.theme['semantics']
            self.assertGreaterEqual(contrast(c[semantic[state]], c[semantic['on_' + state]]), 4.5)
        t = copy.deepcopy(self.theme)
        t['semantics']['on_selected'] = 'surface'
        with self.assertRaisesRegex(ValueError, 'contrast'):
            render(t)

    def test_hover_cannot_override_state_colours(self):
        css = render(self.theme)
        for selector in ('*', '#tags', '#tags:hover'):
            block = re.search(re.escape(selector) + r' \{([^}]+)', css).group(1)
            self.assertNotRegex(block, r'(?:color|background)\s*:')
        # Emphasis changes must not recolour selected workspaces.
        t = copy.deepcopy(self.theme)
        t['colors']['accent'] = '#123456'
        self.assertEqual(render(t), css)

    def test_cli_validate_rejects_bad_semantic_colour(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'bad.toml'
            p.write_text((ROOT / 'themes/rhapsody.toml').read_text().replace('#E3BE47', '#343442'))
            r = subprocess.run([sys.executable, str(ROOT / 'scripts/theme.py'), 'validate', str(p)], capture_output=True)
            self.assertNotEqual(r.returncode, 0)

    def test_cli_rejects_invalid_theme(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'bad.toml'
            p.write_text('name = "bad"\n')
            r = subprocess.run([sys.executable, str(ROOT / 'scripts/theme.py'), 'validate', str(p)], capture_output=True)
            self.assertNotEqual(r.returncode, 0)

if __name__ == '__main__': unittest.main()
