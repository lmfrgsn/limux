#!/usr/bin/env python3
"""Guarded polkit authentication agent: one MangoWM autostart for polkit-gnome.

  activate  add the autostart and start the agent now
  verify    one agent running and exactly one autostart line
  rollback  stop the agent and remove the autostart

The GTK 3 dialog follows the Limux GTK theme and interface font. Run from Foot in
the desktop session; the package is installed separately.
"""
import argparse
import fcntl
import os
from pathlib import Path
import subprocess
import tempfile
import time

HOME = Path.home()
CONFIG = HOME/'.config/mango/config.conf'
AGENT = '/usr/lib/polkit-gnome/polkit-gnome-authentication-agent-1'
AUTOSTART = f'exec_once={AGENT}'
NAME = 'polkit-gnome-au'  # the kernel's 15-character process name


def run(*args):
    return subprocess.run(args, check=True, capture_output=True, text=True, timeout=12)


def agent_pids():
    found = subprocess.run(['pgrep', '-u', str(os.getuid()), '-x', NAME], capture_output=True, text=True)
    return [int(pid) for pid in found.stdout.split()]


def configured(text):
    lines = [line.strip() for line in text.splitlines() if not line.lstrip().startswith('#')]
    agents = [line for line in lines if line.startswith('exec') and 'polkit' in line]
    if agents and agents != [AUTOSTART]:
        raise RuntimeError('another polkit agent autostart exists; inspect the MangoWM config')
    return bool(agents)


def write_config(before, after):
    with tempfile.NamedTemporaryFile(mode='w', dir=CONFIG.parent, prefix='.polkit-', delete=False) as stream:
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


def activate():
    if not os.access(AGENT, os.X_OK):
        raise RuntimeError('polkit-gnome is not installed; run: sudo pacman -S --needed polkit-gnome')
    run('mmsg', 'get', 'version')
    before = CONFIG.read_text()
    if configured(before) and len(agent_pids()) == 1:
        print('Polkit agent already active.')
        return
    if agent_pids() and not configured(before):
        raise RuntimeError('a polkit agent is already running outside Limux; stop it first')
    if not configured(before):
        lines = before.splitlines(keepends=True)
        last = max(i for i, line in enumerate(lines) if line.startswith('exec_once='))
        lines.insert(last + 1, AUTOSTART + '\n')
        write_config(before, ''.join(lines))
    try:
        if not agent_pids():
            subprocess.Popen(['setsid', '-f', AGENT], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(1.5)
        if len(agent_pids()) != 1:
            raise RuntimeError('the polkit agent did not start')
    except BaseException:
        write_config(CONFIG.read_text(), before)
        raise
    print('Polkit agent active: admin actions now ask for your password in a dialog.')


def rollback():
    for pid in agent_pids():
        os.kill(pid, 15)
    before = CONFIG.read_text()
    if configured(before):
        run('mmsg', 'get', 'version')
        write_config(before, ''.join(line for line in before.splitlines(keepends=True) if line.strip() != AUTOSTART))
    print('Polkit agent stopped and its autostart removed. The package stays installed.')


def verify():
    state = configured(CONFIG.read_text()), len(agent_pids())
    summary = 'active' if state == (True, 1) else 'not active' if state == (False, 0) else f'mixed: autostart={state[0]}, agents={state[1]}'
    print(f'Polkit agent {summary}.')
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('action', choices=['activate', 'verify', 'rollback'])
    action = parser.parse_args().action
    if action == 'verify':
        if verify() != 'active':
            raise SystemExit('Polkit agent is not fully active.')
        return
    with (Path(os.environ['XDG_RUNTIME_DIR'])/'limux-polkit-activation.lock').open('w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        activate() if action == 'activate' else rollback()


if __name__ == '__main__':
    try:
        main()
    except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as exc:
        raise SystemExit(f'Polkit agent: {exc}')
