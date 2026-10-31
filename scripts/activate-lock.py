#!/usr/bin/env python3
"""Guarded Limux lock screen and idle behaviour: hyprlock, hypridle, one helper,
one MangoWM autostart and the Ctrl+Command+Q binding.

  test      lock now with the candidate config; unlock with your password. The lock
            releases itself after 60 seconds if anything goes wrong. Activation
            requires a passing test of these exact files.
  activate  install the files, add the autostart and binding, start hypridle
  verify    check every owned item against its pin
  rollback  stop hypridle, remove the binding, autostart and owned files

Run from Foot in the desktop session. Packages are installed separately.
"""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import tomllib

ROOT = Path(__file__).resolve().parents[1]
HOME = Path.home()
sys.path.insert(0, str(ROOT/'scripts'))
from lock import render  # noqa: E402

MANIFEST = ROOT/'themes/recovery/lock.json'
CONFIG = HOME/'.config/mango/config.conf'
APPEARANCE = HOME/'.config/hypr/limux-lock.conf'
# Hand-maintained files: the live copy is canonical; machine/ holds the reviewed source.
SOURCES = {HOME/'.config/hypr/hyprlock.conf': ROOT/'machine/home/.config/hypr/hyprlock.conf',
           HOME/'.config/hypr/hypridle.conf': ROOT/'machine/home/.config/hypr/hypridle.conf',
           HOME/'.local/bin/limux-idle': ROOT/'machine/home/.local/bin/limux-idle'}
AUTOSTART = 'exec_once=hypridle'
BINDING = 'bind=CTRL+SUPER,q,spawn,loginctl lock-session'
LAUNCHER = 'bind=SUPER,space,spawn,rofi -show drun'
PAM = Path('/etc/pam.d/hyprlock')
ESCAPE_SECONDS = 60


def digest(data):
    return hashlib.sha256(data).hexdigest()


def run(*args, timeout=12):
    return subprocess.run(args, check=True, capture_output=True, text=True, timeout=timeout)


def candidate(manifest):
    """Every owned file's desired bytes, checked against the approval pins."""
    theme = tomllib.loads((ROOT/'themes/rhapsody.toml').read_text())
    files = {APPEARANCE: render(theme).encode()}
    files.update({live: source.read_bytes() for live, source in SOURCES.items()})
    for path, data in files.items():
        if digest(data) != manifest['files'][str(path.relative_to(HOME))]:
            raise RuntimeError(f'{path.name} differs from the approved pin')
    return files


def candidate_digest(files):
    return digest(b''.join(digest(files[p]).encode() for p in sorted(files)))


def require_tools():
    for tool in ('hyprlock', 'hypridle', 'brightnessctl', 'mmsg', 'loginctl'):
        if not shutil.which(tool):
            raise RuntimeError(f'{tool} is not installed; run: sudo pacman -S --needed hyprlock hypridle')
    if not PAM.is_file():
        raise RuntimeError(f'{PAM} is missing; reinstall hyprlock before locking')
    run('mmsg', 'get', 'version')


def mango_lines(text):
    lines = [line.strip() for line in text.splitlines() if not line.lstrip().startswith('#')]
    if lines.count(LAUNCHER) != 1:
        raise RuntimeError('normal Command+Space launcher is not unique')
    others = [line for line in lines if line.lower().replace(' ', '').startswith(('bind=ctrl+super,q,', 'bind=super+ctrl,q,'))]
    if others and others != [BINDING]:
        raise RuntimeError('Ctrl+Command+Q is already assigned to something else')
    idle = [line for line in lines if line.startswith('exec') and 'hypridle' in line]
    if idle and idle != [AUTOSTART]:
        raise RuntimeError('another hypridle autostart exists; inspect the MangoWM config')
    return bool(others), bool(idle)


def owned_state(manifest):
    """'original', 'active', 'previous' (an earlier approved version) or 'unknown' for each owned item."""
    state = {}
    for rel, pin in manifest['files'].items():
        path = HOME/rel
        if path.is_symlink() or (path.exists() and not path.is_file()):
            state[rel] = 'unknown'
        elif not path.exists():
            state[rel] = 'original'
        else:
            found = digest(path.read_bytes())
            state[rel] = ('active' if found == pin else
                          'previous' if found in manifest.get('previous', {}).get(rel, []) else 'unknown')
    binding, autostart = mango_lines(CONFIG.read_text())
    state['binding'] = 'active' if binding else 'original'
    state['autostart'] = 'active' if autostart else 'original'
    return state


