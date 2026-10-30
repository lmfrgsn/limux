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
        specs = THEME['mangobar_candidate']
        css_by_variant = {name: render_quiet(THEME, name) for name in ('A', 'B', 'C')}
        self.assertIn('background: #AD492F; border-radius: 2px', css_by_variant['A'])
        self.assertIn('background: #AD492F; border-radius: 3px', css_by_variant['B'])
        self.assertIn('background: #A55A43; border-radius: 3px', css_by_variant['C'])
        for name, css in css_by_variant.items():
            accent = specs[specs[name]['active_color']]
            self.assertGreaterEqual(contrast(accent, THEME['colors']['surface']), 4.5)
            self.assertIn(f'#tags.active {{ color: {THEME["colors"]["surface"]}; background: {accent}', css)
            self.assertNotIn('min-width', css)
            self.assertNotIn('#tags:hover', css)
            self.assertNotIn('gradient', css)
            self.assertIn('#tags.active', css)
            self.assertIn('#tags.urgent', css)
            self.assertNotIn('#layout {', css)

    def test_preview_config_changes_only_left_modules_height_and_title_limit(self):
        original = json.loads(quiet.LIVE.read_text())
        for name in ('A', 'B', 'C'):
            with self.subTest(name=name):
                candidate = quiet.candidate_config(name, THEME)
                expected = json.loads(json.dumps(original))
                expected['modules-left'] = ['workspaces', 'window']
                expected['height'] = THEME['mangobar_candidate'][name]['bar_height']
                expected['window']['max-length'] = 240
                self.assertEqual(candidate, expected)

    def test_native_hover_keeps_geometry(self):
        if not SOURCE.exists():
            self.skipTest('retained Mangobar source not available')
        harness = r'''
#include "style.h"
#include <assert.h>
#include <stdlib.h>
int main(int argc, char **argv) {
  StyleSheet ss;
  style_sheet_init(&ss);
  assert(style_sheet_load(&ss, argv[1]) == 0);
  Style base = style_resolve(&ss, "tags", "active");
  Style hover = style_resolve(&ss, "tags", "hover");
  assert(base.background_set && base.color_set);
  assert(base.radius_set && base.radius == atoi(argv[2]));
  assert(!hover.min_width_set);
  assert(!hover.color_set && !hover.background_set);
  assert(base.padding_left == hover.padding_left);
  assert(base.padding_right == hover.padding_right);
  assert(base.margin_left == hover.margin_left);
  assert(base.margin_right == hover.margin_right);
  Style combined = style_overlay(&base, &hover);
  assert(combined.color == base.color && combined.background == base.background);
  const char *states[] = {"empty", "inactive", "occupied", "active", "urgent"};
  for (int i = 0; i < 5; ++i) {
    Style state = style_resolve(&ss, "tags", states[i]);
    assert(!state.min_width_set);
    assert(state.padding_left == base.padding_left);
    assert(state.padding_right == base.padding_right);
    assert(state.margin_left == base.margin_left);
    assert(state.margin_right == base.margin_right);
  }
  return 0;
}
'''
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            (path / 'check.c').write_text(harness)
            subprocess.run(['cc', '-I', str(SOURCE), str(path / 'check.c'),
                            str(SOURCE / 'style.c'), '-o', str(path / 'check')], check=True)
            for variant in ('A', 'B', 'C'):
                css = path / f'{variant}.css'
                css.write_text(render_quiet(THEME, variant))
                subprocess.run([str(path / 'check'), str(css),
                                str(THEME['mangobar_candidate'][variant]['active_radius'])], check=True)
