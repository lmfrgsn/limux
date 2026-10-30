#!/usr/bin/env python3
"""Prepare/check and reversibly activate the reviewed Quiet Workspace Strip.

Run only from Foot in the active MangoWM session. The existing MangoWM startup
entry and upstream ~/.local/bin/mangobar binary remain in place.
"""
import argparse
import ctypes
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time

from importlib.util import module_from_spec, spec_from_file_location

ROOT = Path(__file__).resolve().parents[1]
HOME = Path.home()
UPSTREAM = HOME / '.local/bin/mangobar'
LAUNCHER = HOME / '.local/bin/limux-bar'
CONFIG = HOME / '.config/mangobar/config.jsonc'
CSS = HOME / '.config/mangobar/style.css'
MANGO = HOME / '.config/mango/config.conf'
PATCHED = HOME / '.local/libexec/limux/mangobar-0.2.2-quiet/mangobar'
STATE = HOME / '.local/state/limux/quiet-bar-activation'
EXPECTED = {
    'upstream': '36a5d8ec257ac5fe4183e655f1f88d97711b218ed02a6f70e1b4ed3fdc237d56',
    'launcher': '42343522012b965af0c8518e477ed4ac66c32dff33eac810c7978f31eef5ab6b',
    'config': '13d8cd1666d70a1beac55c358363af2be0f4305bfda6fec7b875ea830f049c48',
    'css': 'f82d060029411d566a2789351e4f3faca0def1ae29f43110d819cc5d7e015dc5',
    'mango': '37d07c20b8c25df2eca5a8b04c2c215d5a23a96745cb71e499e99894154598f5',
    'candidate_config': 'b906220cd7ac83704a3ce23ff558b1698813d0e3ee261c99361266bd8ba5a7c8',
    'candidate_css': '03c674d5acb12287503b9fd08b9adb6903e8c7feaaf083d11dc8f93db598ab7c',
}
OLD_LINE = "BINARY = HOME / '.local/bin/mangobar'"
NEW_LINE = "BINARY = HOME / '.local/libexec/limux/mangobar-0.2.2-quiet/mangobar'"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def checked_file(path, expected):
    if path.is_symlink() or not path.is_file() or digest(path.read_bytes()) != expected:
        raise RuntimeError(f'unexpected file; inspect before changing: {path}')


