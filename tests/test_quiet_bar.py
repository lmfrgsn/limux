import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import tomllib
import unittest
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from mangobar import contrast, render_quiet

spec = importlib.util.spec_from_file_location('quiet_bar', ROOT / 'scripts/quiet-bar.py')
quiet = importlib.util.module_from_spec(spec)
spec.loader.exec_module(quiet)
THEME = tomllib.loads((ROOT / 'themes/rhapsody.toml').read_text())
SOURCE = Path('/home/liam/.local/state/limux/bar-migration/sources/mangobar')

class QuietBarTest(unittest.TestCase):
    def test_variants_and_contrast(self):
        warm = render_quiet(THEME, 'vermillion')
        neutral = render_quiet(THEME, 'neutral')
        self.assertIn('#AD492F', warm)
        self.assertNotIn('#AD492F', neutral)
        self.assertIn('#tags.active { color: #343442; background: #EAE9F0; }', neutral)
        self.assertGreaterEqual(contrast('#AD492F', THEME['colors']['surface']), 4.5)
        for css in (warm, neutral):
            self.assertNotIn('min-width', css)
            self.assertNotIn('#tags:hover', css)
            self.assertNotIn('gradient', css)
            self.assertIn('#tags.active', css)
            self.assertIn('#tags.urgent', css)
            self.assertNotIn('#layout {', css)

    def test_preview_config_changes_only_left_modules_and_title_limit(self):
        original = json.loads(quiet.LIVE.read_text())
        candidate = quiet.candidate_config()
        self.assertEqual(candidate['modules-left'], ['workspaces', 'window'])
        self.assertEqual(candidate['window']['max-length'], 240)
        original['modules-left'] = ['workspaces', 'window']
        original['window']['max-length'] = 240
        self.assertEqual(candidate, original)

    def test_native_hover_keeps_geometry(self):
        if not SOURCE.exists():
            self.skipTest('retained Mangobar source not available')
        harness = r'''
#include "style.h"
#include <assert.h>
int main(int argc, char **argv) {
  StyleSheet ss;
  style_sheet_init(&ss);
  assert(style_sheet_load(&ss, argv[1]) == 0);
  Style base = style_resolve(&ss, "tags", "active");
  Style hover = style_resolve(&ss, "tags", "hover");
  assert(!hover.min_width_set);
  assert(!hover.color_set && !hover.background_set);
  assert(base.padding_left == hover.padding_left);
  assert(base.padding_right == hover.padding_right);
  assert(base.margin_left == hover.margin_left);
  assert(base.margin_right == hover.margin_right);
  Style combined = style_overlay(&base, &hover);
  assert(combined.color == base.color && combined.background == base.background);
  return 0;
}
'''
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            (path / 'check.c').write_text(harness)
            subprocess.run(['cc', '-I', str(SOURCE), str(path / 'check.c'),
                            str(SOURCE / 'style.c'), '-o', str(path / 'check')], check=True)
            for variant in ('vermillion', 'neutral'):
                css = path / f'{variant}.css'
                css.write_text(render_quiet(THEME, variant))
                subprocess.run([str(path / 'check'), str(css)], check=True)
