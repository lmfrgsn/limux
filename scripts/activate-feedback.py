#!/usr/bin/env python3
"""Guarded Limux feedback: the level card for the volume, brightness, keyboard-light
and microphone keys, and the low-battery warning.

  activate  install limux-level and limux-battery, add the level call to
            t2-hardware-control and one battery autostart, start the watcher
  verify    pinned helpers, the level call and autostart present once, one watcher
  rollback  stop the watcher, remove the autostart, the level call and the helpers

The cards' appearance is the Mako fragment (scripts/activate-mako.py). Key
bindings and what each key does are unchanged: t2-hardware-control still sets the
level; the added call only shows it. Run from Foot in the desktop session.
"""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
HOME = Path.home()
MANIFEST = ROOT/'themes/recovery/feedback.json'
CONFIG = HOME/'.config/mango/config.conf'
BIN = HOME/'.local/bin'
HELPERS = ('limux-level', 'limux-battery')
CONTROL = BIN/'t2-hardware-control'
AUTOSTART = f'exec_once={BIN}/limux-battery'
LEVEL_CALL = '''
# Limux level card (scripts/activate-feedback.py): show the level just set.
case "${1:-}" in
    volume-up|volume-down|mute) limux_level=volume ;;
    mic-mute) limux_level=microphone ;;
    screen-up|screen-down) limux_level=display ;;
    keyboard-up|keyboard-down) limux_level=keyboard ;;
    *) limux_level= ;;
esac
if [[ -n $limux_level && -x $HOME/.local/bin/limux-level ]]; then
    "$HOME/.local/bin/limux-level" "$limux_level" >/dev/null 2>&1 || true
fi
'''


def digest(data):
    return hashlib.sha256(data).hexdigest()


def run(*args):
    return subprocess.run(args, check=True, capture_output=True, text=True, timeout=12)


def write(path, data, mode):
    fd, name = tempfile.mkstemp(prefix='.limux-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            os.fchmod(stream.fileno(), mode)
            stream.write(data)
        os.replace(name, path)
    finally:
        Path(name).unlink(missing_ok=True)


def sources(manifest):
    data = {name: (ROOT/'machine/home/.local/bin'/name).read_bytes() for name in HELPERS}
    if {name: digest(d) for name, d in data.items()} != manifest['helpers']:
        raise RuntimeError('a feedback helper differs from the approved pin')
    return data


def helper_state(name, manifest):
    path = BIN/name
    if not path.exists():
        return 'original'
    found = digest(path.read_bytes()) if path.is_file() and not path.is_symlink() else None
    return 'active' if found == manifest['helpers'][name] else 'unknown'


def control_state():
    text = CONTROL.read_text()
    count = text.count(LEVEL_CALL)
    if count > 1 or (count == 0 and 'limux-level' in text):
        raise RuntimeError(f'{CONTROL} has an edited level call; inspect it')
    return count == 1


def autostart_present(text):
    found = [line.strip() for line in text.splitlines() if 'limux-battery' in line and not line.lstrip().startswith('#')]
    if found and found != [AUTOSTART]:
        raise RuntimeError('another limux-battery line exists in the MangoWM config; inspect it')
    return bool(found)


def write_config(before, after):
    with tempfile.NamedTemporaryFile(mode='w', dir=CONFIG.parent, prefix='.feedback-', delete=False) as stream:
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
    except Exception:
        CONFIG.write_text(before)
        raise


def watchers():
    found = subprocess.run(['pgrep', '-u', str(os.getuid()), '-f', f'^(/usr/bin/)?bash {BIN}/limux-battery$'],
                           capture_output=True, text=True)
    return [int(pid) for pid in found.stdout.split()]


def activate(manifest):
    run('mmsg', 'get', 'version')
    data = sources(manifest)
    states = {name: helper_state(name, manifest) for name in HELPERS}
    if 'unknown' in states.values():
        raise RuntimeError('a feedback helper in ~/.local/bin has unreviewed edits; refusing to overwrite')
    before_config, before_control = CONFIG.read_text(), CONTROL.read_bytes()
    try:
        for name in HELPERS:
            if states[name] != 'active':
                write(BIN/name, data[name], 0o755)
        if not control_state():
            write(CONTROL, before_control + LEVEL_CALL.encode(), CONTROL.stat().st_mode & 0o777)
        if not autostart_present(before_config):
            text = before_config.splitlines(keepends=True)
            last = max(i for i, line in enumerate(text) if line.startswith('exec_once='))
            text.insert(last + 1, AUTOSTART + '\n')
            write_config(before_config, ''.join(text))
        for pid in watchers():
            os.kill(pid, 15)
        time.sleep(0.3)
        subprocess.Popen(['setsid', '-f', str(BIN/'limux-battery')], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(1)
        if len(watchers()) != 1:
            raise RuntimeError('the battery watcher did not start')
    except BaseException as failure:
        for pid in watchers():
            os.kill(pid, 15)
        if CONFIG.read_text() != before_config:
            write_config(CONFIG.read_text(), before_config)
        write(CONTROL, before_control, CONTROL.stat().st_mode & 0o777)
        for name in HELPERS:
            if states[name] == 'original':
                (BIN/name).unlink(missing_ok=True)
        raise RuntimeError('activation failed; previous state restored') from failure
    print('Feedback active: volume, brightness and keyboard-light keys show a level card; '
          'a battery warning appears at 10% and 5%.')


def rollback(manifest):
    if any(helper_state(name, manifest) == 'unknown' for name in HELPERS):
        raise RuntimeError('a feedback helper has unreviewed edits; refusing to remove')
    for pid in watchers():
        os.kill(pid, 15)
    before = CONFIG.read_text()
    if autostart_present(before):
        run('mmsg', 'get', 'version')
        write_config(before, ''.join(line for line in before.splitlines(keepends=True) if line.strip() != AUTOSTART))
    if control_state():
        write(CONTROL, CONTROL.read_bytes().replace(LEVEL_CALL.encode(), b''), CONTROL.stat().st_mode & 0o777)
    for name in HELPERS:
        (BIN/name).unlink(missing_ok=True)
    print('Feedback removed: no level card or battery warning; the keys work as before.')


def verify(manifest):
    sources(manifest)
    parts = {'helpers': all(helper_state(n, manifest) == 'active' for n in HELPERS),
             'level call': control_state(), 'autostart': autostart_present(CONFIG.read_text()),
             'watcher': len(watchers()) == 1}
    summary = 'active' if all(parts.values()) else 'mixed: ' + ', '.join(f'{k}={v}' for k, v in parts.items())
    print(f'Approval pin verified. Feedback {summary}.')
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('action', choices=['activate', 'verify', 'rollback'])
    action = parser.parse_args().action
    manifest = json.loads(MANIFEST.read_text())
    if action == 'verify':
        if verify(manifest) != 'active':
            raise SystemExit('Feedback is not fully active.')
        return
    with (Path(os.environ['XDG_RUNTIME_DIR'])/'limux-feedback-activation.lock').open('w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        activate(manifest) if action == 'activate' else rollback(manifest)


if __name__ == '__main__':
    try:
        main()
    except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as exc:
        raise SystemExit(f'Feedback: {exc}')
