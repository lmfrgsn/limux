import copy
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import tomllib
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
from imv import render  # noqa: E402

spec = importlib.util.spec_from_file_location('imv_activation', ROOT/'scripts/activate-imv.py')
a = importlib.util.module_from_spec(spec)
spec.loader.exec_module(a)
THEME = tomllib.loads((ROOT/'themes/rhapsody.toml').read_text())


class ImvTests(unittest.TestCase):
    def test_appearance_only_from_tokens(self):
        conf = render(THEME)
        self.assertIn('background = 2F303B', conf)
        self.assertIn('overlay_font = Inter:11', conf)
        self.assertIn('overlay = false', conf)
        self.assertNotIn('[binds]', conf)       # imv's default keys stay
        self.assertIn(' · ', conf)              # separators survive imv's shell expansion

    def test_low_contrast_is_refused(self):
        theme = copy.deepcopy(THEME)
        theme['imv']['overlay_text'] = 'accent'
        with self.assertRaises(ValueError):
            render(theme)

    def test_defaults_are_added_and_removed_without_touching_others(self):
        with tempfile.TemporaryDirectory() as folder:
            mime = Path(folder)/'mimeapps.list'
            mime.write_text('[Default Applications]\ntext/html=firefox.desktop\n')
            with patch.object(a, 'MIMEAPPS', mime):
                self.assertEqual(a.defaults_state(), 'original')
                parser = a.read_mimeapps()
                for t in a.TYPES:
                    parser.set(a.SECTION, t, a.DESKTOP)
                a.write_mimeapps(parser)
                self.assertEqual(a.defaults_state(), 'active')
                self.assertIn('text/html=firefox.desktop', mime.read_text())
                mime.write_text(mime.read_text().replace('image/png=imv.desktop', 'image/png=gimp.desktop'))
                with self.assertRaises(RuntimeError):
                    a.defaults_state()

    def test_pin_matches_render(self):
        a.candidate(json.loads(a.MANIFEST.read_text()))


if __name__ == '__main__':
    unittest.main()
