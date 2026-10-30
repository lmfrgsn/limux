#!/usr/bin/env python3
"""Guarded Mako appearance activation. Behaviour lines stay in the user's config;
appearance moves to a generated include. Rollback restores the exact prior file."""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import tempfile
import tomllib
from mako import render

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT/'themes/recovery/mako.json'
APPEARANCE = {'font', 'background-color', 'text-color', 'border-color', 'border-size', 'border-radius',
              'padding', 'width', 'height', 'margin', 'outer-margin', 'progress-color', 'icons',
              'max-icon-size', 'icon-path', 'icon-location', 'icon-border-radius', 'markup', 'format',
              'text-alignment'}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def regular(path):
    if path.is_symlink() or not path.is_file() or path.stat().st_uid != os.getuid():
        raise RuntimeError(f'Expected an owned regular file: {path}')
    return path.read_bytes()


def sync_directory(path):
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def atomic_write(path, data):
    mode = path.stat().st_mode & 0o777 if path.exists() else 0o644
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


def include_line(style):
    if any(char in str(style) for char in '\n\r#'):
        raise RuntimeError('Unsupported appearance path')
    return f'include={style}'


def active_from(original, style):
    """Drop appearance lines everywhere; include the fragment at the end of the
    global section so the user's own sections still follow it."""
    lines = original.decode().split('\n')
    kept = [line for line in lines if line.split('=', 1)[0].strip() not in APPEARANCE or '=' not in line]
    first_section = next((i for i, line in enumerate(kept) if line.startswith('[')), len(kept))
    insert = first_section
    while insert > 0 and not kept[insert - 1].strip():
        insert -= 1
    kept.insert(insert, include_line(style))
    return '\n'.join(kept).encode()


def versions(config, style, manifest):
    before = regular(config)
    original = regular(ROOT/'themes/recovery'/manifest['recovery_file'])
    if digest(original) != manifest['original_sha256']:
        raise RuntimeError('Mako recovery copy failed its integrity check')
    active = active_from(original, style)
    if before not in (original, active):
        raise RuntimeError('Unknown Mako configuration; refusing to overwrite it')
    existing = regular(style) if style.exists() or style.is_symlink() else None
    if existing is not None and digest(existing) != manifest['baseline_sha256']:
        raise RuntimeError('Unknown Mako appearance file; refusing to overwrite or remove it')
    return before, existing, original, active


def candidate(manifest):
    data = render(tomllib.loads((ROOT/'themes/rhapsody.toml').read_text())).encode()
    if digest(data) != manifest['baseline_sha256']:
        raise RuntimeError('Generated Mako appearance differs from the pinned approved version')
    return data


def stage_validate(original, style_data):
    """Start a private Mako on its own bus; a parse error makes it exit at once."""
    with tempfile.TemporaryDirectory(prefix='limux-mako-') as folder:
        folder = Path(folder)
        config = folder/'config'
        if style_data is None:
            config.write_bytes(original)
        else:
            (folder/'rhapsody').write_bytes(style_data)
            config.write_bytes(active_from(original, folder/'rhapsody'))
        result = subprocess.run(['dbus-run-session', '--', 'timeout', '1.5', 'mako', '-c', str(config)],
                                capture_output=True, text=True, timeout=15)
        if result.returncode != 124:
            raise RuntimeError(f'Mako rejected the staged configuration: {result.stderr.strip()[:300]}')


def reload():
    subprocess.run(['makoctl', 'reload'], check=True, capture_output=True, timeout=10)


def transition(config, style, desired_config, desired_style):
    """Fragment before the include; include removed before the fragment.
    Any failure restores the exact prior bytes and reloads."""
    before = regular(config)
    old_style = regular(style) if style.exists() else None
    try:
        if desired_style is not None and old_style != desired_style:
            atomic_write(style, desired_style)
        if before != desired_config:
            atomic_write(config, desired_config)
        reload()
        if desired_style is None and style.exists():
            style.unlink()
            sync_directory(style.parent)
    except BaseException:
        if old_style is not None:
            atomic_write(style, old_style)
        atomic_write(config, before)
        if old_style is None:
            style.unlink(missing_ok=True)
            sync_directory(style.parent)
        try:
            reload()
        finally:
            raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['check', 'activate', 'rollback', 'verify'])
    args = parser.parse_args()
    manifest = json.loads(MANIFEST.read_text())
    installed = subprocess.run(['pacman', '-Q', 'mako'], capture_output=True, text=True).stdout
    if f"mako {manifest['mako_version']}-" not in installed:
        raise RuntimeError('Mako version changed; review options before activation')
    directory = Path(os.environ.get('XDG_CONFIG_HOME', str(Path.home()/'.config')))/'mako'
    config, style = directory/'config', directory/'rhapsody'
    before, old_style, original, active = versions(config, style, manifest)
    if args.action in ('check', 'verify'):
        data = candidate(manifest)
        stage_validate(original, data)
        on = before == active and old_style == data
        if args.action == 'verify' and not on:
            raise RuntimeError('Rhapsody Mako is not active on disk')
        print('Approval pin and staged Mako validation passed. On disk: ' +
              ('Rhapsody notifications.' if on else 'previous notifications.'))
        return
    desired_style = candidate(manifest) if args.action == 'activate' else None
    stage_validate(original, desired_style)
    runtime = Path(os.environ['XDG_RUNTIME_DIR'])
    with (runtime/'limux-mako-activation.lock').open('w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if versions(config, style, manifest)[:2] != (before, old_style):
            raise RuntimeError('Mako configuration changed during preflight')
        transition(config, style, active if desired_style is not None else original, desired_style)
    print('Activated Rhapsody notifications; Mako reloaded.' if desired_style is not None else
          'Restored the previous Mako configuration; Mako reloaded.')


if __name__ == '__main__':
    def interrupted(signum, frame):
        raise InterruptedError('Activation interrupted')
    signal.signal(signal.SIGTERM, interrupted)
    try:
        main()
    except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as exc:
        raise SystemExit(str(exc))