def atomic_write(path, data, mode=None):
    if path.exists() and (path.is_symlink() or not path.is_file()):
        raise RuntimeError(f'unsafe destination: {path}')
    path.parent.mkdir(parents=True, exist_ok=True)
    if mode is None:
        mode = path.stat().st_mode & 0o777 if path.exists() else 0o644
    fd, name = tempfile.mkstemp(prefix='.limux-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            os.fchmod(stream.fileno(), mode)
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
        directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        Path(name).unlink(missing_ok=True)


def candidate_launcher(original):
    text = original.decode()
    if text.count(OLD_LINE) != 1:
        raise RuntimeError('unexpected launcher binary declaration')
    return text.replace(OLD_LINE, NEW_LINE, 1).encode()


def require_session():
    lib = ctypes.CDLL('libwayland-client.so.0')
    lib.wl_display_connect.argtypes = [ctypes.c_char_p]
    lib.wl_display_connect.restype = ctypes.c_void_p
    lib.wl_display_disconnect.argtypes = [ctypes.c_void_p]
    display = lib.wl_display_connect(None)
    if not display:
        raise RuntimeError('Wayland unavailable; run from Foot in the active session')
    lib.wl_display_disconnect(display)


def startup_entry():
    # The complete current MangoWM config is hash-pinned. Its one startup entry
    # is preserved byte-for-byte through activation and rollback.
    checked_file(MANGO, EXPECTED['mango'])
    entries = [line.strip() for line in MANGO.read_text().splitlines()
               if line.strip().startswith(('exec=', 'exec_once='))
               and any(word in line for word in ('mangobar', 'limux-bar', 'waybar'))]
    expected = f'exec_once={HOME}/.local/bin/limux-bar start'
    if entries != [expected]:
        raise RuntimeError(f'unexpected bar startup entries: {entries}')
    # Reuse the existing broad duplicate scan, including user services.
    spec = spec_from_file_location('approved_bar_activation', ROOT / 'scripts/activate-mangobar.py')
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    module.startup_entries(HOME)


def managed_bar(binary):
    status = json.loads(subprocess.run([str(LAUNCHER), 'status'], check=True,
                                       capture_output=True, text=True).stdout)
    pids = status['mangobar']
    if len(pids) != 1 or pids[0] != status['managed_pid']:
        raise RuntimeError(f'expected exactly one managed bar, no previews: {status}')
    pid = pids[0]
    proc = Path('/proc') / str(pid)
    if proc.stat().st_uid != os.getuid() or (proc / 'exe').resolve() != binary.resolve():
        raise RuntimeError('bar executable or owner does not match expected launcher')
    argv = (proc / 'cmdline').read_bytes().split(b'\0')[:-1]
    expected = [str(binary), '-c', str(CONFIG), '-s', str(CSS)]
    if argv != [arg.encode() for arg in expected]:
        raise RuntimeError('bar arguments differ from the canonical configuration')


def existing_bar_or_none():
    status = json.loads(subprocess.run([str(LAUNCHER), 'status'], check=True,
                                       capture_output=True, text=True).stdout)
    pids = status['mangobar']
    if not pids and status['managed_pid'] is None:
        return None
    if len(pids) != 1 or pids[0] != status['managed_pid']:
        raise RuntimeError(f'unmanaged or duplicate bar during recovery: {status}')
    exe = (Path('/proc') / str(pids[0]) / 'exe').resolve()
    for binary in (UPSTREAM, PATCHED):
        if exe == binary.resolve():
            managed_bar(binary)
            return binary
    raise RuntimeError(f'unexpected running bar during recovery: {exe}')


def generate_candidate():
    spec = spec_from_file_location('quiet_bar', ROOT / 'scripts/quiet-bar.py')
    quiet = module_from_spec(spec)
    sys.path.insert(0, str(ROOT / 'scripts'))
    spec.loader.exec_module(quiet)
    output = quiet.render()
    config = (output / 'revised.jsonc').read_bytes()
    css = (output / 'revised.css').read_bytes()
    if digest(config) != EXPECTED['candidate_config'] or digest(css) != EXPECTED['candidate_css']:
        raise RuntimeError('preview output changed since visual approval')
    spec = spec_from_file_location('quiet_build', ROOT / 'scripts/quiet-mangobar-build.py')
    builder = module_from_spec(spec)
    spec.loader.exec_module(builder)
    binary = builder.build()
    if subprocess.run([str(binary), '-v'], check=True, capture_output=True,
                      text=True).stdout.strip() != 'mangobar 0.2.2':
        raise RuntimeError('unexpected patched Mangobar version')
    return config, css, binary.read_bytes()


def write_backup(original, candidate, binary_hash):
    STATE.parent.mkdir(parents=True, exist_ok=True)
    if STATE.exists():
        raise RuntimeError(f'activation state already exists: {STATE}; inspect or roll back')
    staged = Path(tempfile.mkdtemp(prefix='.quiet-bar-', dir=STATE.parent))
    try:
        for name, data in original.items():
            (staged / name).write_bytes(data)
        (staged / 'manifest.json').write_text(json.dumps({
            'original': {name: digest(data) for name, data in original.items()},
            'candidate': {name: digest(data) for name, data in candidate.items()},
            'binary': binary_hash,
        }, indent=2) + '\n')
        os.replace(staged, STATE)
    finally:
        if staged.exists():
            shutil.rmtree(staged)


def backup():
    manifest = json.loads((STATE / 'manifest.json').read_text())
    original = {name: (STATE / name).read_bytes() for name in ('config', 'css', 'launcher')}
    if any(digest(data) != manifest['original'][name] for name, data in original.items()):
        raise RuntimeError('rollback backup failed integrity check')
    return manifest, original


def refresh_and_verify(binary):
    subprocess.run([str(LAUNCHER), 'refresh'], check=True, timeout=25)
    time.sleep(1)
    managed_bar(binary)
    startup_entry()
    checked_file(UPSTREAM, EXPECTED['upstream'])


def activate():
    if STATE.exists():
        raise RuntimeError('activation state exists; run rollback before a new activation')
    for path, key in ((UPSTREAM, 'upstream'), (LAUNCHER, 'launcher'),
                      (CONFIG, 'config'), (CSS, 'css')):
        checked_file(path, EXPECTED[key])
    startup_entry()
    require_session()
    managed_bar(UPSTREAM)
    config, css, binary = generate_candidate()
    original = {'config': CONFIG.read_bytes(), 'css': CSS.read_bytes(),
                'launcher': LAUNCHER.read_bytes()}
    candidate = {'config': config, 'css': css,
                 'launcher': candidate_launcher(original['launcher'])}
    if PATCHED.exists():
        raise RuntimeError(f'candidate binary destination already exists: {PATCHED}')
    write_backup(original, candidate, digest(binary))
    try:
        atomic_write(PATCHED, binary, 0o755)
        atomic_write(CONFIG, config)
        atomic_write(CSS, css)
        atomic_write(LAUNCHER, candidate['launcher'])
        refresh_and_verify(PATCHED)
        for name, path in (('config', CONFIG), ('css', CSS), ('launcher', LAUNCHER)):
            if digest(path.read_bytes()) != digest(candidate[name]):
                raise RuntimeError(f'{name} changed during activation')
    except BaseException as failure:
        try:
            for name, path in (('config', CONFIG), ('css', CSS), ('launcher', LAUNCHER)):
                atomic_write(path, original[name])
            refresh_and_verify(UPSTREAM)
            if PATCHED.exists() and digest(PATCHED.read_bytes()) == digest(binary):
                PATCHED.unlink()
            shutil.rmtree(STATE)
        except BaseException as recovery:
            raise RuntimeError(f'activation failed; backup retained at {STATE}; recovery failed: {recovery}') from failure
        raise RuntimeError('activation failed; original bar restored') from failure
    print('Quiet Workspace Strip active; one managed bar and one startup entry verified.')


def rollback():
    if not STATE.exists():
        raise RuntimeError('no Quiet Workspace Strip activation state to roll back')
    manifest, original = backup()
    require_session()
    startup_entry()
    checked_file(UPSTREAM, EXPECTED['upstream'])
    if PATCHED.exists():
        checked_file(PATCHED, manifest['binary'])
    for name, path in (('config', CONFIG), ('css', CSS), ('launcher', LAUNCHER)):
        if path.is_symlink() or digest(path.read_bytes()) not in (manifest['candidate'][name],
                                                                   manifest['original'][name]):
            raise RuntimeError(f'{name} has unreviewed edits; refusing rollback overwrite')
    existing_bar_or_none()
    for name, path in (('config', CONFIG), ('css', CSS), ('launcher', LAUNCHER)):
        atomic_write(path, original[name])
    refresh_and_verify(UPSTREAM)
    PATCHED.unlink(missing_ok=True)
    try:
        PATCHED.parent.rmdir()
    except OSError:
        pass
    shutil.rmtree(STATE)
    print('Original Mangobar binary, CSS, config and launcher restored; one managed bar verified.')


def check():
    if STATE.exists():
        manifest, _ = backup()
        require_session()
        startup_entry()
        checked_file(PATCHED, manifest['binary'])
        for name, path in (('config', CONFIG), ('css', CSS), ('launcher', LAUNCHER)):
            checked_file(path, manifest['candidate'][name])
        managed_bar(PATCHED)
        print('Quiet Workspace Strip active; one managed bar and one startup entry.')
    else:
        for path, key in ((UPSTREAM, 'upstream'), (LAUNCHER, 'launcher'),
                          (CONFIG, 'config'), (CSS, 'css')):
            checked_file(path, EXPECTED[key])
        startup_entry()
        require_session()
        managed_bar(UPSTREAM)
        generate_candidate()
        print('Baseline healthy; pinned candidate builds. Activation remains pending.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['check', 'activate', 'rollback'])
    action = parser.parse_args().action
    runtime = Path(os.environ['XDG_RUNTIME_DIR'])
    with (runtime / 'limux-quiet-bar-activation.lock').open('w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        {'check': check, 'activate': activate, 'rollback': rollback}[action]()


if __name__ == '__main__':
    try:
        main()
    except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as exc:
        raise SystemExit(f'Quiet Workspace Strip: {exc}')
