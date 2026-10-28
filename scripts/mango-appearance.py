#!/usr/bin/env python3
"""Check/preview/activate/roll back only MangoWM's owned appearance values."""
import argparse
from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import tomllib
import uuid
from mango import extract, merge, render, values

ROOT = Path(__file__).resolve().parents[1]
LIVE = Path.home()/'.config/mango/config.conf'
STATE = Path(os.environ.get('XDG_STATE_HOME', Path.home()/'.local/state'))/'limux/mango-appearance'


def read_live():
    if LIVE.is_symlink() or not LIVE.is_file() or LIVE.stat().st_uid != os.getuid():
        raise RuntimeError('Expected an owned regular MangoWM config')
    return LIVE.read_bytes()


def atomic(path, data, mode=0o600):
    fd, temporary = tempfile.mkstemp(prefix='.limux-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as f:
            os.fchmod(f.fileno(), mode)
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


def native_check(data):
    # Complete merged config is an ephemeral validation input, never a second
    # active config or a repository snapshot of machine-specific functionality.
    with tempfile.TemporaryDirectory(prefix='limux-mango-check-') as directory:
        path = Path(directory)/'config.conf'
        path.write_bytes(data)
        subprocess.run(['mango', '-p', '-c', str(path)], check=True, capture_output=True, timeout=15)


def ipc(*args):
    r = subprocess.run(['mmsg', *args], check=True, capture_output=True, text=True, timeout=10)
    if '"error"' in r.stdout.lower() or '"success":false' in r.stdout.lower().replace(' ', ''):
        raise RuntimeError(f'Mango IPC rejected request: {r.stdout}')
    return r.stdout


def session(version):
    if version not in ipc('get', 'version'):
        raise RuntimeError('Unexpected running MangoWM version; review before preview')
    p = subprocess.run(['pgrep', '-u', str(os.getuid()), '-x', 'mango'], capture_output=True, text=True)
    pids = p.stdout.split()
    if p.returncode != 0 or len(pids) != 1:
        raise RuntimeError('Expected exactly one existing MangoWM process')
    argv = (Path('/proc')/pids[0]/'cmdline').read_bytes().split(b'\0')[:-1]
    if b'-c' in argv:
        i = argv.index(b'-c')
        if i+1 == len(argv) or Path(os.fsdecode(argv[i+1])).resolve() != LIVE.resolve():
            raise RuntimeError('Running MangoWM uses a different configuration')
    elif Path(os.environ.get('XDG_CONFIG_HOME', Path.home()/'.config')).resolve() != LIVE.parent.parent.resolve():
        raise RuntimeError('Unexpected default configuration directory')


def reload_config():
    ipc('dispatch', 'reload_config')
    ipc('get', 'version')


@contextmanager
def locked():
    STATE.mkdir(parents=True, exist_ok=True, mode=0o700)
    with (STATE/'operation.lock').open('w') as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        yield


def restore(record):
    current = read_live()
    # Preserve nonvisual edits made during a preview. Refuse concurrent visual
    # edits rather than overwriting someone else's new appearance decisions.
    if extract(current) not in (record['before'], record['after']):
        raise RuntimeError('Visual settings changed concurrently; journal retained for review')
    restored = merge(current, record['before'])
    native_check(restored)
    if read_live() != current:
        raise RuntimeError('Config changed during restoration validation')
    atomic(LIVE, restored, LIVE.stat().st_mode & 0o777)
    reload_config()
    (STATE/'pending.json').unlink(missing_ok=True)


def watchdog(identifier, seconds):
    time.sleep(seconds)
    with locked():
        pending = STATE/'pending.json'
        if pending.exists():
            record = json.loads(pending.read_text())
            if record['id'] == identifier:
                restore(record)


def apply(before, after, seconds=None):
    pending = STATE/'pending.json'
    if pending.exists():
        raise RuntimeError('An unfinished operation exists. Run rollback first.')
    if merge(after, extract(before)) != before:
        raise RuntimeError('Refusing changes outside the 16 owned appearance values')
    native_check(after)
    if read_live() != before:
        raise RuntimeError('Config changed during preflight')
    record = {'id': uuid.uuid4().hex, 'before': extract(before), 'after': extract(after)}
    atomic(pending, (json.dumps(record, indent=2)+'\n').encode())
    try:
        # Arm independent restoration before replacing live bytes. Survives
        # terminal closure/SIGKILL of the preview parent. Only owned values are
        # journalled; no full config backups or recurring startup processes.
        with (STATE/'watchdog.log').open('w') as log:
            subprocess.Popen([sys.executable, str(Path(__file__).resolve()), '_watchdog',
                              record['id'], str((seconds or 0)+8)],
                             stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        atomic(LIVE, after, LIVE.stat().st_mode & 0o777)
        reload_config()
        if read_live() != after:
            raise RuntimeError('Config changed after replacement')
        if seconds is None:
            pending.unlink()
    except BaseException:
        restore(record)
        raise
    return record


def main():
    if len(sys.argv) == 4 and sys.argv[1] == '_watchdog':
        watchdog(sys.argv[2], int(sys.argv[3]))
        return
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['check', 'verify', 'preview', 'activate', 'rollback'])
    parser.add_argument('--seconds', type=int, default=30)
    args = parser.parse_args()
    if not 10 <= args.seconds <= 60:
        parser.error('preview duration must be 10–60 seconds')
    manifest = json.loads((ROOT/'themes/recovery/mango.json').read_text())
    if args.action == 'rollback':
        # Disk restoration is allowed even if compositor access is lost; a
        # failed reload retains the journal for retry from the desktop session.
        with locked():
            pending = STATE/'pending.json'
            if pending.exists():
                restore(json.loads(pending.read_text()))
            else:
                current = read_live()
                if extract(current) not in (manifest['rollback'], manifest['candidate_values']):
                    raise RuntimeError('Unknown live appearance; refusing rollback overwrite')
                restored = merge(current, manifest['rollback'])
                native_check(restored)
                if read_live() != current:
                    raise RuntimeError('Config changed during rollback validation')
                atomic(LIVE, restored, LIVE.stat().st_mode & 0o777)
                reload_config()
        print('Previous appearance restored; nonvisual settings untouched.')
        return
    t = tomllib.loads((ROOT/'themes/rhapsody.toml').read_text())
    fragment = render(t)
    sha = hashlib.sha256(fragment.encode()).hexdigest()
    if sha != manifest['candidate_sha256']:
        raise RuntimeError('Candidate changed; review manifest before preview')
    if args.action == 'activate' and manifest['approved_sha256'] != sha:
        raise RuntimeError('Permanent activation is locked: candidate awaits user visual approval.')
    current = read_live()
    if extract(current) not in (manifest['rollback'], values(t)):
        raise RuntimeError('Unknown live appearance; preserve/review it before replacement')
    candidate = merge(current, values(t))
    native_check(current)
    native_check(candidate)
    version = subprocess.run(['mango', '-v'], capture_output=True, text=True, check=True).stdout
    if manifest['version'] not in version:
        raise RuntimeError('Installed MangoWM version changed; review compatibility')
    out = ROOT/'build/mango-candidate1'
    out.mkdir(parents=True, exist_ok=True)
    (out/'appearance.conf').write_text(fragment)
    if args.action in ('check', 'verify'):
        active = extract(current) == values(t) and manifest['approved_sha256'] == sha
        if args.action == 'verify':
            if not active:
                raise RuntimeError('Live configuration does not contain the approved appearance')
            session(manifest['version'])
        state = 'approved baseline' if active else 'previous appearance'
        print(f'Native validation passed; live config contains {state}. Only 16 appearance values are owned.')
        if args.action == 'verify':
            print('One compositor using this config is reachable. Rendered appearance still requires desktop inspection.')
        return
    session(manifest['version'])
    if args.action == 'preview':
        subprocess.run(['grim', str(out/'before.png')], check=True, timeout=10)
    with locked():
        record = apply(current, candidate, args.seconds if args.action == 'preview' else None)
    if args.action == 'activate':
        print('Approved appearance activated in the single existing config.')
        return
    try:
        time.sleep(2)
        subprocess.run(['grim', str(out/'candidate.png')], check=True, timeout=10)
        print(f'Preview visible for {args.seconds}s; Ctrl+C restores. Screenshots: {out}', flush=True)
        time.sleep(max(0, args.seconds-2))
    finally:
        with locked():
            pending = STATE/'pending.json'
            if pending.exists() and json.loads(pending.read_text())['id'] == record['id']:
                restore(record)
    print('Preview ended; original appearance restored.')


if __name__ == '__main__':
    def interrupted(signum, frame):
        raise InterruptedError('Appearance operation interrupted')
    signal.signal(signal.SIGTERM, interrupted)
    signal.signal(signal.SIGHUP, interrupted)
    try:
        main()
    except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as exc:
        details = getattr(exc, 'stderr', None)
        if isinstance(details, bytes):
            details = details.decode(errors='replace')
        raise SystemExit(str(exc) + ('\n' + details.strip() if details else ''))
