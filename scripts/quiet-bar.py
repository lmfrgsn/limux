#!/usr/bin/env python3
"""Render and briefly preview unapproved Quiet Workspace Strip candidates."""
import argparse
import json
from pathlib import Path
import subprocess
import time
import tomllib
from mangobar import render_quiet

ROOT = Path(__file__).resolve().parents[1]
LIVE = Path.home() / '.config/mangobar/config.jsonc'
BAR = Path.home() / '.local/bin/mangobar'
OUT = ROOT / 'build/quiet-workspace-strip'


def candidate_config(path=LIVE):
    # Current live JSONC is strict JSON. Refuse unfamiliar syntax rather than
    # risk dropping a commented setting while generating an isolated preview.
    data = json.loads(path.read_text())
    left = data['modules-left']
    if left != ['workspaces', 'layout', 'window']:
        raise ValueError('unexpected left modules; inspect before changing the preview')
    data['modules-left'] = ['workspaces', 'window']
    data['window']['max-length'] = 240
    return data


def render(output=OUT):
    theme = tomllib.loads((ROOT / 'themes/rhapsody.toml').read_text())
    config = candidate_config()
    output.mkdir(parents=True, exist_ok=True)
    (output / 'config.jsonc').write_text(json.dumps(config, indent=2) + '\n')
    for variant in ('vermillion', 'neutral'):
        (output / f'{variant}.css').write_text(render_quiet(theme, variant))
    return output


def preview(variant, output=OUT):
    output = render(output)
    before = output / f'{variant}-before.png'
    after = output / f'{variant}-candidate.png'
    hover = output / f'{variant}-hover.png'
    subprocess.run(['grim', str(before)], check=True)
    bar = subprocess.Popen([str(BAR), '-c', str(output / 'config.jsonc'),
                            '-s', str(output / f'{variant}.css')])
    try:
        time.sleep(3)
        if bar.poll() is not None:
            raise RuntimeError('preview bar exited before capture')
        subprocess.run(['grim', str(after)], check=True)
        print(f'{variant} preview visible for 25 seconds; move the pointer across all nine workspaces.', flush=True)
        time.sleep(10)
        subprocess.run(['grim', str(hover)], check=True)
        time.sleep(15)
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
    parser.add_argument('--variant', choices=['vermillion', 'neutral'], default='vermillion')
    args = parser.parse_args()
    try:
        if args.action == 'render':
            print(render())
        else:
            preview(args.variant)
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as exc:
        raise SystemExit(f'Quiet Workspace Strip: {exc}')
