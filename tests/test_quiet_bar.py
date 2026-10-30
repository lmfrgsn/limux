import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import tomllib
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from mangobar import contrast, render_quiet


def load_script(name, module_name):
    spec = importlib.util.spec_from_file_location(module_name, ROOT / 'scripts' / name)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


quiet = load_script('quiet-bar.py', 'quiet_bar')
builder = load_script('quiet-mangobar-build.py', 'quiet_mangobar_build')
THEME = tomllib.loads((ROOT / 'themes/rhapsody.toml').read_text())


class QuietBarTest(unittest.TestCase):
    def test_preview_duration_is_bounded_before_launch(self):
        with self.assertRaises(ValueError):
            quiet.preview(seconds=301)

    def test_one_candidate_has_unboxed_states_and_readable_active_number(self):
        css = render_quiet(THEME)
        q = THEME['mangobar_candidate']
        self.assertEqual(q['bar_height'], 30)  # B geometry retained
        self.assertEqual(q['workspace_padding'], 7)
        self.assertIn(f'background: {q["active_orange"]};', css)
        self.assertIn(f'background-inset: {q["active_inset"]}px;', css)
        self.assertIn(f'border-radius: {q["active_radius"]}px;', css)
        self.assertGreaterEqual(contrast(q['active_orange'], THEME['colors']['signal_ink']), 4.5)
        for state in ('empty', 'inactive', 'occupied', 'urgent'):
            self.assertIn(f'#tags.{state} {{', css)
            self.assertIn('background: none;', css.split(f'#tags.{state} {{', 1)[1].split('}', 1)[0])
        self.assertNotIn('min-width', css)
        self.assertNotIn('#tags:hover', css)
        self.assertNotIn('#layout {', css)

    def test_preview_config_preserves_functional_modules(self):
        original = json.loads(quiet.LIVE.read_text())
        candidate = quiet.candidate_config(THEME)
        expected = json.loads(json.dumps(original))
        expected['modules-left'] = ['workspaces', 'window']
        expected['height'] = 30
        expected['window']['max-length'] = 240
        self.assertEqual(candidate, expected)

    def test_isolated_native_css_and_hover_geometry(self):
        if not builder.SOURCE.exists():
            self.skipTest('retained Mangobar source not available')
        sources = builder.patched_sources()  # also checks exact upstream hashes
        self.assertIn('int mid_x0 = 0;', sources['mangobar.c'])
        self.assertIn('int mid_x1 = (int)bar->width;', sources['mangobar.c'])
        self.assertIn('cairo_rounded_rect(bar_bg_cr, x1, fill_y', sources['mangobar.c'])
        harness = r'''
#include "style.h"
#include <assert.h>
int main(int argc, char **argv) {
  StyleSheet ss;
  style_sheet_init(&ss);
  assert(style_sheet_load(&ss, argv[1]) == 0);
  Style active = style_resolve(&ss, "tags", "active");
  Style hover = style_resolve(&ss, "tags", "hover");
  assert(active.background_set && active.background_inset_set);
  assert(active.background_inset == 4 && active.radius == 4);
  assert(!hover.background_inset_set && !hover.min_width_set);
  assert(!hover.radius_set && !hover.color_set && !hover.background_set);
  Style combined = style_overlay(&active, &hover);
  assert(combined.background_inset == active.background_inset);
  assert(combined.background == active.background);
  assert(combined.radius == active.radius && combined.color == active.color);
  const char *states[] = {"empty", "inactive", "occupied", "urgent"};
  for (int i = 0; i < 4; ++i) {
    Style state = style_resolve(&ss, "tags", states[i]);
    assert(state.background_set && (state.background & 0xffu) == 0);
    assert(!state.background_inset_set);
    assert(!state.min_width_set);
    assert(state.padding_left == active.padding_left);
    assert(state.padding_right == active.padding_right);
    assert(state.margin_left == active.margin_left);
    assert(state.margin_right == active.margin_right);
  }
  return 0;
}
'''
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            for name in ('style.h', 'style.c'):
                (path / name).write_text(sources[name])
            (path / 'check.c').write_text(harness)
            css = path / 'revised.css'
            css.write_text(render_quiet(THEME))
            subprocess.run(['cc', '-I', str(path), str(path / 'check.c'),
                            str(path / 'style.c'), '-o', str(path / 'check')], check=True)
            subprocess.run([str(path / 'check'), str(css)], check=True)


if __name__ == '__main__':
    unittest.main()
