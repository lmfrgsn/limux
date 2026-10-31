#!/usr/bin/env python3
"""Activate or roll back only Rofi's existing theme, leaving behaviour intact."""
import argparse
import ctypes
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import tempfile
import tomllib
from rofi import THEME_CONFIGURATION, render

ROOT = Path(__file__).resolve().parents[1]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def regular(path):
    if path.is_symlink() or not path.is_file() or path.stat().st_uid != os.getuid():
        raise RuntimeError(f'Expected an owned regular file: {path}')
    return path.read_bytes()


def atomic_write(path, data):
    regular(path)
    fd, temporary = tempfile.mkstemp(prefix='.limux-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as f:
            os.fchmod(f.fileno(), path.stat().st_mode & 0o777)
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temporary, path)
        fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
    finally:
        Path(temporary).unlink(missing_ok=True)


def transition(path, desired, verify):
    previous = regular(path)
    if previous == desired:
        verify()
        return False
    try:
        atomic_write(path, desired)
        verify()
    except BaseException as failure:
        try:
            atomic_write(path, previous)
        except BaseException as recovery:
            raise RuntimeError(f'Activation failed and recovery could not restore the theme: {recovery}') from failure
        raise RuntimeError(f'Activation failed; prior live theme restored: {failure}') from failure
    return True


def dump(args):
    p = subprocess.run(['rofi', *args], check=True, capture_output=True, text=True, timeout=15)
    if 'Parser error' in p.stderr:
        raise RuntimeError(p.stderr.strip())
    return p.stdout


def theme_properties(text):
    # Native dump emits one property per line, with flat named theme blocks.
    blocks = re.findall(r'(?m)^([^\n{}]+) \{\n(.*?)^\}', text, re.S)
    if not blocks:
        raise RuntimeError('No theme properties in native Rofi dump')
    return {name: tuple(sorted(line.strip() for line in body.splitlines() if line.strip()))
            for name, body in blocks}


def functional_config(text):
    # The picker theme owns only how launcher entries are shown and searched.
    # Rofi prints unset defaults as /* key: value; */ comments; match both forms.
    return '\n'.join(line for line in text.splitlines() if not line.startswith('@theme ')
                     and line.strip().lstrip('/*').strip().split(':', 1)[0] not in THEME_CONFIGURATION)


def require_session():
    lib = ctypes.CDLL('libwayland-client.so.0')
    lib.wl_display_connect.argtypes = [ctypes.c_char_p]
    lib.wl_display_connect.restype = ctypes.c_void_p
    lib.wl_display_disconnect.argtypes = [ctypes.c_void_p]
    display = lib.wl_display_connect(None)
    if not display:
        raise RuntimeError('Cannot reach Wayland; no live changes. Run this command from Foot.')
    lib.wl_display_disconnect(display)


def require_closed():
    result = subprocess.run(['pgrep', '-u', str(os.getuid()), '-x', 'rofi'], capture_output=True)
    if result.returncode != 1:
        raise RuntimeError('Close any open Rofi before activation/rollback (or pgrep failed).')


