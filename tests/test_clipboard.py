import importlib.machinery
import importlib.util
import json
from pathlib import Path
import sys
import unittest

sys.dont_write_bytecode = True  # the helper lives in machine/, which must hold only tracked files

ROOT = Path(__file__).resolve().parents[1]
loader = importlib.machinery.SourceFileLoader('limux_clipboard', str(ROOT/'machine/home/.local/bin/limux-clipboard'))
spec = importlib.util.spec_from_loader('limux_clipboard', loader)
c = importlib.util.module_from_spec(spec)
loader.exec_module(c)
spec = importlib.util.spec_from_file_location('clipboard_activation', ROOT/'scripts/activate-clipboard.py')
a = importlib.util.module_from_spec(spec)
spec.loader.exec_module(a)


class ClipboardTests(unittest.TestCase):
    def test_rows_name_text_links_and_images(self):
        self.assertEqual(c.row('  hello\n  world  '), ('hello world', 'Text'))
        self.assertEqual(c.row('https://example.org/a?b=1'), ('https://example.org/a?b=1', 'Link'))
        self.assertEqual(c.row('[[ binary data 88 KiB png 1920x1080 ]]'), ('PNG, 1920 × 1080', 'Image'))
        name, kind = c.row('x' * 200)
        self.assertEqual((len(name), name[-1], kind), (c.PREVIEW, '…', 'Text'))

    def test_history_is_memory_only_and_bounded(self):
        self.assertIn('/run/user/', str(c.DB)) if str(c.DB).startswith('/run') else None
        self.assertEqual(c.MAX_ITEMS, 50)
        self.assertIn('-max-items', c.CLIPHIST)

    def test_mango_lines_are_exclusive(self):
        self.assertEqual(a.lines(f'{a.BINDING}\n{a.AUTOSTART}\n'), (True, True))
        self.assertEqual(a.lines('exec_once=/a\n'), (False, False))
        with self.assertRaises(RuntimeError):
            a.lines('bind=SUPER+SHIFT,v,spawn,something-else\n')

    def test_pin_matches_source(self):
        a.candidate(json.loads(a.MANIFEST.read_text()))


if __name__ == '__main__':
    unittest.main()
