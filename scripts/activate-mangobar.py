#!/usr/bin/env python3
"""Activate/rollback the approved baseline through the existing managed launcher.

Never edits functionality or startup. Refuses unknown CSS, unmanaged processes,
changed launchers and inaccessible sessions. Restores prior CSS on restart failure.
"""
import argparse
import ctypes
import fcntl
import hashlib
import json
import os
import signal
from pathlib import Path
import subprocess
import tempfile
import time
import tomllib
from mangobar import render

ROOT = Path(__file__).resolve().parents[1]
HOME = Path.home()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def atomic_write(path, data):
    if path.is_symlink() or not path.is_file():
        raise RuntimeError(f'Expected a regular owned file: {path}')
    mode = path.stat().st_mode & 0o777
    fd, temporary = tempfile.mkstemp(prefix='.limux-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as f:
            os.fchmod(f.fileno(), mode)
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temporary, path)
        directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        Path(temporary).unlink(missing_ok=True)


def transition(path, desired, refresh, verify):
    previous = path.read_bytes()
    if previous == desired:
        verify()
        return 'Already active; one managed process verified.'
    try:
        atomic_write(path, desired)
        refresh()
        verify()
    except BaseException as failure:
        atomic_write(path, previous)
        try:
            refresh()
            verify()
        except BaseException as recovery:
            raise RuntimeError(f'Prior CSS restored, but bar recovery failed: {recovery}') from failure
        raise RuntimeError('Activation failed; prior CSS and managed bar restored.') from failure
    return 'Style activated; one managed process verified.'


def require_session():
    lib = ctypes.CDLL('libwayland-client.so.0')
    lib.wl_display_connect.argtypes = [ctypes.c_char_p]
    lib.wl_display_connect.restype = ctypes.c_void_p
    lib.wl_display_disconnect.argtypes = [ctypes.c_void_p]
    display = lib.wl_display_connect(None)
    if not display:
        raise RuntimeError('Cannot reach Wayland. Run from Foot in the active desktop session; no files changed.')
    lib.wl_display_disconnect(display)


def startup_entries(home):
    roots = [home/'.config/mango', home/'.config/autostart', home/'.config/systemd/user',
             Path('/etc/xdg/autostart'), Path('/etc/systemd/user')]
    entries = []
    for root in roots:
        if not root.exists():
            continue
        for path in root.rglob('*'):
            if not path.is_file():
                continue
            # Ignore disabled service definitions; enabled user-unit symlinks
            # are inspected as well. Fail conservatively on any extra launcher.
            for line in path.read_text(errors='replace').splitlines():
                line = line.strip()
                if line.startswith(('exec=', 'exec_once=', 'Exec=', 'ExecStart=')) and any(
                        name in line for name in ('mangobar', 'limux-bar', 'waybar')):
                    entries.append((path, line))
    expected = (home/'.config/mango/config.conf', f'exec_once={home}/.local/bin/limux-bar start')
    if entries != [expected]:
        raise RuntimeError(f'Expected exactly the existing Mangobar startup entry; found {entries}')
    return entries


def managed_status(launcher, home):
    result = subprocess.run([str(launcher), 'status'], check=True, capture_output=True, text=True)
    status = json.loads(result.stdout)
    pids = status['mangobar']
    if len(pids) != 1 or pids[0] != status['managed_pid']:
        raise RuntimeError(f'Expected one existing managed Mangobar; found {status}')
    pid = pids[0]
    proc = Path('/proc')/str(pid)
    if proc.stat().st_uid != os.getuid() or (proc/'exe').resolve() != (home/'.local/bin/mangobar').resolve():
        raise RuntimeError('Managed process executable/owner mismatch')
    argv = (proc/'cmdline').read_bytes().split(b'\0')[:-1]
    expected = [str(home/'.local/bin/mangobar'), '-c', str(home/'.config/mangobar/config.jsonc'),
                '-s', str(home/'.config/mangobar/style.css')]
    if argv != [arg.encode() for arg in expected]:
        raise RuntimeError('Managed bar uses unexpected config/style arguments')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['check', 'activate', 'rollback'])
    args = parser.parse_args()
    recovery = ROOT/'themes/recovery'
    manifest = json.loads((recovery/'mangobar.json').read_text())
    baseline = render(tomllib.loads((ROOT/'themes/rhapsody.toml').read_text())).encode()
    rollback = (recovery/'mangobar-before-rhapsody.css').read_bytes()
    launcher = HOME/'.local/bin/limux-bar'
    if digest(baseline) != manifest['baseline_sha256'] or digest(rollback) != manifest['rollback_sha256']:
        raise RuntimeError('Baseline/recovery differs from the reviewed manifest; refusing activation')
    if digest(launcher.read_bytes()) != manifest['launcher_sha256']:
        raise RuntimeError('Existing launcher changed; review before activation')
    startup_entries(HOME)
    path = HOME/'.config/mangobar/style.css'
    if path.is_symlink() or digest(path.read_bytes()) not in (manifest['baseline_sha256'], manifest['rollback_sha256']):
        raise RuntimeError('Unrecognized live style; preserve/review it before activation')
    require_session()
    managed_status(launcher, HOME)
    protected = [HOME/'.config/mangobar/config.jsonc', HOME/'.config/mango/config.conf', launcher]
    before = {p: digest(p.read_bytes()) for p in protected}

    def verify():
        managed_status(launcher, HOME)
        startup_entries(HOME)
        if any(digest(p.read_bytes()) != h for p, h in before.items()):
            raise RuntimeError('Functional config or launcher changed during activation')

    def refresh():
        subprocess.run([str(launcher), 'refresh'], check=True, timeout=20)
        time.sleep(2)

    # Serialize activation attempts separately from the launcher's refresh lock.
    with (Path(os.environ['XDG_RUNTIME_DIR'])/'limux-style-activation.lock').open('w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        verify()
        if digest(path.read_bytes()) not in (manifest['baseline_sha256'], manifest['rollback_sha256']):
            raise RuntimeError('Live style changed during preflight')
        if args.action == 'check':
            print('Session reachable; one managed Mangobar and one startup entry verified.')
            return
        desired = baseline if args.action == 'activate' else rollback
        print(transition(path, desired, refresh, verify))
        if path.read_bytes() != desired:
            raise RuntimeError('Live style changed after activation')


if __name__ == '__main__':
    def interrupted(signum, frame):
        raise InterruptedError('Activation interrupted')
    signal.signal(signal.SIGTERM, interrupted)
    try:
        main()
    except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as exc:
        raise SystemExit(str(exc))