def payload(action, manifest):
    recovery = ROOT/'themes/recovery'
    old = (recovery/'rofi-before-rhapsody.rasi').read_bytes()
    if digest(old) != manifest['rollback_sha256']:
        raise RuntimeError('Recovery theme differs from the versioned manifest')
    if digest((recovery/'rofi-search.svg').read_bytes()) != manifest['search_icon_sha256']:
        raise RuntimeError('Recovery icon differs from the versioned manifest')
    if action == 'restore-original':
        return old  # Recovery must work even if future tokens/adapter drift.
    if action == 'rollback':
        previous = (recovery/manifest['previous_file']).read_bytes()
        if digest(previous) != manifest['previous_sha256']:
            raise RuntimeError('Previous Rhapsody theme differs from the versioned manifest')
        return previous
    new = render(tomllib.loads((ROOT/'themes/rhapsody.toml').read_text())).encode()
    if digest(new) != manifest['baseline_sha256']:
        raise RuntimeError('Generated theme differs from the approved picker; refusing activation')
    return new


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['check', 'activate', 'rollback', 'restore-original'])
    args = parser.parse_args()
    home = Path.home()
    config = home/'.config/rofi/config.rasi'
    live = home/'.config/rofi/charcoal.rasi'
    icon = home/'.config/rofi/assets/search.svg'
    manifest = json.loads((ROOT/'themes/recovery/rofi.json').read_text())
    desired = payload(args.action, manifest)
    if digest(regular(config)) != manifest['config_sha256']:
        raise RuntimeError('Rofi functional config changed; review before activation')
    if digest(regular(icon)) != manifest['search_icon_sha256']:
        raise RuntimeError('Rollback icon changed/missing; review the versioned recovery asset')
    before = regular(live)
    if digest(before) not in (manifest['baseline_sha256'], manifest['previous_sha256'], manifest['rollback_sha256']):
        raise RuntimeError('Unknown live theme; preserve/review it before activation')
    mango = home/'.config/mango/config.conf'
    if 'bind=SUPER,space,spawn,rofi -show drun' not in regular(mango).decode().splitlines():
        raise RuntimeError('Expected Command+Space launcher binding is absent')
    protected = [config, icon, mango, home/'.config/mangobar/style.css',
                 home/'.config/mangobar/config.jsonc', home/'.config/foot/foot.ini']
    hashes = {p: digest(regular(p)) for p in protected}
    current_function = functional_config(dump(['-dump-config']))
    explicit_function = functional_config(dump(['-config', str(config), '-dump-config']))
    if current_function != explicit_function:
        raise RuntimeError('Default Rofi is loading a different functional config')
    current_theme = theme_properties(dump(['-dump-theme']))
    if current_theme != theme_properties(dump(['-config', str(config), '-theme', str(live), '-dump-theme'])):
        raise RuntimeError('Default launcher does not resolve the expected live theme')
    with tempfile.TemporaryDirectory(prefix='limux-rofi-') as temporary:
        stage = Path(temporary)/'theme.rasi'
        stage.write_bytes(desired)
        expected = theme_properties(dump(['-config', str(config), '-theme', str(stage), '-dump-theme']))
        if functional_config(dump(['-config', str(config), '-theme', str(stage), '-dump-config'])) != current_function:
            raise RuntimeError('Staged theme changes Rofi functionality')
        if args.action == 'check':
            state = {manifest['baseline_sha256']: 'Limux picker', manifest['previous_sha256']: 'previous graphite Limux picker',
                     manifest['rollback_sha256']: 'pre-Rhapsody theme'}[digest(before)]
            print(f'Native syntax, approved hash, default launcher and preserved config verified. Live: {state}.')
            print('Search/navigation/Enter/Escape bindings preserved; interactive checks require the desktop.')
            return
        require_session()
        require_closed()
        runtime = Path(os.environ['XDG_RUNTIME_DIR'])
        with (runtime/'limux-rofi-activation.lock').open('w') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            require_closed()
            if regular(live) != before or any(digest(regular(p)) != h for p, h in hashes.items()):
                raise RuntimeError('Live files changed during preflight')

            def verify():
                if regular(live) != desired:
                    raise RuntimeError('Live theme does not match selected version')
                if theme_properties(dump(['-dump-theme'])) != expected:
                    raise RuntimeError('Normal launcher does not resolve the selected styling')
                if functional_config(dump(['-dump-config'])) != current_function:
                    raise RuntimeError('Functional settings changed')
                if any(digest(regular(p)) != h for p, h in hashes.items()):
                    raise RuntimeError('Protected configuration changed')

            changed = transition(live, desired, verify)
    print(('Activated' if changed else 'Already using') + {'rollback': ' the previous graphite Limux picker.',
          'restore-original': ' the pre-Rhapsody launcher.', 'activate': ' the approved Limux picker.'}[args.action])
    print('Command+Space uses it normally. Check search, Up/Down, Escape, then reopen and launch an app with Enter.')


if __name__ == '__main__':
    def interrupted(signum, frame):
        raise InterruptedError('Activation interrupted')
    signal.signal(signal.SIGTERM, interrupted)
    try:
        main()
    except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as exc:
        raise SystemExit(str(exc))
