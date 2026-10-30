#!/usr/bin/env python3
"""Switch only Limux Commands' picker appearance via a reversible state marker."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts' / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


commands = load('limux_commands_appearance', 'limux-commands.py')
binding = load('limux_commands_binding', 'activate-commands.py')
STATE = commands.APPEARANCE_STATE
CANDIDATE_SHA256 = '036c640884eab51b1acf3addc371dac2c18d1177438496c0d5d2dcb2900931ea'
MARKER = f'neutral-v1 {CANDIDATE_SHA256}\n'.encode()


def marker(path=STATE):
    if not path.exists() and not path.is_symlink():
        return None
    if path.is_symlink() or not path.is_file() or path.stat().st_uid != os.getuid():
        raise RuntimeError('unexpected Commands appearance marker ownership')
    if path.stat().st_mode & 0o077:
        raise RuntimeError('Commands appearance marker must have mode 600')
    data = path.read_bytes()
    if not re.fullmatch(rb'neutral-v1 [0-9a-f]{64}\n', data):
        raise RuntimeError('unrecognized Commands appearance marker')
    return data


def preflight():
    if not binding.inspect(binding.CONFIG.read_text()):
        raise RuntimeError('Command+K binding is not the approved Commands invocation')
    approved_rofi = json.loads((ROOT / 'themes/recovery/rofi.json').read_text())['baseline_sha256']
    if hashlib.sha256(commands.THEME.read_bytes()).hexdigest() != approved_rofi:
        raise RuntimeError('base Rofi theme differs from the approved launcher')
    style = commands.preview_theme(candidate=True)
    if hashlib.sha256(style.encode()).hexdigest() != CANDIDATE_SHA256:
        raise RuntimeError('Commands candidate differs from the reviewed preview')
    result = subprocess.run(['rofi', '-theme', str(commands.THEME), '-theme-str', style,
                             '-dump-theme'], capture_output=True, text=True, timeout=15, check=True)
    if 'Parser error' in result.stderr or 'element selected.active' not in result.stdout:
        raise RuntimeError('Rofi did not resolve the candidate heading state')


def atomic_marker(path=STATE):
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    if path.parent.is_symlink():
        raise RuntimeError('Commands state directory must not be a symlink')
    fd, temporary = tempfile.mkstemp(prefix='.commands-appearance-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            os.fchmod(stream.fileno(), 0o600)
            stream.write(MARKER)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        sync_directory(path.parent)
    finally:
        Path(temporary).unlink(missing_ok=True)


def sync_directory(path):
    directory = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(directory)
    finally:
        os.close(directory)


def change(action, path=STATE):
    current = marker(path)
    if action == 'check':
        preflight()
        print('Commands appearance:', 'approved baseline' if current is None else
              'neutral candidate' if current == MARKER else 'older candidate marker')
        return
    lock = commands.picker_lock()
    if lock is None:
        raise RuntimeError('close the open Commands picker before changing appearance')
    try:
        current = marker(path)
        if action == 'rollback':
            if current is None:
                print('Already using approved Commands appearance')
                return
            path.unlink()
            sync_directory(path.parent)
            print('Approved Commands appearance restored')
            return
        preflight()
        if current is not None:
            if current != MARKER:
                raise RuntimeError('another Commands appearance marker is active')
            print('Neutral Commands appearance already active')
            return
        atomic_marker(path)
        try:
            if not commands.appearance_active(path):
                raise RuntimeError('Commands appearance activation did not verify')
        except BaseException:
            path.unlink(missing_ok=True)
            raise
        print('Neutral Commands appearance activated; Command+K binding unchanged')
    finally:
        os.close(lock)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['check', 'activate', 'rollback'])
    change(parser.parse_args().action)


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError,
            subprocess.TimeoutExpired) as exc:
        raise SystemExit(f'Commands appearance: {exc}')
