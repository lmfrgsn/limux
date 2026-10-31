import importlib.util
import json
from pathlib import Path
import shutil
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
# The Quiet Strip's own config: while bar status is active, its activation keeps
# that input in its state folder and the live file is the layered result.
BAR_STATUS_INPUT = Path.home() / '.local/state/limux/bar-status-activation/config'
QUIET_INPUT = BAR_STATUS_INPUT if BAR_STATUS_INPUT.exists() else quiet.LIVE


class QuietBarTest(unittest.TestCase):
    def test_preview_duration_is_bounded_before_launch(self):
        with self.assertRaises(ValueError):
            quiet.preview(seconds=301)

    def test_one_candidate_preserves_orange_geometry_with_approved_white_ink_exception(self):
        css = render_quiet(THEME)
        q = THEME['mangobar_candidate']
        self.assertEqual(q['bar_height'], 30)  # B geometry retained
        self.assertEqual(q['workspace_padding'], 7)
        accent = THEME['colors'][THEME['semantics']['workspace_active']]
        self.assertIn(f'background: {accent};', css)
        self.assertIn(f'background-inset: {q["active_inset"]}px;', css)
        self.assertIn(f'border-radius: {q["active_radius"]}px;', css)
        ink = THEME['colors'][THEME['semantics']['on_workspace_active']]
        self.assertEqual(ink, '#FFFFFF')
        self.assertEqual(THEME['semantics']['on_workspace_active'], 'pure_white')
        self.assertEqual(THEME['semantics']['on_terminal_cursor'], 'signal_ink')
        self.assertAlmostEqual(contrast(accent, ink), 3.53, places=2)
        self.assertEqual(q['active_text_contrast_exception'], 'approved-white-on-orange')
        self.assertIn('margin-left: 8px;', css)
        self.assertIn(f'margin: 0px {q["workspace_gap"]}px;', css)
        self.assertIn(f'background: {accent};', css)
        for state in ('empty', 'inactive', 'occupied', 'urgent'):
            self.assertIn(f'#tags.{state} {{', css)
            self.assertIn('background: none;', css.split(f'#tags.{state} {{', 1)[1].split('}', 1)[0])
        self.assertNotIn('min-width', css)
        self.assertNotIn('#tags:hover', css)
        self.assertNotIn('#layout {', css)

    def test_white_contrast_exception_is_scoped_and_general_validation_stays_strict(self):
        import copy
        from mangobar import render
        changed = copy.deepcopy(THEME)
        changed['semantics']['on_selected'] = 'pure_white'
        with self.assertRaisesRegex(ValueError, 'selected text contrast'):
            render(changed)
        changed = copy.deepcopy(THEME)
        changed['colors']['pure_white'] = '#FDFDFD'
        with self.assertRaisesRegex(ValueError, 'unapproved active workspace contrast exception'):
            render_quiet(changed)

    def test_preview_config_preserves_functional_modules(self):
        original = json.loads(QUIET_INPUT.read_text())
        # The active Quiet Strip has already hidden the layout indicator.
        with tempfile.TemporaryDirectory() as d:
            source = Path(d) / 'active.jsonc'
            source.write_text(json.dumps(original))
            candidate = quiet.candidate_config(THEME, source)
        self.assertEqual(candidate['modules-left'], ['workspaces', 'window'])
        self.assertEqual(candidate['height'], 30)
        self.assertEqual(candidate['window']['max-length'], 240)
        battery = candidate['battery']
        self.assertEqual(battery['device'], 'BAT0')
        self.assertEqual(battery['format'], 'Bat {percent}%{icon}')
        self.assertEqual(battery['icon-charging'], ' chg')
        self.assertEqual(battery['icon-full'], '')
        self.assertEqual(battery['icons'], [''] * 11)
        self.assertFalse(battery['hide-on-ac'])

    def test_generated_battery_config_parses_with_pinned_native_parser(self):
        if not builder.SOURCE.exists():
            self.skipTest('retained Mangobar source not available')
        sources = builder.patched_sources()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            source = path / 'rtconfig.c'
            header = path / 'rtconfig.h'
            source.write_text(sources['rtconfig.c'])
            header.write_text(sources['rtconfig.h'])
            config = path / 'candidate.jsonc'
            config.write_text(json.dumps(quiet.candidate_config(THEME, QUIET_INPUT)))
            harness = path / 'check.c'
            harness.write_text(r'''
#include "rtconfig.h"
#include <assert.h>
#include <string.h>
int main(int argc, char **argv) {
  assert(argc == 2 && mango_config_load(argv[1]) == 0);
  assert(g_cfg.battery_count == 1);
  MangoBatteryCfg *b = &g_cfg.batteries[0];
  assert(strcmp(b->device, "BAT0") == 0);
  assert(strcmp(b->fmt, "Bat {percent}%{icon}") == 0);
  assert(strcmp(b->icon_charging, " chg") == 0);
  assert(strcmp(b->icon_full, "") == 0);
  assert(b->icon_count == 11);
  for (int i = 0; i < b->icon_count; i++) assert(strcmp(b->icons[i], "") == 0);
  return 0;
}
''')
            executable = path / 'check'
            subprocess.run(['cc', '-I', str(path), '-I/usr/include/cjson',
                            str(harness), str(source), '-lcjson', '-o', str(executable)],
                           check=True)
            subprocess.run([str(executable), str(config)], check=True)

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
  assert(active.margin_left == 8 && active.margin_right == 1);
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
