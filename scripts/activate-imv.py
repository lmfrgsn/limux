#!/usr/bin/env python3
"""Guarded Limux image viewer: the generated imv config and imv as the default for
common image types.

  activate  install ~/.config/imv/config and set imv as the image default
  verify    pinned config and every image default pointing at imv
  rollback  remove the config and Limux's image defaults (the system default returns)

imv is installed separately. Appearance comes from [imv] tokens (scripts/imv.py).
"""
import argparse
import configparser
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import tomllib

ROOT = Path(__file__).resolve().parents[1]
HOME = Path.home()
sys.path.insert(0, str(ROOT/'scripts'))
from imv import render  # noqa: E402

MANIFEST = ROOT/'themes/recovery/imv.json'
CONFIG = HOME/'.config/imv/config'
MIMEAPPS = HOME/'.config/mimeapps.list'
DESKTOP = 'imv.desktop'
TYPES = ('image/png', 'image/jpeg', 'image/gif', 'image/webp', 'image/bmp', 'image/tiff', 'image/svg+xml',
         'image/heif', 'image/heic', 'image/avif', 'image/jxl')
SECTION = 'Default Applications'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def candidate(manifest):
    data = render(tomllib.loads((ROOT/'themes/rhapsody.toml').read_text())).encode()
    if digest(data) != manifest['config']:
        raise RuntimeError('generated imv config differs from the approved pin')
    return data


def read_mimeapps():
    parser = configparser.ConfigParser(interpolation=None, delimiters=('=',))
    parser.optionxform = str  # MIME types are case-sensitive keys
    if MIMEAPPS.exists():
        parser.read_string(MIMEAPPS.read_text())
    return parser


def defaults_state():
    parser = read_mimeapps()
    current = {t: parser.get(SECTION, t, fallback=None) for t in TYPES}
    others = sorted(t for t, v in current.items() if v not in (None, DESKTOP))
    if others:
        raise RuntimeError('another app is the chosen default for ' + ', '.join(others) + '; inspect mimeapps.list')
    values = set(current.values())
    return 'active' if values == {DESKTOP} else 'original' if values == {None} else 'mixed'


def write_mimeapps(parser):
    buffer = io.StringIO()
    parser.write(buffer, space_around_delimiters=False)
    MIMEAPPS.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix='.limux-', dir=MIMEAPPS.parent)
    try:
        with os.fdopen(fd, 'w') as stream:
            stream.write(buffer.getvalue().rstrip('\n') + '\n')
        os.replace(name, MIMEAPPS)
    finally:
        Path(name).unlink(missing_ok=True)


def config_state(manifest):
    if not CONFIG.exists():
        return 'original'
    found = digest(CONFIG.read_bytes()) if CONFIG.is_file() and not CONFIG.is_symlink() else None
    return ('active' if found == manifest['config'] else
            'previous' if found in manifest.get('previous', []) else 'unknown')


def activate(manifest):
    if not shutil.which('imv') or not Path('/usr/share/applications', DESKTOP).is_file():
        raise RuntimeError('install first: sudo pacman -S --needed imv')
    data = candidate(manifest)
    state = config_state(manifest)
    if state == 'unknown':
        raise RuntimeError(f'{CONFIG} has unreviewed edits; refusing to overwrite')
    if state == 'active' and defaults_state() == 'active':
        print('Image viewer already active.')
        return
    before = MIMEAPPS.read_bytes() if MIMEAPPS.exists() else None
    CONFIG.parent.mkdir(parents=True, exist_ok=True)
    CONFIG.write_bytes(data)
    try:
        parser = read_mimeapps()
        if not parser.has_section(SECTION):
            parser.add_section(SECTION)
        for t in TYPES:
            parser.set(SECTION, t, DESKTOP)
        write_mimeapps(parser)
        if defaults_state() != 'active':
            raise RuntimeError('image defaults did not verify')
    except BaseException:
        if before is None:
            MIMEAPPS.unlink(missing_ok=True)
        else:
            MIMEAPPS.write_bytes(before)
        raise
    print('Image viewer active: images open in imv on a graphite ground; press o for the info line.')


def rollback(manifest):
    if config_state(manifest) == 'unknown':
        raise RuntimeError(f'{CONFIG} has unreviewed edits; refusing to remove')
    defaults_state()  # refuses if another app was chosen meanwhile
    parser = read_mimeapps()
    if parser.has_section(SECTION):
        for t in TYPES:
            parser.remove_option(SECTION, t)
        write_mimeapps(parser)
    CONFIG.unlink(missing_ok=True)
    try:
        CONFIG.parent.rmdir()
    except OSError:
        pass
    print('Image viewer configuration removed; images use the system default again. imv stays installed.')


def verify(manifest):
    candidate(manifest)
    state, defaults = config_state(manifest), defaults_state()
    summary = ('active' if (state, defaults) == ('active', 'active') else
               'not active' if (state, defaults) == ('original', 'original') else
               f'mixed: config={state}, defaults={defaults}')
    print(f'Approval pin verified. Image viewer {summary}.')
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('action', choices=['activate', 'verify', 'rollback'])
    action = parser.parse_args().action
    manifest = json.loads(MANIFEST.read_text())
    if action == 'verify':
        if verify(manifest) != 'active':
            raise SystemExit('Image viewer is not fully active.')
        return
    activate(manifest) if action == 'activate' else rollback(manifest)


if __name__ == '__main__':
    try:
        main()
    except (OSError, RuntimeError, ValueError, configparser.Error) as exc:
        raise SystemExit(f'Image viewer: {exc}')
