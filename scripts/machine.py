#!/usr/bin/env python3
"""Limux machine files: the hand-maintained configuration, helpers and system files
this MacBookPro15,1 depends on, tracked under machine/ at their real paths.

Generated Rhapsody outputs are not tracked here; their activation scripts recreate them.
Private snippets, backups, fstab, built binaries and third-party audio data are excluded.

  status   compare the live machine with the repository (read-only)
  capture  copy changed live files into the repository for review and commit
  restore  copy repository files to a fresh machine; never replaces a differing file
"""
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
STORE = ROOT/'machine'

# Paths relative to $HOME.
HOME_FILES = (
    '.config/mango/config.conf',
    '.config/foot/foot.ini',
    '.config/mako/config',
    '.config/hypr/hyprlock.conf',
    '.config/hypr/hypridle.conf',
    '.config/rofi/config.rasi',
    '.config/mimeapps.list',
    '.config/pipewire/t2-151-speakers.json',
    '.config/pipewire/t2-151-speakers-locked.json',
    '.config/wireplumber/wireplumber.conf.d/51-t2-151-speaker-dsp.conf',
    '.config/systemd/user/t2-speaker-mute.service',
    '.local/bin/limux-bar',
    '.local/bin/mango-notifications',
    '.local/bin/mango-screenshot',
    '.local/bin/limux-night-light',
    '.local/bin/limux-idle',
    '.local/bin/t2-hardware-control',
    '.local/bin/setup-t2-hardware',
    '.local/bin/finish-t2-audio',
    '.local/bin/enable-t2-speakers',
    '.local/bin/verify-t2-hardware',
    '.local/bin/test-t2-speakers',
    '.local/bin/install-limux-mangobar',
    '.local/bin/finish-desktop-setup',
    '.local/bin/finish-rofi-redesign',
    '.local/share/limux/mangobar/capacity-volume.patch',
    '.local/share/limux/mangobar/wifi-status.py',
    '.local/share/t2-hardware-setup/README.md',
    '.local/share/t2-hardware-setup/build-speaker-dsp.sh',
    '.local/share/t2-hardware-setup/configure-dsp.py',
    '.local/share/t2-hardware-setup/initialize-speakers.py',
    '.local/share/t2-hardware-setup/measure-test-output.py',
    '.local/share/t2-hardware-setup/speaker-quarantine.conf',
    '.local/share/t2-hardware-setup/test-stream-mutes.py',
)
# Absolute paths, owned by root.
SYSTEM_FILES = (
    '/etc/default/grub',
    '/etc/pacman.conf',
    '/etc/mkinitcpio.d/linux-t2.preset',
    '/etc/tiny-dfr/config.toml',
    '/etc/t2fand.conf',
    '/etc/udev/rules.d/90-t2-backlight-access.rules',
    '/etc/systemd/system/limux-touchbar-recover.service',
    '/usr/local/sbin/limux-touchbar-recover',
)
SYSTEM_UNITS = ('NetworkManager.service', 'bluetooth.service', 't2fanrd.service', 'tiny-dfr.service',
                'limux-touchbar-recover.service', 'systemd-resolved.service')
USER_UNITS = ('pipewire.socket', 'pipewire-pulse.socket', 'pipewire.service', 'pipewire-pulse.service',
              'wireplumber.service', 't2-speaker-mute.service')
PACKAGES = STORE/'packages.txt'


def entries(home=None, system=None):
    """Yield (live path, repository path, is_system) for every tracked file."""
    home = Path(home or os.environ.get('LIMUX_MACHINE_HOME') or Path.home())
    system = Path(system or os.environ.get('LIMUX_MACHINE_ROOT') or '/')
    for rel in HOME_FILES:
        yield home/rel, STORE/'home'/rel, False
    for path in SYSTEM_FILES:
        yield system/path.lstrip('/'), STORE/'system'/path.lstrip('/'), True


