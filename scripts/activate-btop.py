#!/usr/bin/env python3
"""Guarded Limux system monitor appearance for btop: the generated theme file and
the four appearance lines Limux owns in btop.conf.

  activate  install ~/.config/btop/themes/limux-rhapsody.theme and set the owned lines
  verify    pinned theme file and owned lines in place
  rollback  restore btop's default appearance lines and remove the theme file

btop is installed separately. Every other btop.conf line (boxes, sorting, update
rate, keys) stays btop's and the user's. btop rewrites btop.conf when it quits, so
every action refuses while btop is running. Appearance comes from [btop] tokens.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import tomllib

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
import btop  # noqa: E402

MANIFEST = ROOT/'themes/recovery/btop.json'


def paths():
    base = Path(os.environ.get('XDG_CONFIG_HOME', str(Path.home()/'.config')))/'btop'
    return base/'btop.conf', base/'themes'/f'{btop.NAME}.theme'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def candidate(manifest):
    theme = tomllib.loads((ROOT/'themes/rhapsody.toml').read_text())
    data, owned = btop.render(theme).encode(), btop.settings(theme)
    if digest(data) != manifest['theme'] or owned != manifest['settings']:
        raise RuntimeError('generated btop appearance differs from the approved pin')
    if set(owned) != set(manifest['defaults']):
        raise RuntimeError('btop owned lines and defaults disagree')
    return data, owned


def read_lines(text, keys):
    found = {}
    for line in text.splitlines():
        m = re.fullmatch(r'(\w+) = (.*)', line)
        if m and m.group(1) in keys:
            if m.group(1) in found:
                raise RuntimeError(f'btop.conf sets {m.group(1)} twice; inspect it')
            found[m.group(1)] = m.group(2)
    return found


def set_lines(text, values):
    for k, v in values.items():
        text, n = re.subn(rf'^{k} = .*$', lambda _: f'{k} = {v}', text, flags=re.M)
        if n == 0:
            text = text.rstrip('\n') + f'\n{k} = {v}\n'
    return text


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix='.limux-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            os.fchmod(stream.fileno(), 0o644)
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
    finally:
        Path(name).unlink(missing_ok=True)


def btop_running():
    return subprocess.run(['pgrep', '-u', str(os.getuid()), '-x', 'btop'], capture_output=True).returncode == 0


def state(manifest, owned):
    conf, theme = paths()
    text = conf.read_text() if conf.exists() else ''
    lines = read_lines(text, owned)
    defaults = manifest['defaults']
    for k in owned:
        if lines.get(k, defaults[k]) not in (owned[k], defaults[k]):
            raise RuntimeError(f'btop.conf {k} = {lines[k]} was chosen by hand; set it back or inspect it')
    if theme.exists() and (theme.is_symlink() or digest(theme.read_bytes()) not in [manifest['theme'], *manifest.get('previous', [])]):
        raise RuntimeError(f'{theme} has unreviewed edits')
    ours = all(lines.get(k) == owned[k] for k in owned)
    pinned = theme.exists() and digest(theme.read_bytes()) == manifest['theme']
    stock = all(lines.get(k, defaults[k]) == defaults[k] for k in owned) and not theme.exists()
    return 'active' if ours and pinned else 'original' if stock else 'mixed'


def activate(manifest):
    data, owned = candidate(manifest)
    if state(manifest, owned) == 'active':
        print('btop appearance already active.')
        return
    conf, theme = paths()
    before = conf.read_bytes() if conf.exists() else None
    base = before.decode() if before is not None else subprocess.run(
        ['btop', '--default-config'], check=True, capture_output=True, text=True).stdout
    write(theme, data)
    try:
        write(conf, set_lines(base, owned).encode())
        if state(manifest, owned) != 'active':
            raise RuntimeError('btop appearance did not verify')
    except BaseException:
        conf.unlink(missing_ok=True) if before is None else write(conf, before)
        theme.unlink(missing_ok=True)
        raise
    print('Limux btop appearance active; open btop to see it.')


def rollback(manifest):
    owned = manifest['settings']
    state(manifest, owned)  # refuses hand-chosen values and edited theme files
    conf, theme = paths()
    if conf.exists():
        write(conf, set_lines(conf.read_text(), manifest['defaults']).encode())
    theme.unlink(missing_ok=True)
    try:
        theme.parent.rmdir()
    except OSError:
        pass
    print("btop's default appearance restored; your other btop settings are unchanged.")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('action', choices=['activate', 'verify', 'rollback'])
    action = parser.parse_args().action
    manifest = json.loads(MANIFEST.read_text())
    if action == 'verify':
        _, owned = candidate(manifest)
        now = state(manifest, owned)
        print(f'Approval pin verified. btop appearance: {now}.')
        if now != 'active':
            raise SystemExit(1)
        return
    if btop_running():
        raise RuntimeError('btop rewrites btop.conf when it quits; close every btop first')
    activate(manifest) if action == 'activate' else rollback(manifest)


if __name__ == '__main__':
    try:
        main()
    except (OSError, RuntimeError, ValueError, subprocess.CalledProcessError) as exc:
        raise SystemExit(f'btop: {exc}')