def hypridle_pids():
    found = subprocess.run(['pgrep', '-u', str(os.getuid()), '-x', 'hypridle'], capture_output=True, text=True)
    return [int(pid) for pid in found.stdout.split()]


def atomic_write(path, data, mode=0o644):
    if path.is_symlink() or (path.exists() and not path.is_file()):
        raise RuntimeError(f'unsafe destination: {path}')
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix='.limux-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            os.fchmod(stream.fileno(), mode)
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
    finally:
        Path(name).unlink(missing_ok=True)


def write_mango(before, after):
    with tempfile.NamedTemporaryFile(mode='w', dir=CONFIG.parent, prefix='.lock-', delete=False) as stream:
        stream.write(after)
        staged = Path(stream.name)
    try:
        run('mango', '-p', '-c', str(staged))
    finally:
        staged.unlink(missing_ok=True)
    mode = CONFIG.stat().st_mode & 0o777
    atomic_write(CONFIG, after.encode(), mode)
    try:
        run('mmsg', 'dispatch', 'reload_config')
        run('mmsg', 'get', 'version')
    except Exception:
        atomic_write(CONFIG, before.encode(), mode)
        try:
            run('mmsg', 'dispatch', 'reload_config')
        except Exception:
            pass
        raise


def with_lines(text):
    lines = text.splitlines(keepends=True)
    last_exec = max(i for i, line in enumerate(lines) if line.startswith('exec_once='))
    lines.insert(last_exec + 1, AUTOSTART + '\n')
    launcher = next(i for i, line in enumerate(lines) if line.strip() == LAUNCHER)
    lines.insert(launcher + 1, BINDING + '\n')
    return ''.join(lines)


def without_lines(text):
    return ''.join(line for line in text.splitlines(keepends=True) if line.strip() not in (AUTOSTART, BINDING))


def marker():
    return Path(os.environ['XDG_RUNTIME_DIR'])/'limux-lock-tested'


# --- Actions -------------------------------------------------------------------

def test(manifest):
    """Lock with the candidate files staged privately; pass only on a password unlock."""
    require_tools()
    files = candidate(manifest)
    if subprocess.run(['pgrep', '-u', str(os.getuid()), '-x', 'hyprlock'], capture_output=True).returncode == 0:
        raise RuntimeError('hyprlock is already running')
    with tempfile.TemporaryDirectory(prefix='limux-lock-') as folder:
        stage = Path(folder)
        (stage/'limux-lock.conf').write_bytes(files[APPEARANCE])
        main = files[HOME/'.config/hypr/hyprlock.conf'].decode().replace(
            'source = ~/.config/hypr/limux-lock.conf', f'source = {stage/"limux-lock.conf"}')
        (stage/'hyprlock.conf').write_text(main)
        print(f'Locking now. Unlock with your password; it releases itself after {ESCAPE_SECONDS} seconds.', flush=True)
        time.sleep(2)
        log = Path(os.environ['XDG_RUNTIME_DIR'])/'limux-lock-test.log'
        with log.open('w') as stream:
            lock = subprocess.Popen(['hyprlock', '--verbose', '--config', str(stage/'hyprlock.conf')],
                                    stdout=stream, stderr=subprocess.STDOUT)
        started, released = time.monotonic(), False
        while lock.poll() is None:
            if time.monotonic() - started > ESCAPE_SECONDS:
                lock.send_signal(signal.SIGUSR1)  # hyprlock's own unlock signal
                released = True
                try:
                    lock.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    lock.kill()
                break
            time.sleep(0.5)
    if released:
        raise RuntimeError(f'the test lock was released automatically, not by password; log: {log}')
    if lock.returncode != 0:
        raise RuntimeError(f'hyprlock exited with {lock.returncode}; log: {log}')
    marker().write_text(candidate_digest(files))
    print('Password unlock works with these exact files. You can activate.')


