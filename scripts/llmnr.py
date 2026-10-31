#!/usr/bin/env python3
"""Limux name lookups: turn off LLMNR in systemd-resolved. LLMNR asks the whole
local network to name a host DNS could not, and any machine there may answer,
which shared Wi-Fi makes easy to abuse. mDNS (.local names) and DNS are unchanged.

  check     show the drop-in state and whether LLMNR is on
  activate  (sudo) install the drop-in and reload systemd-resolved
  verify    the drop-in is in place and resolved reports LLMNR off
  rollback  (sudo) remove the drop-in and reload systemd-resolved
"""
import argparse
import os
from pathlib import Path
import subprocess
import tempfile

DROPIN = Path('/etc/systemd/resolved.conf.d/limux-no-llmnr.conf')
CONTENT = ('# Limux (~/limux/scripts/llmnr.py): no LLMNR name lookups on the local network.\n'
           '[Resolve]\nLLMNR=no\n')


def state():
    if not DROPIN.exists():
        return 'original'
    if DROPIN.is_symlink() or DROPIN.read_text() != CONTENT:
        raise RuntimeError(f'{DROPIN} has edits Limux did not make; inspect it')
    return 'active'


def llmnr_on():
    out = subprocess.run(['resolvectl', 'status'], capture_output=True, text=True, timeout=10).stdout
    protocols = next((line for line in out.splitlines() if 'Protocols:' in line), '')
    if 'LLMNR' not in protocols:
        raise RuntimeError('resolvectl did not report the LLMNR setting')
    return '+LLMNR' in protocols


def reload():
    subprocess.run(['systemctl', 'reload', 'systemd-resolved'], check=True, capture_output=True, timeout=20)


def require_root():
    if os.geteuid() != 0:
        raise RuntimeError('this needs root: run it with sudo')


def activate():
    require_root()
    if state() == 'active' and not llmnr_on():
        print('LLMNR already off.')
        return
    DROPIN.parent.mkdir(mode=0o755, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix='.limux-', dir=DROPIN.parent)
    try:
        with os.fdopen(fd, 'w') as stream:
            os.fchmod(stream.fileno(), 0o644)
            stream.write(CONTENT)
        os.replace(name, DROPIN)
    finally:
        Path(name).unlink(missing_ok=True)
    try:
        reload()
        if llmnr_on():
            raise RuntimeError('resolved still reports LLMNR on')
    except BaseException:
        DROPIN.unlink(missing_ok=True)
        reload()
        raise
    print('LLMNR off. DNS and .local (mDNS) names work as before.')


def rollback():
    require_root()
    state()
    DROPIN.unlink(missing_ok=True)
    try:
        DROPIN.parent.rmdir()
    except OSError:
        pass
    reload()
    print("LLMNR back to systemd-resolved's default (on).")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('action', choices=['check', 'activate', 'verify', 'rollback'])
    action = parser.parse_args().action
    if action in ('check', 'verify'):
        now, on = state(), llmnr_on()
        print(f'LLMNR {"on" if on else "off"}; Limux drop-in {now}.')
        if action == 'verify' and (now, on) != ('active', False):
            raise SystemExit(1)
    else:
        activate() if action == 'activate' else rollback()


if __name__ == '__main__':
    try:
        main()
    except (OSError, RuntimeError, subprocess.SubprocessError) as exc:
        raise SystemExit(f'LLMNR: {exc}')
