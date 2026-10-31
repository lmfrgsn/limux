#!/usr/bin/env python3
"""Limux launcher entries: per-user desktop-entry overrides that hide developer and
helper entries and name the core apps by role. Functional Limux content, not theme."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT/'themes/recovery/launcher-entries.json'
SYSTEM = Path('/usr/share/applications')
# Reachable elsewhere or not for everyday launching: helpers, servers, test tools.
HIDE = ('footclient', 'foot-server', 'qv4l2', 'qvidcap', 'rofi', 'rofi-theme-selector',
        'thunar-bulk-rename', 'thunar-settings', 'xfce4-about')
# Name by role, matching the Command menu; the app name stays as GenericName for search.
RENAME = {'thunar': ('Files', 'Thunar'), 'foot': ('Terminal', 'Foot'), 'btop': ('Activity Monitor', 'btop')}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def generate(system=SYSTEM):
    """Return ({file name: bytes}, {source name: sha256}) for every owned override."""
    files, sources = {}, {}
    for app in HIDE:
        files[f'{app}.desktop'] = f'[Desktop Entry]\nType=Application\nName={app}\nHidden=true\n'.encode()
    for app, (name, generic) in RENAME.items():
        source = (system/f'{app}.desktop').read_bytes()
        sources[f'{app}.desktop'] = digest(source)
        section, out = None, []
        for line in source.decode().splitlines():
            if line.startswith('['):
                section = line
            # Only the main entry is renamed; actions such as Thunar's "Home" stay as they are.
            if section == '[Desktop Entry]' and re.match(r'(Name|GenericName)(\[[^\]]+\])?=', line):
                if line.startswith('Name='):
                    out.append(f'Name={name}')
                elif line.startswith('GenericName='):
                    out.append(f'GenericName={generic}')
                continue
            out.append(line)
        files[f'{app}.desktop'] = ('\n'.join(out) + '\n').encode()
    return files, sources


def classify(directory, manifest):
    state = {}
    for name, expected in manifest['files'].items():
        path = directory/name
        if path.is_symlink() or (path.exists() and not path.is_file()):
            state[name] = 'unknown'
        elif not path.exists():
            state[name] = 'original'
        else:
            state[name] = 'active' if digest(path.read_bytes()) == expected else 'unknown'
    return state


def write(path, data):
    fd, name = tempfile.mkstemp(prefix='.limux-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            os.fchmod(stream.fileno(), 0o644)
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
    finally:
        Path(name).unlink(missing_ok=True)


def activate(directory, manifest, files):
    state = classify(directory, manifest)
    unknown = sorted(n for n, v in state.items() if v == 'unknown')
    if unknown:
        raise RuntimeError('Existing entries differ; refusing to overwrite: ' + ', '.join(unknown))
    directory.mkdir(parents=True, exist_ok=True)
    done = []
    try:
        for name, data in files.items():
            if state[name] == 'original':
                write(directory/name, data)
                done.append(name)
    except BaseException:
        for name in done:
            (directory/name).unlink(missing_ok=True)
        raise
    return done


def rollback(directory, manifest):
    """Remove only overrides that still match what Limux wrote; report the rest."""
    state = classify(directory, manifest)
    for name, value in state.items():
        if value == 'active':
            (directory/name).unlink()
    return sorted(n for n, v in state.items() if v == 'unknown')


def candidate(manifest, system=SYSTEM):
    files, sources = generate(system)
    if sources != manifest['sources']:
        raise RuntimeError('A system desktop entry changed since approval; review and re-pin the overrides')
    if {n: digest(d) for n, d in files.items()} != manifest['files']:
        raise RuntimeError('Generated launcher entries differ from the pinned approved version')
    return files


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['check', 'activate', 'rollback', 'verify'])
    args = parser.parse_args()
    manifest = json.loads(MANIFEST.read_text())
    directory = Path(os.environ.get('XDG_DATA_HOME', str(Path.home()/'.local/share')))/'applications'
    if args.action == 'rollback':
        kept = rollback(directory, manifest)
        print('Removed the Limux launcher overrides; system entries show again.')
        if kept:
            print('Left unchanged because they were edited after activation: ' + ', '.join(kept))
        return
    files = candidate(manifest)
    if args.action == 'activate':
        activate(directory, manifest, files)
        print('Activated Limux launcher entries: Firefox, Files, Terminal and Activity Monitor.')
        return
    state = classify(directory, manifest)
    summary = ('active' if set(state.values()) == {'active'} else 'not applied' if set(state.values()) == {'original'}
               else 'mixed: ' + ', '.join(f'{k}={v}' for k, v in state.items()))
    if args.action == 'verify' and summary != 'active':
        raise RuntimeError(f'Limux launcher entries are not fully active: {summary}')
    print(f'Approval pin and system sources verified. Launcher entries: {summary}.')


if __name__ == '__main__':
    try:
        main()
    except (OSError, RuntimeError, ValueError) as exc:
        raise SystemExit(str(exc))
