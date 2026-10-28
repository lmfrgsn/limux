"""Optional integration test against the actual Mangobar C parser.

MANGOBAR_SOURCE=/path/to/mangobar python3 -m unittest discover -s tests -v
No source is downloaded or vendored; compilation stays in a temporary directory.
"""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
import tomllib
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from mangobar import render

SOURCE = os.environ.get('MANGOBAR_SOURCE')

@unittest.skipUnless(SOURCE, 'Set MANGOBAR_SOURCE to test the native parser')
class NativeStyleTests(unittest.TestCase):
    def test_resolved_states_and_hover(self):
        root = Path(__file__).resolve().parents[1]
        theme = tomllib.loads((root / 'themes/rhapsody.toml').read_text())
        c, sem = theme['colors'], theme['semantics']
        argb = lambda name: '0x' + c[sem[name]][1:] + 'ffu'
        harness = r'''
#include "style.h"
#include <assert.h>
int main(int argc, char **argv) {
    StyleSheet ss;
    style_sheet_init(&ss);
    assert(style_sheet_load(&ss, argv[1]) == 0);
    Style active = style_resolve(&ss, "tags", "active");
    Style urgent = style_resolve(&ss, "tags", "urgent");
    Style hover = style_resolve(&ss, "tags", "hover");
    assert(!hover.background_set && !hover.color_set);
    active = style_overlay(&active, &hover);
    urgent = style_overlay(&urgent, &hover);
    assert(active.background == SELECTED && active.color == ON_SELECTED);
    assert(urgent.background == URGENT && urgent.color == ON_URGENT);
    assert(active.radius == 0 && active.min_width == 26);
    assert(ss.menu.border_color_set);
    return 0;
}
'''
        for key in ('on_selected', 'selected', 'on_urgent', 'urgent'):
            harness = harness.replace(key.upper(), argb(key))
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            (d/'check.c').write_text(harness)
            (d/'candidate.css').write_text(render(theme))
            subprocess.run(['cc', '-I', SOURCE, str(d/'check.c'), str(Path(SOURCE)/'style.c'), '-o', str(d/'check')], check=True)
            subprocess.run([str(d/'check'), str(d/'candidate.css')], check=True)
