import configparser
import copy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import tomllib
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
from foot import overrides, palette, render, settings
from mangobar import render as bar_render
from rofi import render as rofi_render
from mango import render as mango_render


class FootTests(unittest.TestCase):
    def setUp(self):
        self.theme = tomllib.loads((ROOT/'themes/rhapsody.toml').read_text())

    def test_native_fragment_and_overrides_are_identical_and_visual_only(self):
        ini = configparser.ConfigParser()
        ini.read_string(render(self.theme))
        expected = settings(self.theme)
        self.assertEqual({s: dict(ini[s]) for s in ini.sections()}, expected)
        self.assertEqual(set(expected), {'main', 'cursor', 'colors-dark'})
        self.assertEqual(set(expected['main']), {'font', 'pad', 'initial-color-theme'})
        argv = overrides(self.theme)
        self.assertEqual(argv[::2], ['-o'] * (len(argv)//2))
        self.assertEqual(argv[1::2], [f'{s}.{k}={v}' for s, values in expected.items() for k,v in values.items()])
        self.assertNotIn('key-bindings', render(self.theme))

    def test_signal_derivation_and_contrast_rejection(self):
        old = palette(self.theme)
        t = copy.deepcopy(self.theme)
        t['colors']['signal_red'] = '#AE4139'
        self.assertNotEqual(palette(t)['terminal_red'], old['terminal_red'])
        t = copy.deepcopy(self.theme)
        t['foot']['foreground'] = 'dark_terminal'
        with self.assertRaisesRegex(ValueError, 'contrast'):
            render(t)
        t = copy.deepcopy(self.theme)
        t['foot']['selection_foreground'] = 'terminal_selection'
        with self.assertRaisesRegex(ValueError, 'contrast'):
            render(t)

    def test_reject_invalid_tokens(self):
        for key, value in [('font', 'bad\n[key-bindings]'), ('font_size', 0), ('padding', -1), ('regular', [])]:
            t = copy.deepcopy(self.theme)
            t['foot'][key] = value
            with self.assertRaises(ValueError):
                render(t)
        t = copy.deepcopy(self.theme)
        t['foot']['colors']['accent'] = '#000000'
        with self.assertRaises(ValueError):
            render(t)

    @unittest.skipUnless(shutil.which('foot'), 'native Foot unavailable')
    def test_native_validation_preserves_behavior_file(self):
        with tempfile.TemporaryDirectory() as folder:
            p = Path(folder)/'foot.ini'
            original = ('[main]\nfont=DejaVu Sans Mono:size=16\n[scrollback]\nlines=4321\n'
                        '[key-bindings]\nclipboard-copy=Super+c\nclipboard-paste=Super+v\n')
            p.write_text(original)
            result = subprocess.run(['foot', '-C', '-c', str(p), *overrides(self.theme)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(p.read_text(), original)
            # A native parser success must actually reject unknown properties.
            result = subprocess.run(['foot', '-C', '-c', str(p), '-o', 'colors-dark.invalid-color=ffffff'], capture_output=True)
            self.assertNotEqual(result.returncode, 0)

    def test_sample_never_executes_input(self):
        result = subprocess.run([sys.executable, str(ROOT/'scripts/preview-foot.py'), '--sample'],
                                input='$(false)\nexit\n', capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Received: '$(false)'", result.stdout)
        self.assertIn('commands and results are fictional', result.stdout)

    def test_approved_other_outputs_unchanged(self):
        for name, renderer in [('mangobar', bar_render), ('rofi', rofi_render), ('mango', mango_render)]:
            manifest = json.loads((ROOT/f'themes/recovery/{name}.json').read_text())
            self.assertEqual(hashlib.sha256(renderer(self.theme).encode()).hexdigest(), manifest['approved_sha256' if name == 'mango' else 'baseline_sha256'])


if __name__ == '__main__':
    unittest.main()
