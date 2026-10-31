import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('polkit_activation', ROOT/'scripts/activate-polkit.py')
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)


class PolkitTests(unittest.TestCase):
    def test_only_the_limux_autostart_is_accepted(self):
        self.assertFalse(p.configured('exec_once=/a\n'))
        self.assertTrue(p.configured(f'exec_once=/a\n{p.AUTOSTART}\n'))
        self.assertFalse(p.configured(f'# {p.AUTOSTART}\n'))
        with self.assertRaises(RuntimeError):
            p.configured('exec_once=/usr/lib/mate-polkit/polkit-mate-authentication-agent-1\n')

    def test_the_previous_plain_autostart_is_upgradeable(self):
        self.assertFalse(p.configured(f'{p.PREVIOUS[0]}\n'))  # recognised, not yet themed
        self.assertIn('GTK_THEME=Limux-Dialog', p.AUTOSTART)

    def test_prompt_theme_matches_its_pin(self):
        files = p.theme_files()
        css = next(data for path, data in files.items() if path.name == 'gtk.css').decode()
        self.assertIn('@import url("/usr/share/themes/adw-gtk3/gtk-3.0/gtk.css");', css)
        self.assertIn('caret-color: #D46A43', css)
        self.assertNotIn('focus-within', css)  # not GTK 3 syntax; it would void the rule

    def test_process_name_is_the_kernel_truncation(self):
        self.assertEqual(p.NAME, Path(p.AGENT).name[:15])


if __name__ == '__main__':
    unittest.main()
