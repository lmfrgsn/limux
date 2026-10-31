#!/usr/bin/env python3
"""Guarded Limux desktop portals: the screen-share picker and floating file choosers.

  activate  install the wlr portal config and the Limux screen-share chooser, add the
            file-chooser float rule to MangoWM, restart the portals
  verify    every owned file matches its pin and the rule is present once
  rollback  remove the files and the rule, restart the wlr portal

The portals themselves (xdg-desktop-portal, -wlr, -gtk) are packages that start on
demand; MangoWM ships their mango-portals.conf. File-chooser styling is part of the
Limux GTK stylesheet (scripts/activate-gtk.py). Run from Foot in the desktop session.
"""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
HOME = Path.home()
MANIFEST = ROOT/'themes/recovery/portals.json'
CONFIG = HOME/'.config/mango/config.conf'
# Hand-maintained files: the live copy is canonical; machine/ holds the reviewed source.
SOURCES = {HOME/'.config/xdg-desktop-portal-wlr/config': ROOT/'machine/home/.config/xdg-desktop-portal-wlr/config',
           HOME/'.local/bin/limux-screen-chooser': ROOT/'machine/home/.local/bin/limux-screen-chooser'}
# Retired: the GTK portal ignores GTK_THEME, so this drop-in had no effect.
RETIRED = HOME/'.config/systemd/user/xdg-desktop-portal-gtk.service.d/limux.conf'
RULE = 'window_rule=is_floating:1,width:1100,height:700,app_id:xdg-desktop-portal-gtk'
PACKAGES = ('xdg-desktop-portal', 'xdg-desktop-portal-wlr', 'xdg-desktop-portal-gtk')


def digest(data):
    return hashlib.sha256(data).hexdigest()


def run(*args):
    return subprocess.run(args, check=True, capture_output=True, text=True, timeout=20)


def candidate(manifest):
    files = {live: source.read_bytes() for live, source in SOURCES.items()}
    for path, data in files.items():
        if digest(data) != manifest['files'][str(path.relative_to(HOME))]:
            raise RuntimeError(f'{path.name} differs from the approved pin')
    return files


def has_rule(text):
    lines = [line.strip() for line in text.splitlines() if not line.lstrip().startswith('#')]
    portal = [line for line in lines if line.startswith('window_rule=') and 'xdg-desktop-portal-gtk' in line]
    if portal and portal != [RULE]:
        raise RuntimeError('another window rule targets the GTK portal; inspect the MangoWM config')
    return bool(portal)


def state(manifest):
    out = {}
    for rel, pin in manifest['files'].items():
        path = HOME/rel
        out[rel] = ('original' if not path.exists() else
                    'active' if path.is_file() and not path.is_symlink() and digest(path.read_bytes()) == pin
                    else 'unknown')
    out['rule'] = 'active' if has_rule(CONFIG.read_text()) else 'original'
    return out


def write_config(before, after):
    with tempfile.NamedTemporaryFile(mode='w', dir=CONFIG.parent, prefix='.portals-', delete=False) as stream:
        stream.write(after)
        staged = Path(stream.name)
    try:
        run('mango', '-p', '-c', str(staged))
        os.chmod(staged, CONFIG.stat().st_mode & 0o777)
        os.replace(staged, CONFIG)
    finally:
        staged.unlink(missing_ok=True)
    try:
        run('mmsg', 'dispatch', 'reload_config')
        run('mmsg', 'get', 'version')
    except Exception:
        CONFIG.write_text(before)
        raise


def write_file(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix='.limux-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            os.fchmod(stream.fileno(), 0o755 if path.parent.name == 'bin' else 0o644)
            stream.write(data)
        os.replace(name, path)
    finally:
        Path(name).unlink(missing_ok=True)


def restart_portals():
    run('systemctl', '--user', 'daemon-reload')
    # The front end keeps its connections to running backends; restart it with them.
    run('systemctl', '--user', 'try-restart', 'xdg-desktop-portal-wlr.service', 'xdg-desktop-portal-gtk.service',
        'xdg-desktop-portal.service')


def activate(manifest):
    missing = [p for p in PACKAGES if subprocess.run(['pacman', '-Q', p], capture_output=True).returncode]
    if missing or not shutil.which('rofi'):
        raise RuntimeError('install first: sudo pacman -S --needed ' + ' '.join(PACKAGES))
    run('mmsg', 'get', 'version')
    if RETIRED.is_file() and RETIRED.read_text().strip().endswith('Environment=GTK_THEME=Limux-Dialog'):
        RETIRED.unlink()
        try:
            RETIRED.parent.rmdir()
        except OSError:
            pass
        restart_portals()
    files = candidate(manifest)
    current = state(manifest)
    unknown = sorted(k for k, v in current.items() if v == 'unknown')
    if unknown:
        raise RuntimeError('unrecognised existing files; refusing to overwrite: ' + ', '.join(unknown))
    if set(current.values()) == {'active'}:
        print('Portals already configured.')
        return
    written, before = [], CONFIG.read_text()
    try:
        for path, data in files.items():
            if not path.exists():
                write_file(path, data)
                written.append(path)
        if not has_rule(before):
            lines = before.splitlines(keepends=True)
            last = max(i for i, line in enumerate(lines) if line.startswith('tag_rule='))
            lines.insert(last + 1, RULE + '\n')
            write_config(before, ''.join(lines))
        restart_portals()
        if set(state(manifest).values()) != {'active'}:
            raise RuntimeError('activation did not verify')
    except BaseException as failure:
        if CONFIG.read_text() != before:
            write_config(CONFIG.read_text(), before)
        for path in written:
            path.unlink(missing_ok=True)
        raise RuntimeError('activation failed; previous state restored') from failure
    print('Portals configured: screen sharing uses the Limux picker; file choosers float, centred.')


def rollback(manifest):
    current = state(manifest)
    unknown = sorted(k for k, v in current.items() if v == 'unknown')
    if unknown:
        raise RuntimeError('owned files have unreviewed edits; refusing to remove: ' + ', '.join(unknown))
    before = CONFIG.read_text()
    if current['rule'] == 'active':
        write_config(before, ''.join(line for line in before.splitlines(keepends=True) if line.strip() != RULE))
    for rel in manifest['files']:
        (HOME/rel).unlink(missing_ok=True)
    for folder in (HOME/'.config/xdg-desktop-portal-wlr', HOME/'.config/systemd/user/xdg-desktop-portal-gtk.service.d'):
        try:
            folder.rmdir()
        except OSError:
            pass
    restart_portals()
    print('Portal configuration removed; the portals use their defaults. Packages stay installed.')


def verify(manifest):
    candidate(manifest)
    current = state(manifest)
    summary = ('active' if set(current.values()) == {'active'} else
               'not active' if set(current.values()) == {'original'} else
               'mixed: ' + ', '.join(f'{k}={v}' for k, v in current.items()))
    print(f'Approval pins verified. Portal configuration {summary}.')
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('action', choices=['activate', 'verify', 'rollback'])
    action = parser.parse_args().action
    manifest = json.loads(MANIFEST.read_text())
    if action == 'verify':
        if verify(manifest) != 'active':
            raise SystemExit('Portal configuration is not fully active.')
        return
    with (Path(os.environ['XDG_RUNTIME_DIR'])/'limux-portals-activation.lock').open('w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        activate(manifest) if action == 'activate' else rollback(manifest)


if __name__ == '__main__':
    try:
        main()
    except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as exc:
        raise SystemExit(f'Portals: {exc}')