def compare(live, stored):
    if live.is_symlink() or (live.exists() and not live.is_file()):
        return 'unsupported'
    if not live.exists():
        return 'missing-live' if stored.exists() else 'missing'
    if not stored.exists():
        return 'untracked'
    same = live.read_bytes() == stored.read_bytes() and executable(live) == executable(stored)
    return 'same' if same else 'differs'


def executable(path):
    return bool(path.stat().st_mode & 0o111)


def copy(source, target):
    """Atomic copy keeping the executable bit; never follows a symlinked target."""
    if target.is_symlink():
        raise RuntimeError(f'refusing to replace symlink {target}')
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix='.limux-', dir=target.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(source.read_bytes())
            os.fchmod(stream.fileno(), 0o755 if executable(source) else 0o644)
        os.replace(name, target)
    finally:
        Path(name).unlink(missing_ok=True)


def explicit_packages():
    return subprocess.run(['pacman', '-Qqe'], capture_output=True, text=True, check=True).stdout


def units(user):
    command = ['systemctl', *(['--user'] if user else []), 'is-enabled', *(USER_UNITS if user else SYSTEM_UNITS)]
    result = subprocess.run(command, capture_output=True, text=True)
    names = USER_UNITS if user else SYSTEM_UNITS
    return dict(zip(names, result.stdout.split()))


def status(home=None, system=None, live_checks=True):
    problems = []
    for live, stored, _ in entries(home, system):
        state = compare(live, stored)
        if state != 'same':
            problems.append(f'{state}: {live}')
    if live_checks:
        if not PACKAGES.exists() or PACKAGES.read_text() != explicit_packages():
            problems.append('differs: explicit package list (pacman -Qqe)')
        for user in (False, True):
            for unit, state in units(user).items():
                if state != 'enabled':
                    problems.append(f'{state}: {"user " if user else ""}unit {unit}')
    return problems


def capture(home=None, system=None):
    changed = []
    for live, stored, _ in entries(home, system):
        state = compare(live, stored)
        if state in ('untracked', 'differs'):
            copy(live, stored)
            changed.append(stored.relative_to(ROOT))
        elif state in ('missing-live', 'unsupported'):
            raise RuntimeError(f'{state}: {live}; nothing captured from it')
    packages = explicit_packages()
    if not PACKAGES.exists() or PACKAGES.read_text() != packages:
        PACKAGES.parent.mkdir(parents=True, exist_ok=True)
        PACKAGES.write_text(packages)
        changed.append(PACKAGES.relative_to(ROOT))
    return changed


def restore(home=None, system=None):
    """Copy home files that are missing; list the sudo steps for system files."""
    restored, conflicts, pending = [], [], []
    for live, stored, is_system in entries(home, system):
        state = compare(live, stored)
        if state in ('differs', 'unsupported'):
            conflicts.append(live)
        elif state == 'missing-live':
            if is_system:
                pending.append((stored, live))
            else:
                copy(stored, live)
                restored.append(live)
    return restored, conflicts, pending


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('action', choices=['status', 'capture', 'restore'])
    action = parser.parse_args().action
    if action == 'status':
        problems = status()
        print('\n'.join(problems) if problems else 'Live machine matches the repository.')
        sys.exit(1 if problems else 0)
    if action == 'capture':
        changed = capture()
        print('\n'.join(f'captured: {p}' for p in changed) if changed else 'Nothing to capture.')
        if changed:
            print('Review with `git diff` before committing; never commit private data.')
        return
    restored, conflicts, pending = restore()
    for path in restored:
        print(f'restored: {path}')
    for path in conflicts:
        print(f'left unchanged (differs from repository; review by hand): {path}')
    for stored, live in pending:
        mode = '755' if executable(stored) else '644'
        print(f'sudo install -D -m{mode} {stored} {live}')
    if pending:
        print('Run the sudo lines above to restore system files, then enable the units listed in docs/machine.md.')


if __name__ == '__main__':
    try:
        main()
    except (OSError, RuntimeError, subprocess.SubprocessError) as exc:
        raise SystemExit(f'Limux machine: {exc}')
