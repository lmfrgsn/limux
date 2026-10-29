#!/usr/bin/env python3
"""Guarded, reversible Limux Commands binding in the sole MangoWM config."""
import argparse
import fcntl
import os
from pathlib import Path
import subprocess
import tempfile

HOME = Path.home()
CONFIG = HOME / '.config/mango/config.conf'
COMMANDS = Path(__file__).resolve().parent / 'limux-commands.py'
LAUNCHER = 'bind=SUPER,space,spawn,rofi -show drun'
BINDING = f'bind=SUPER,k,spawn,/usr/bin/python3 {COMMANDS} preview'


def run(*args):
    return subprocess.run(args, check=True, capture_output=True, text=True, timeout=12)


def inspect(text):
    lines = [line.strip() for line in text.splitlines() if not line.lstrip().startswith('#')]
    if lines.count(LAUNCHER) != 1:
        raise RuntimeError('normal Command+Space launcher is not unique')
    related = [line for line in lines if line.startswith('bind=SUPER,k,')]
    if related and related != [BINDING]:
        raise RuntimeError('Command+K is already assigned to another command')
    if lines.count(BINDING) > 1:
        raise RuntimeError('duplicate Command+K binding')
    return bool(related)


def validate(text):
    with tempfile.NamedTemporaryFile(mode='w', dir=CONFIG.parent, prefix='.commands-', delete=False) as stream:
        stream.write(text)
        staged = Path(stream.name)
    try:
        run('mango', '-p', '-c', str(staged))
    finally:
        staged.unlink(missing_ok=True)


def atomic_write(text, mode):
    with tempfile.NamedTemporaryFile(mode='w', dir=CONFIG.parent, prefix='.commands-', delete=False) as stream:
        stream.write(text)
        staged = Path(stream.name)
    try:
        os.chmod(staged, mode)
        os.replace(staged, CONFIG)
    finally:
        staged.unlink(missing_ok=True)


def change(action):
    if CONFIG.is_symlink() or not CONFIG.is_file():
        raise RuntimeError('expected a regular MangoWM config')
    before = CONFIG.read_text()
    active = inspect(before)
    validate(before)
    if action == 'check':
        print('Command+K:', 'Limux Commands' if active else 'unassigned')
        return
    if action == 'activate' and active or action == 'rollback' and not active:
        print('Already in requested state')
        return
    # Refuse to change on-disk configuration when compositor reload cannot be verified.
    run('mmsg', 'get', 'version')
    if action == 'activate':
        after = before.replace(LAUNCHER + '\n', LAUNCHER + '\n' + BINDING + '\n', 1)
        if after == before:
            raise RuntimeError('launcher binding has unexpected formatting')
    else:
        after = before.replace(BINDING + '\n', '', 1)
    validate(after)
    mode = CONFIG.stat().st_mode & 0o777
    atomic_write(after, mode)
    try:
        run('mmsg', 'dispatch', 'reload_config')
        run('mmsg', 'get', 'version')
        if inspect(CONFIG.read_text()) != (action == 'activate'):
            raise RuntimeError('post-reload binding mismatch')
    except Exception:
        atomic_write(before, mode)
        try:
            run('mmsg', 'dispatch', 'reload_config')
        except Exception:
            pass
        raise
    print('Command+K activated' if action == 'activate' else 'Command+K removed')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['check', 'activate', 'rollback'])
    action = parser.parse_args().action
    if action == 'check':
        change(action)
        return
    lock = HOME / '.cache/limux-commands-activation.lock'
    lock.parent.mkdir(mode=0o700, exist_ok=True)
    with lock.open('w') as stream:
        fcntl.flock(stream, fcntl.LOCK_EX)
        change(action)


if __name__ == '__main__':
    try:
        main()
    except (OSError, RuntimeError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        raise SystemExit(f'limux-commands activation: {exc}')
