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
from mangobar import render

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
        self.assertIn(self.theme['colors']['accent'], css)
        self.assertIn('#tags.active', css)
        self.assertIn('#custom-wifi', css)
        properties = re.findall(r'(?:\{|;)\s*([a-z-]+)\s*:', css)
        self.assertLessEqual(set(properties), {'font-family','font-size','font-weight','color','background','background-color','padding','margin','border-radius','min-width','border-color'})
        self.assertNotIn('border-width:', css)

    def test_deterministic_and_theme_independent(self):
        self.assertEqual(render(self.theme), render(copy.deepcopy(self.theme)))
        t = copy.deepcopy(self.theme)
        t['colors']['accent'] = '#123456'
        self.assertIn('#123456', render(t))
        self.assertNotEqual(render(t), render(self.theme))

    def test_cli_rejects_invalid_theme(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'bad.toml'
            p.write_text('name = "bad"\n')
            r = subprocess.run([sys.executable, str(ROOT / 'scripts/theme.py'), 'validate', str(p)], capture_output=True)
            self.assertNotEqual(r.returncode, 0)

if __name__ == '__main__': unittest.main()
