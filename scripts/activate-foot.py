#!/usr/bin/env python3
"""Guarded Foot appearance activation; no running terminals are restarted."""
import argparse
import ctypes
import fcntl
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import tempfile
import tomllib
from foot import render

ROOT = Path(__file__).resolve().parents[1]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def regular(path):
    if path.is_symlink() or not path.is_file() or path.stat().st_uid != os.getuid():
        raise RuntimeError(f'Expected an owned regular file: {path}')
    return path.read_bytes()


def atomic_write(path, data):
    if path.exists() or path.is_symlink():
        regular(path)
    mode = path.stat().st_mode & 0o777 if path.exists() else 0o600
    fd, name = tempfile.mkstemp(prefix='.limux-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            os.fchmod(stream.fileno(), mode)
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
        sync_directory(path.parent)
    finally:
        Path(name).unlink(missing_ok=True)


def sync_directory(path):
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def native(config):
    subprocess.run(['foot', '-C', '-c', str(config)], check=True, capture_output=True, timeout=15)


def require_session():
    lib = ctypes.CDLL('libwayland-client.so.0')
    lib.wl_display_connect.argtypes = [ctypes.c_char_p]
    lib.wl_display_connect.restype = ctypes.c_void_p
    lib.wl_display_disconnect.argtypes = [ctypes.c_void_p]
    display = lib.wl_display_connect(None)
    if not display:
        raise RuntimeError('Cannot reach Wayland; no live changes. Run from Foot after the shell review.')
    lib.wl_display_disconnect(display)


def include_line(style):
    # Native paths are unquoted; reject ambiguous INI input.
    if any(char in str(style) for char in '\n\r#'):
        raise RuntimeError('Unsupported appearance path')
    return f'include={style}\n'.encode()


def versions(config, style, manifest):
    """Recover known original bytes without importing functional config into Git."""
    before = regular(config)
    line = manifest['original_font_line'].encode()
    include = include_line(style)
    if digest(before) == manifest['original_config_sha256']:
        original = before
    elif before.count(include) == 1:
        original = before.replace(include, line, 1)
        if digest(original) != manifest['original_config_sha256']:
            raise RuntimeError('Foot configuration changed; review before activation/rollback')
    else:
        raise RuntimeError('Unknown Foot configuration; refusing to overwrite it')
    if original.count(line) != 1:
        raise RuntimeError('Expected one original font definition')
    active = original.replace(line, include, 1)
    existing = regular(style) if style.exists() or style.is_symlink() else None
    if existing is not None and digest(existing) != manifest['baseline_sha256']:
        raise RuntimeError('Unknown appearance file; refusing to overwrite/remove it')
    if before == active and existing is None:
        # Rollback can still repair a missing include; activation can reinstall it.
        pass
    return before, existing, original, active


def candidate(manifest):
    data = render(tomllib.loads((ROOT/'themes/rhapsody.toml').read_text())).encode()
    if digest(data) != manifest['baseline_sha256']:
        raise RuntimeError('Generated Foot appearance differs from approved 5cf323e')
    return data


def stage_validate(original, style_data, manifest):
    with tempfile.TemporaryDirectory(prefix='limux-foot-') as folder:
        folder = Path(folder)
        config, style = folder/'foot.ini', folder/'rhapsody.ini'
        if style_data is not None:
            style.write_bytes(style_data)
            config.write_bytes(original.replace(manifest['original_font_line'].encode(), include_line(style), 1))
        else:
            config.write_bytes(original)
        native(config)


def transition(config, style, original, active, desired_style, verify):
    """Write dependency before include; remove include before dependency.

    Known intermediate states are accepted on retry after power loss/SIGKILL.
    Caught failures restore exact prior bytes; no persistent backup files.
    """
    before = regular(config)
    old_style = regular(style) if style.exists() else None
    desired_config = active if desired_style is not None else original
    try:
        if desired_style is not None and old_style != desired_style:
            atomic_write(style, desired_style)
        if before != desired_config:
            atomic_write(config, desired_config)
        verify(desired_config)
        if desired_style is None and style.exists():
            style.unlink()
            sync_directory(style.parent)
    except BaseException:
        # Restore the original dependency first if it existed.
        if old_style is not None:
            atomic_write(style, old_style)
        atomic_write(config, before)
        if old_style is None:
            style.unlink(missing_ok=True)
            sync_directory(style.parent)
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['check', 'activate', 'rollback', 'verify'])
    args = parser.parse_args()
    directory = Path(os.environ.get('XDG_CONFIG_HOME', str(Path.home()/'.config')))/'foot'
    config, style = directory/'foot.ini', directory/'rhapsody.ini'
    manifest = json.loads((ROOT/'themes/recovery/foot.json').read_text())
    version = subprocess.check_output(['foot', '--version'], text=True)
    if f"foot version: {manifest['foot_version']} " not in version:
        raise RuntimeError('Foot version changed; review defaults and recovery compatibility')
    before, old_style, original, active = versions(config, style, manifest)
    # Rollback deliberately does not read or render current theme tokens.
    desired = None if args.action == 'rollback' else candidate(manifest)
    stage_validate(original, None, manifest)
    if desired is not None:
        stage_validate(original, desired, manifest)
    if args.action in ('check', 'verify'):
        if args.action == 'verify':
            if before != active or old_style != desired:
                raise RuntimeError('Approved Rhapsody Foot is not active on disk')
            native(config)
        state = 'Rhapsody' if before == active and old_style else 'previous styling (or recoverable incomplete activation)'
        print(f'Native syntax and approval/recovery checks passed. On disk: {state}.')
        print('New Foot processes read this config; existing windows/servers keep their current appearance.')
        return
    require_session()
    if args.action == 'activate':
        font = tomllib.loads((ROOT/'themes/rhapsody.toml').read_text())['foot']['font']
        family = subprocess.check_output(['fc-match', '-f', '%{family}', font], text=True)
        if font not in family.split(','):
            raise RuntimeError('Approved font unavailable; refusing silent fallback')
    runtime = Path(os.environ['XDG_RUNTIME_DIR'])
    with (runtime/'limux-foot-activation.lock').open('w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        current = versions(config, style, manifest)
        if current[:2] != (before, old_style):
            raise RuntimeError('Foot configuration changed during preflight')
        def verify(expected):
            if regular(config) != expected:
                raise RuntimeError('Live Foot configuration differs from staged bytes')
            if desired is not None and regular(style) != desired:
                raise RuntimeError('Live appearance differs from approved bytes')
            native(config)
        transition(config, style, original, active, desired, verify)
    print('Restored previous Foot styling.' if args.action == 'rollback' else 'Activated approved Rhapsody Foot styling.')
    print('Open a NEW normal Foot window to use it. No running terminal or server was restarted.')


if __name__ == '__main__':
    def interrupted(signum, frame):
        raise InterruptedError('Activation interrupted')
    signal.signal(signal.SIGTERM, interrupted)
    try:
        main()
    except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as exc:
        raise SystemExit(str(exc))
