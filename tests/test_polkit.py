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

    def test_process_name_is_the_kernel_truncation(self):
        self.assertEqual(p.NAME, Path(p.AGENT).name[:15])


if __name__ == '__main__':
    unittest.main()
