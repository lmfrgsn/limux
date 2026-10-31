#!/usr/bin/env python3
"""Mac-style Command shortcuts for Thunar's own actions. Functional Limux setting:
writes Thunar's accelerator map; rollback restores Thunar's defaults exactly."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT/'themes/recovery/thunar-shortcuts.json'
# Command keys MangoWM already owns globally are left on Thunar's defaults:
# N (layout), I and M (minimise), R (reload), O (overlay), G, E, K, Space, Tab, arrows left/right.
SHORTCUTS = {
    'ThunarActionManager/copy': '<Super>c',
    'ThunarActionManager/cut': '<Super>x',
    'ThunarActionManager/paste': '<Super>v',
    'ThunarActionManager/undo': '<Super>z',
    'ThunarActionManager/redo': '<Super><Shift>z',
    'ThunarActionManager/move-to-trash': '<Super>BackSpace',
    'ThunarActionManager/open': '<Super>Down',
    'ThunarStandardView/select-all-files': '<Super>a',
    'ThunarStandardView/create-folder': '<Super><Shift>n',
    'ThunarStandardView/duplicate': '<Super>d',
    'ThunarStandardView/back': '<Super>bracketleft',
    'ThunarStandardView/forward': '<Super>bracketright',
    'ThunarWindow/open-parent': '<Super>Up',
    'ThunarWindow/open-home': '<Super><Shift>h',
    'ThunarWindow/open-location': '<Super>l',
    'ThunarWindow/search': '<Super>f',
    'ThunarWindow/new-tab': '<Super>t',
    'ThunarWindow/close-tab': '<Super>w',
    'ThunarWindow/close-window': '<Super>q',
    'ThunarWindow/view-as-icons': '<Super>1',
    'ThunarWindow/view-as-detailed-list': '<Super>2',
    'ThunarWindow/view-as-compact-list': '<Super>3',
    'ThunarWindow/zoom-in-alt2': '<Super>equal',
    'ThunarWindow/zoom-out': '<Super>minus',
    'ThunarWindow/zoom-reset': '<Super>0',
}
LINE = re.compile(r'^(; )?\(gtk_accel_path "<Actions>/([^"]+)" "([^"]*)"\)$')


def digest(data):
    return hashlib.sha256(data).hexdigest()


def parse(text):
    """Accelerators Thunar treats as set by the user (uncommented lines)."""
    return {m.group(2): m.group(3) for m in map(LINE.match, text.splitlines()) if m and not m.group(1)}


def render(original):
    out, seen = [], set()
    for line in original.splitlines():
        m = LINE.match(line)
        if m and m.group(2) in SHORTCUTS:
            out.append(f'(gtk_accel_path "<Actions>/{m.group(2)}" "{SHORTCUTS[m.group(2)]}")')
            seen.add(m.group(2))
        else:
            out.append(line)
    out += [f'(gtk_accel_path "<Actions>/{p}" "{a}")' for p, a in SHORTCUTS.items() if p not in seen]
    return '\n'.join(out) + '\n'


def same_keys(accels):
    """Thunar may save modifiers in another order (<Shift><Super>z for <Super><Shift>z)."""
    return {path: (frozenset(re.findall(r'<([^>]+)>', accel)), accel.rsplit('>', 1)[-1])
            for path, accel in accels.items()}


def state(text):
    current = parse(text)
    return 'active' if same_keys(current) == same_keys(SHORTCUTS) else 'original' if not current else 'unknown'


def thunar_running():
    return subprocess.run(['pgrep', '-u', str(os.getuid()), '-x', 'thunar'], capture_output=True).returncode == 0


def validate():
    """Syntax only here; tests/test_thunar_shortcuts.py checks every key with GTK's parser."""
    for path, accel in SHORTCUTS.items():
        if not re.fullmatch(r'[A-Za-z]+/[a-z0-9-]+', path) or not re.fullmatch(r'(<(Super|Shift)>)+[A-Za-z0-9]+', accel):
            raise RuntimeError(f'Invalid Thunar shortcut: {path}={accel}')


def write(path, text):
    fd, name = tempfile.mkstemp(prefix='.limux-', dir=path.parent)
    try:
        with os.fdopen(fd, 'w') as stream:
            os.fchmod(stream.fileno(), path.stat().st_mode & 0o777 if path.exists() else 0o644)
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
    finally:
        Path(name).unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['check', 'activate', 'rollback', 'verify'])
    args = parser.parse_args()
    manifest = json.loads(MANIFEST.read_text())
    original = (ROOT/'themes/recovery'/manifest['recovery_file']).read_text()
    if digest(original.encode()) != manifest['original_sha256'] or state(original) != 'original':
        raise RuntimeError('Thunar shortcut recovery copy failed its integrity check')
    live = Path(os.environ.get('XDG_CONFIG_HOME', str(Path.home()/'.config')))/'Thunar/accels.scm'
    current = live.read_text() if live.exists() else original
    now = state(current)
    if now == 'unknown':
        raise RuntimeError('Thunar shortcuts were changed by hand; review before activation or rollback')
    if args.action in ('check', 'verify'):
        validate()
        if args.action == 'verify' and now != 'active':
            raise RuntimeError('Limux Thunar shortcuts are not active')
        print(f'All {len(SHORTCUTS)} Command shortcuts are valid. Live: '
              + ('Limux shortcuts.' if now == 'active' else 'Thunar defaults.'))
        return
    if thunar_running():
        raise RuntimeError('Close every Thunar window first (or run `thunar -q`); Thunar rewrites this file on quit')
    if args.action == 'activate':
        validate()
        if now != 'active':
            write(live, render(current))
        print('Activated Command shortcuts in Thunar (⌘C/X/V, ⌘Z, ⌘A, ⌘⌫, ⌘↑/↓, ⌘[ ], ⌘T/W/Q, ⌘1–3 and more).')
    else:
        if now != 'original':
            write(live, original)
        print("Restored Thunar's default shortcuts.")


if __name__ == '__main__':
    try:
        main()
    except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as exc:
        raise SystemExit(str(exc))
