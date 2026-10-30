#!/usr/bin/env python3
"""Validate a Limux theme or render an isolated token preview."""
import argparse
import json
from pathlib import Path
import re
import tomllib
from mangobar import render as render_mangobar
from rofi import render as render_rofi
from mango import render as render_mango
from foot import render as render_foot
from gtk import render as render_gtk
from mako import render as render_mako

parser = argparse.ArgumentParser()
parser.add_argument('action', choices=['validate', 'render'])
parser.add_argument('theme', type=Path)
parser.add_argument('--output', type=Path)
args = parser.parse_args()
try:
    theme = tomllib.loads(args.theme.read_text())
    assert isinstance(theme['name'], str) and theme['name']
    for name in ('canvas', 'surface', 'chrome', 'accent', 'text', 'dark_terminal'):
        assert re.fullmatch(r'#[0-9a-fA-F]{6}', theme['colors'][name])
    for name in ('sans', 'mono'):
        assert isinstance(theme['typography'][name], str) and theme['typography'][name]
    assert isinstance(theme['typography']['size'], int) and theme['typography']['size'] > 0
    for name in ('radius', 'spacing', 'border'):
        assert isinstance(theme['geometry'][name], int) and theme['geometry'][name] >= 0
    css = render_mangobar(theme)  # Validate the complete adapter contract for both actions.
    rasi = render_rofi(theme)
    mango = render_mango(theme)
    foot = render_foot(theme)
    gtk = render_gtk(theme)
    mako = render_mako(theme)
    if args.action == 'render':
        if args.output is None:
            parser.error('render requires --output')
        args.output.mkdir(parents=True, exist_ok=True)
        (args.output / 'tokens.json').write_text(json.dumps(theme, indent=2) + '\n')
        (args.output / 'mangobar.css').write_text(css)
        (args.output / 'rofi.rasi').write_text(rasi)
        (args.output / 'mango.conf').write_text(mango)
        (args.output / 'foot.ini').write_text(foot)
        (args.output / 'gtk.css').write_text(gtk)
        (args.output / 'mako').write_text(mako)
    print(f"Validated {theme['name']}" + ('; preview written' if args.action == 'render' else ''))
except (OSError, KeyError, ValueError, TypeError, AssertionError) as e:
    parser.exit(1, f'Invalid theme: {e}\n')
