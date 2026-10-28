#!/usr/bin/env python3
"""Separate Foot window, native visual overrides, no live writes or activation."""
import argparse
import os
from pathlib import Path
import subprocess
import sys
import time
import tomllib
from foot import overrides, palette, render

ROOT = Path(__file__).resolve().parents[1]


def sample(theme):
    """An interactive specimen, not a shell or an actual Codex session."""
    c, f = palette(theme), theme['foot']
    def rgb(name, background=False):
        value = c[name]
        return '\x1b[' + ('48' if background else '38') + ';2;' + ';'.join(str(int(value[i:i+2], 16)) for i in (1, 3, 5)) + 'm'
    reset = '\x1b[0m'
    print('Terminal appearance review')
    print(rgb(f['secondary']) + 'Illustrative transcript below; commands and results are fictional.' + reset)
    print('\n$ git diff --stat\n scripts/adapter.py | 8 ++++++--')
    print('\n> Refine the adapter while preserving keyboard behaviour.\n')
    print('  Read the shared tokens and retained the functional configuration.')
    print('\x1b[32m  + map semantic roles through the shared palette' + reset)
    print('\x1b[31m  - remove an independent colour literal' + reset)
    print('\x1b[33m  Review pending: text, cursor and selection at display scale.' + reset)
    print('\nANSI foregrounds  (black shown on light ground for legibility)')
    names = ['black', 'red', 'green', 'yellow', 'blue', 'magenta', 'cyan', 'white']
    for offset in (30, 90):
        for i, name in enumerate(names):
            ground = rgb('canvas', True) if offset == 30 and i == 0 else ''
            print(f'{ground}\x1b[{offset+i}m{name:9}{reset}', end='')
        print()
    print('\n' + rgb(f['secondary']) + 'Secondary text: 0123456789  Il1 O0  [] {} ()  -> != <=  /path/file.py' + reset)
    print(rgb(f['selection_background'], True) + rgb(f['selection_foreground']) + ' Selection colour sample — also drag to select real text ' + reset)
    print('\nDrag-select this sentence. Copy/paste using Command+C/V and Ctrl+Shift+C/V.')
    print('Type wait to test Ctrl+C, ansi to redraw, or exit to close. Other input is echoed.')
    print('No input is executed as a command. The cursor below is the real Foot cursor.\n')
    while True:
        try:
            value = input('preview> ')
            if value == 'exit':
                return
            if value == 'ansi':
                return sample(theme)
            if value == 'wait':
                print('Waiting 10 seconds; Ctrl+C should interrupt…', flush=True)
                time.sleep(10)
            else:
                # repr prevents pasted terminal control characters being interpreted.
                print('Received:', repr(value))
        except KeyboardInterrupt:
            print('\nCtrl+C interrupted the sample; it was not treated as Copy.')
        except EOFError:
            return


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='native validation only; no window')
    parser.add_argument('--font', choices=['DejaVu Sans Mono', 'IBM Plex Mono'], help='preview-only family comparison at the same 16pt size; requires installed font')
    parser.add_argument('--shell', action='store_true', help='open normal configured shell instead of specimen')
    parser.add_argument('--capture', action='store_true', help='capture the actual desktop after two seconds (may contain private windows)')
    parser.add_argument('--sample', action='store_true', help=argparse.SUPPRESS)
    args = parser.parse_args()
    theme = tomllib.loads((ROOT/'themes/rhapsody.toml').read_text())
    if args.font:
        theme['foot']['font'] = args.font
    if args.sample:
        sample(theme)
        return
    config = Path(os.environ.get('XDG_CONFIG_HOME', str(Path.home()/'.config')))/'foot/foot.ini'
    original = config.read_bytes()  # Fail before launch if expected functional config is absent.
    family = subprocess.check_output(['fc-match', '-f', '%{family}', theme['foot']['font']], text=True)
    if theme['foot']['font'] not in family.split(','):
        raise RuntimeError(f'Required preview font is unavailable (resolved to {family}); no silent fallback')
    out = ROOT/'build/foot-candidate1'
    out.mkdir(parents=True, exist_ok=True)
    appearance = out/'foot.ini'
    appearance.write_text(render(theme))
    command = ['foot', '-c', str(config), *overrides(theme)]
    subprocess.run(['foot', '-C', '-c', str(appearance)], check=True)
    subprocess.run([*command, '-C'], check=True)
    print('Native Foot validation passed; existing behaviour config retained.', flush=True)
    if args.check:
        return
    child = None
    try:
        invocation = [*command, '-T', 'Foot — Rhapsody candidate']
        # Do not override app-id, sizing, shell, TERM, bindings or window rules.
        if not args.shell:
            invocation += [sys.executable, str(Path(__file__).resolve()), '--sample']
        child = subprocess.Popen(invocation)
        if args.capture:
            time.sleep(2)
            if child.poll() is None:
                subprocess.run(['grim', str(out/'candidate.png')], check=True)
                print(f'Actual desktop screenshot: {out}/candidate.png', flush=True)
        status = child.wait()
        if status:
            raise RuntimeError(f'Foot exited with status {status}. Run this command from Foot in the desktop session.')
    finally:
        if child is not None and child.poll() is None:
            child.terminate()
            try:
                child.wait(timeout=5)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait()
        if config.read_bytes() != original:
            raise RuntimeError('Live Foot config changed externally during preview; no restoration attempted')


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('\nPreview closed; existing terminals untouched.')
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
        raise SystemExit(str(exc))
