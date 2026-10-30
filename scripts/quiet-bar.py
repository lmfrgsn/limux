#!/usr/bin/env python3
"""Render and briefly preview the unapproved inset Quiet Workspace Strip."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import time
import tomllib
from mangobar import render_quiet

ROOT = Path(__file__).resolve().parents[1]
LIVE = Path.home() / '.config/mangobar/config.jsonc'
OUT = ROOT / 'build/quiet-workspace-strip'
BAR = OUT / 'mangobar-build/mangobar'


def candidate_config(theme, path=LIVE):
    # Current live JSONC is strict JSON. Refuse unfamiliar syntax rather than
    # risk dropping a commented setting while generating an isolated preview.
    data = json.loads(path.read_text())
    left = data['modules-left']
    if left != ['workspaces', 'layout', 'window']:
        raise ValueError('unexpected left modules; inspect before changing the preview')
    candidate = theme['mangobar_candidate']
    data['modules-left'] = ['workspaces', 'window']
    data['height'] = candidate['bar_height']
    data['window']['max-length'] = candidate['title_max_width']
    return data


def render(output=OUT):
    theme = tomllib.loads((ROOT / 'themes/rhapsody.toml').read_text())
    output.mkdir(parents=True, exist_ok=True)
    config = candidate_config(theme)
    (output / 'revised.jsonc').write_text(json.dumps(config, indent=2) + '\n')
    (output / 'revised.css').write_text(render_quiet(theme))
    # Keep old screenshots for historical comparison, remove obsolete styles.
    for stale in ('config.jsonc', 'vermillion.css', 'neutral.css',
                  'A.css', 'B.css', 'C.css', 'A.jsonc', 'B.jsonc', 'C.jsonc'):
        (output / stale).unlink(missing_ok=True)
    return output


def preview(output=OUT, seconds=25):
    if not 15 <= seconds <= 300:
        raise ValueError('preview duration must be 15–300 seconds')
    output = render(output)
    before = output / 'revised-before.png'
    after = output / 'revised-candidate.png'
    hover = output / 'revised-hover.png'
    subprocess.run(['grim', str(before)], check=True)
    subprocess.run([sys.executable, str(ROOT / 'scripts/quiet-mangobar-build.py')], check=True)
    bar = subprocess.Popen([str(BAR), '-c', str(output / 'revised.jsonc'),
                            '-s', str(output / 'revised.css')])
    try:
        time.sleep(3)
        if bar.poll() is not None:
            raise RuntimeError('preview bar exited before capture')
        subprocess.run(['grim', str(after)], check=True)
        print(f'Revised preview visible for {seconds} seconds; move across all nine workspaces.', flush=True)
        time.sleep(10)
        subprocess.run(['grim', str(hover)], check=True)
        time.sleep(seconds - 10)
    finally:
        if bar.poll() is None:
            bar.terminate()
            try:
                bar.wait(timeout=5)
            except subprocess.TimeoutExpired:
                bar.kill()
                bar.wait()
    print(f'Screenshots: {before}, {after}, {hover}. Live bar unchanged.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['render', 'preview'])
    parser.add_argument('--seconds', type=int, default=25)
    args = parser.parse_args()
    try:
        if args.action == 'render':
            print(render())
        else:
            preview(seconds=args.seconds)
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as exc:
        raise SystemExit(f'Quiet Workspace Strip: {exc}')