def activate(manifest):
    require_tools()
    files = candidate(manifest)
    if not marker().exists() or marker().read_text() != candidate_digest(files):
        raise RuntimeError('run the unlock test first: python3 scripts/activate-lock.py test')
    state = owned_state(manifest)
    unknown = sorted(k for k, v in state.items() if v == 'unknown')
    if unknown:
        raise RuntimeError('unrecognised existing files; refusing to overwrite: ' + ', '.join(unknown))
    if set(state.values()) == {'active'} and len(hypridle_pids()) == 1:
        print('Lock screen already active.')
        return
    upgrade = state['binding'] == 'active' and state['autostart'] == 'active'
    if hypridle_pids() and not upgrade:
        raise RuntimeError('hypridle is already running outside Limux; stop it first')
    if upgrade:
        # Only appearance or helper files change; the running hypridle keeps going
        # and hyprlock reads its config at each lock.
        for path, data in files.items():
            if state[str(path.relative_to(HOME))] == 'previous':
                atomic_write(path, data, 0o755 if path.name == 'limux-idle' else 0o644)
        if set(owned_state(manifest).values()) != {'active'}:
            raise RuntimeError('upgrade did not verify')
        print('Lock screen updated in place.')
        return
    written = []
    before = CONFIG.read_text()
    try:
        replaced = {}
        for path, data in files.items():
            if not path.exists():
                atomic_write(path, data, 0o755 if path.name == 'limux-idle' else 0o644)
                written.append(path)
            elif state[str(path.relative_to(HOME))] == 'previous':
                replaced[path] = path.read_bytes()
                atomic_write(path, data, 0o755 if path.name == 'limux-idle' else 0o644)
        after = without_lines(before)
        write_mango(before, with_lines(after))
        subprocess.Popen(['setsid', '-f', 'hypridle'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(1.5)
        if len(hypridle_pids()) != 1:
            raise RuntimeError('hypridle did not start')
        if set(owned_state(manifest).values()) != {'active'}:
            raise RuntimeError('activation did not verify')
    except BaseException as failure:
        for pid in hypridle_pids():
            os.kill(pid, signal.SIGTERM)
        if CONFIG.read_text() != before:
            write_mango(CONFIG.read_text(), before)
        for path in written:
            path.unlink(missing_ok=True)
        for path, data in replaced.items():
            atomic_write(path, data, 0o755 if path.name == 'limux-idle' else 0o644)
        raise RuntimeError('activation failed; previous state restored') from failure
    print('Lock screen active: locks at 5 minutes idle and before sleep; Ctrl+Command+Q locks now.')


def rollback(manifest):
    state = owned_state(manifest)
    unknown = sorted(k for k, v in state.items() if v == 'unknown')
    if unknown:
        raise RuntimeError('owned files have unreviewed edits; refusing to remove: ' + ', '.join(unknown))
    for pid in hypridle_pids():
        os.kill(pid, signal.SIGTERM)
    before = CONFIG.read_text()
    if state['binding'] == 'active' or state['autostart'] == 'active':
        run('mmsg', 'get', 'version')
        write_mango(before, without_lines(before))
    for rel in manifest['files']:
        (HOME/rel).unlink(missing_ok=True)
    try:
        (HOME/'.config/hypr').rmdir()
    except OSError:
        pass
    marker().unlink(missing_ok=True)
    print('Lock screen removed: hypridle stopped, binding and autostart removed. Packages stay installed.')


def verify(manifest):
    candidate(manifest)
    state = owned_state(manifest)
    pids = hypridle_pids()
    summary = ('active' if set(state.values()) == {'active'} and len(pids) == 1 else
               'not active' if set(state.values()) == {'original'} and not pids else
               'mixed: ' + ', '.join(f'{k}={v}' for k, v in state.items()) + f', hypridle={len(pids)}')
    print(f'Approval pins verified. Lock screen {summary}.')
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('action', choices=['test', 'activate', 'verify', 'rollback'])
    action = parser.parse_args().action
    manifest = json.loads(MANIFEST.read_text())
    if action == 'verify':
        if verify(manifest) != 'active':
            raise SystemExit('Lock screen is not fully active.')
        return
    with (Path(os.environ['XDG_RUNTIME_DIR'])/'limux-lock-activation.lock').open('w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        {'test': test, 'activate': activate, 'rollback': rollback}[action](manifest)


if __name__ == '__main__':
    try:
        main()
    except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as exc:
        raise SystemExit(f'Lock screen: {exc}')
