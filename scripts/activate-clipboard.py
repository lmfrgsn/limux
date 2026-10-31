#!/usr/bin/env python3
"""Guarded Limux clipboard history: the limux-clipboard helper, its watcher autostart
and the Command+Shift+V binding.

  activate  install the helper, add the autostart and binding, start the watcher
  verify    pinned helper, one watcher running, each MangoWM line present once
  rollback  stop the watcher, wipe the history, remove the lines and the helper

Run from Foot in the desktop session; cliphist is installed separately.
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
import time

ROOT = Path(__file__).resolve().parents[1]
HOME = Path.home()
MANIFEST = ROOT/'themes/recovery/clipboard.json'
CONFIG = HOME/'.config/mango/config.conf'
HELPER = HOME/'.local/bin/limux-clipboard'
SOURCE = ROOT/'machine/home/.local/bin/limux-clipboard'
AUTOSTART = f'exec_once={HELPER} watch'
BINDING = f'bind=SUPER+SHIFT,v,spawn,{HELPER} pick'
LAUNCHER = 'bind=SUPER,space,spawn,rofi -show drun'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def run(*args):
    return subprocess.run(args, check=True, capture_output=True, text=True, timeout=12)


def watchers():
    """PIDs of this user's limux-clipboard watch processes."""
    found = subprocess.run(['pgrep', '-u', str(os.getuid()), '-f', f'{HELPER} watch$'], capture_output=True, text=True)
    return [int(pid) for pid in found.stdout.split()]


def lines(text):
    current = [line.strip() for line in text.splitlines() if not line.lstrip().startswith('#')]
    keys = [line for line in current if line.lower().replace(' ', '').startswith(('bind=super+shift,v,', 'bind=shift+super,v,'))]
    if keys and keys != [BINDING]:
        raise RuntimeError('Command+Shift+V is already assigned to something else')
    starts = [line for line in current if line.startswith('exec') and 'clip' in line]
    if starts and starts != [AUTOSTART]:
        raise RuntimeError('another clipboard autostart exists; inspect the MangoWM config')
    return bool(keys), bool(starts)


def write_config(before, after):
    with tempfile.NamedTemporaryFile(mode='w', dir=CONFIG.parent, prefix='.clipboard-', delete=False) as stream:
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


def candidate(manifest):
    data = SOURCE.read_bytes()
    if digest(data) != manifest['helper']:
        raise RuntimeError('limux-clipboard differs from the approved pin')
    return data


def helper_state(manifest):
    if not HELPER.exists():
        return 'original'
    found = digest(HELPER.read_bytes()) if HELPER.is_file() and not HELPER.is_symlink() else None
    return ('active' if found == manifest['helper'] else
            'previous' if found in manifest.get('previous', []) else 'unknown')


def activate(manifest):
    if not shutil.which('cliphist') or not shutil.which('wl-paste'):
        raise RuntimeError('install first: sudo pacman -S --needed cliphist')
    run('mmsg', 'get', 'version')
    data = candidate(manifest)
    state = helper_state(manifest)
    if state == 'unknown':
        raise RuntimeError(f'{HELPER} has unreviewed edits; refusing to overwrite')
    before = CONFIG.read_text()
    binding, autostart = lines(before)
    if state == 'active' and binding and autostart and len(watchers()) == 1:
        print('Clipboard history already active.')
        return
    previous = HELPER.read_bytes() if HELPER.exists() else None
    try:
        if state != 'active':
            HELPER.parent.mkdir(parents=True, exist_ok=True)
            fd, name = tempfile.mkstemp(prefix='.limux-', dir=HELPER.parent)
            with os.fdopen(fd, 'wb') as stream:
                os.fchmod(stream.fileno(), 0o755)
                stream.write(data)
            os.replace(name, HELPER)
        if not (binding and autostart):
            text = before.splitlines(keepends=True)
            if not autostart:
                last = max(i for i, line in enumerate(text) if line.startswith('exec_once='))
                text.insert(last + 1, AUTOSTART + '\n')
            if not binding:
                launcher = next(i for i, line in enumerate(text) if line.strip() == LAUNCHER)
                text.insert(launcher + 1, BINDING + '\n')
            write_config(before, ''.join(text))
        for pid in watchers():
            os.kill(pid, 15)  # restart so the watcher runs the current helper
        time.sleep(0.5)
        subprocess.Popen(['setsid', '-f', str(HELPER), 'watch'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(1.5)
        if len(watchers()) != 1:
            raise RuntimeError('the clipboard watcher did not start')
    except BaseException as failure:
        for pid in watchers():
            os.kill(pid, 15)
        if CONFIG.read_text() != before:
            write_config(CONFIG.read_text(), before)
        if previous is None:
            HELPER.unlink(missing_ok=True)
        else:
            HELPER.write_bytes(previous)
        raise RuntimeError('activation failed; previous state restored') from failure
    print('Clipboard history active: Command+Shift+V shows recent copies.')


def rollback(manifest):
    if helper_state(manifest) == 'unknown':
        raise RuntimeError(f'{HELPER} has unreviewed edits; refusing to remove')
    if HELPER.exists() and shutil.which('cliphist'):
        subprocess.run([str(HELPER), 'clear'], capture_output=True)
    for pid in watchers():
        os.kill(pid, 15)
    before = CONFIG.read_text()
    if any(lines(before)):
        run('mmsg', 'get', 'version')
        write_config(before, ''.join(line for line in before.splitlines(keepends=True)
                                     if line.strip() not in (AUTOSTART, BINDING)))
    HELPER.unlink(missing_ok=True)
    print('Clipboard history removed: watcher stopped, history wiped, binding and autostart removed.')


def verify(manifest):
    candidate(manifest)
    binding, autostart = lines(CONFIG.read_text())
    state, count = helper_state(manifest), len(watchers())
    summary = ('active' if (state, binding, autostart, count) == ('active', True, True, 1) else
               'not active' if (state, binding, autostart, count) == ('original', False, False, 0) else
               f'mixed: helper={state}, binding={binding}, autostart={autostart}, watchers={count}')
    print(f'Approval pin verified. Clipboard history {summary}.')
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('action', choices=['activate', 'verify', 'rollback'])
    action = parser.parse_args().action
    manifest = json.loads(MANIFEST.read_text())
    if action == 'verify':
        if verify(manifest) != 'active':
            raise SystemExit('Clipboard history is not fully active.')
        return
    with (Path(os.environ['XDG_RUNTIME_DIR'])/'limux-clipboard-activation.lock').open('w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        activate(manifest) if action == 'activate' else rollback(manifest)


if __name__ == '__main__':
    try:
        main()
    except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as exc:
        raise SystemExit(f'Clipboard history: {exc}')
