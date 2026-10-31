import copy
import importlib.util
from pathlib import Path
import sys
import tomllib
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
from lock import render  # noqa: E402

spec = importlib.util.spec_from_file_location('lock_activation', ROOT/'scripts/activate-lock.py')
a = importlib.util.module_from_spec(spec)
spec.loader.exec_module(a)
THEME = tomllib.loads((ROOT/'themes/rhapsody.toml').read_text())


class LockTests(unittest.TestCase):
    def test_appearance_follows_tokens(self):
        conf = render(THEME)
        self.assertIn('color = rgb(DADAE3)', conf)          # desktop canvas ground
        self.assertIn('outer_color = rgb(D46A43)', conf)    # orange field edge
        self.assertIn('fail_color = rgb(AD4038)', conf)
        self.assertIn('capslock_color = -1', conf)          # caps lock is a label, not an edge colour
        self.assertIn('size = 280, 40', conf)
        self.assertIn('dots_spacing = 0.88', conf)
        self.assertIn('animation = fadeOut, 1, 2, limux', conf)
        # hyprlang treats a lone '#' as a comment; colours inside markup must be '##'.
        for line in conf.splitlines():
            if not line.lstrip().startswith('#'):
                self.assertNotRegex(line.replace('##', ''), '#')
        for forbidden in ('general {', 'auth {', 'pam', 'grace', 'source ='):
            self.assertNotIn(forbidden, conf)               # behaviour stays hand-maintained

    def test_low_contrast_and_bad_geometry_are_refused(self):
        for section, key, value in (('lock', 'date', 'text_secondary'), ('lock', 'field_width', 5),
                                    ('lock', 'placeholder', 'metal')):
            theme = copy.deepcopy(THEME)
            theme[section][key] = value
            with self.assertRaises(ValueError):
                render(theme)

    def test_mango_lines_are_added_once_and_removed_exactly(self):
        base = ('exec_once=/a\nexec_once=/b\n# keys\n' + a.LAUNCHER + '\nbind=SUPER,k,spawn,x\n')
        added = a.with_lines(base)
        self.assertEqual(added.count(a.AUTOSTART), 1)
        self.assertEqual(added.count(a.BINDING), 1)
        self.assertLess(added.index('exec_once=/b'), added.index(a.AUTOSTART))
        self.assertEqual(a.mango_lines(added), (True, True))
        self.assertEqual(a.without_lines(added), base)
        self.assertEqual(a.mango_lines(base), (False, False))
        with self.assertRaises(RuntimeError):
            a.mango_lines(base + 'bind=SUPER+CTRL,q,killclient,\n')

    def test_pins_match_sources(self):
        import json
        a.candidate(json.loads(a.MANIFEST.read_text()))


if __name__ == '__main__':
    unittest.main()
