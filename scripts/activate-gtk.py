#!/usr/bin/env python3
"""Guarded Limux Files activation: GTK 3 theme, Rhapsody stylesheet, outline icons
and Thunar view settings. Rollback restores defaults without reading tokens."""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import tempfile
import tomllib
from gtk import gsettings, render_css, render_icons, thunar_settings

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT/'themes/recovery/gtk.json'
SCHEMA = 'org.gnome.desktop.interface'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def tree_digest(files, links):
    h = hashlib.sha256()
    for rel in sorted(files):
        h.update(f'F {rel}\n'.encode())
        h.update(files[rel])
    for rel in sorted(links):
        h.update(f'L {rel} {links[rel]}\n'.encode())
    return h.hexdigest()


def read_tree(root):
    files, links = {}, {}
    for path in sorted(root.rglob('*')):
        rel = path.relative_to(root).as_posix()
        if path.is_symlink():
            links[rel] = os.readlink(path)
        elif path.is_file():
            if path.stat().st_uid != os.getuid():
                raise RuntimeError(f'Unexpected icon file ownership: {path}')
            files[rel] = path.read_bytes()
    return files, links


def sync_directory(path):
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


class Live:
    """The user's real GTK settings, Thunar xfconf channel and appearance files."""

    def __init__(self):
        config = Path(os.environ.get('XDG_CONFIG_HOME', str(Path.home()/'.config')))
        data = Path(os.environ.get('XDG_DATA_HOME', str(Path.home()/'.local/share')))
        self.css = config/'gtk-3.0/gtk.css'
        self.icons = data/'icons'

    def get_setting(self, key):
        out = subprocess.run(['gsettings', 'get', SCHEMA, key], capture_output=True, text=True, check=True)
        return out.stdout.strip().strip("'")

    def set_setting(self, key, value):
        subprocess.run(['gsettings', 'set', SCHEMA, key, value], check=True, capture_output=True)

    def reset_setting(self, key):
        subprocess.run(['gsettings', 'reset', SCHEMA, key], check=True, capture_output=True)

    def get_prop(self, name):
        out = subprocess.run(['xfconf-query', '-c', 'thunar', '-p', f'/{name}'], capture_output=True, text=True)
        if out.returncode != 0:
            if 'does not exist' in out.stderr + out.stdout:
                return None
            raise RuntimeError(f'Cannot read Thunar setting {name}: {out.stderr.strip()}')
        return out.stdout.rstrip('\n')

    def set_prop(self, name, kind, value):
        subprocess.run(['xfconf-query', '-c', 'thunar', '-p', f'/{name}', '-n', '-t', kind, '-s', value],
                       check=True, capture_output=True)

    def reset_prop(self, name):
        subprocess.run(['xfconf-query', '-c', 'thunar', '-p', f'/{name}', '-r'], check=True, capture_output=True)


def classify(live, manifest):
    """Return each owned item's state: 'original', 'active', 'previous' (an earlier
    approved stylesheet or icon set, safe to replace) or 'unknown'."""
    state = {}
    if live.css.is_symlink() or (live.css.exists() and not live.css.is_file()):
        state['css'] = 'unknown'
    elif not live.css.exists():
        state['css'] = 'original'
    else:
        found = digest(live.css.read_bytes())
        state['css'] = ('active' if found == manifest['css_sha256'] else
                        'previous' if found in manifest.get('css_previous_sha256', []) else 'unknown')
    icons = live.icons/manifest['icon_theme']
    if icons.is_symlink() or (icons.exists() and not icons.is_dir()):
        state['icons'] = 'unknown'
    elif not icons.exists():
        state['icons'] = 'original'
    else:
        found = tree_digest(*read_tree(icons))
        state['icons'] = ('active' if found == manifest['icons_sha256'] else
                          'previous' if found in manifest.get('icons_previous_sha256', []) else 'unknown')
    for key, value in manifest['gsettings'].items():
        current = live.get_setting(key)
        state[f'gsettings:{key}'] = ('active' if current == value else
                                     'original' if current == manifest['gsettings_original'][key] else 'unknown')
    for name, (_, value) in manifest['xfconf'].items():
        current = live.get_prop(name)
        state[f'xfconf:{name}'] = 'original' if current is None else 'active' if current == value else 'unknown'
    return state


def install_icons(live, manifest, files, links):
    """Stage the set beside the live one and swap it in. An earlier approved set is
    moved aside and returned, so a later failure can put it back."""
    final = live.icons/manifest['icon_theme']
    live.icons.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix='.limux-icons-', dir=live.icons))
    aside = None
    try:
        for rel, data in files.items():
            (staging/rel).parent.mkdir(parents=True, exist_ok=True)
            (staging/rel).write_bytes(data)
        for rel, target in links.items():
            (staging/rel).parent.mkdir(parents=True, exist_ok=True)
            (staging/rel).symlink_to(target)
        if final.exists():
            aside = live.icons/f'.limux-icons-previous-{os.getpid()}'
            os.rename(final, aside)
        try:
            os.rename(staging, final)
        except BaseException:
            if aside is not None:
                os.rename(aside, final)
            raise
        sync_directory(live.icons)
    finally:
        shutil.rmtree(staging, ignore_errors=True)
    return aside


def write_css(live, data):
    live.css.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix='.limux-', dir=live.css.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            os.fchmod(stream.fileno(), 0o644)
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, live.css)
        sync_directory(live.css.parent)
    finally:
        Path(name).unlink(missing_ok=True)


def remove(live, manifest, item):
    if item == 'css':
        live.css.unlink()
        sync_directory(live.css.parent)
    elif item == 'icons':
        shutil.rmtree(live.icons/manifest['icon_theme'])
        sync_directory(live.icons)
    elif item.startswith('gsettings:'):
        live.reset_setting(item.split(':', 1)[1])
    else:
        live.reset_prop(item.split(':', 1)[1])


def activate(live, manifest, css, files, links):
    """Icons and stylesheet first, Thunar settings next, the GTK theme switch last."""
    state = classify(live, manifest)
    unknown = sorted(k for k, v in state.items() if v == 'unknown')
    if unknown:
        raise RuntimeError('Unrecognised existing values; refusing to overwrite: ' + ', '.join(unknown))
    done, aside, old_css = [], None, None
    try:
        if state['icons'] in ('original', 'previous'):
            aside = install_icons(live, manifest, files, links)
            done.append('icons')
        if state['css'] == 'previous':
            old_css = live.css.read_bytes()
            write_css(live, css)
        elif state['css'] == 'original':
            write_css(live, css)
            done.append('css')
        for name, (kind, value) in manifest['xfconf'].items():
            if state[f'xfconf:{name}'] == 'original':
                live.set_prop(name, kind, value)
                done.append(f'xfconf:{name}')
        for key in manifest['gsettings']:  # gtk-theme is listed last
            if state[f'gsettings:{key}'] == 'original':
                live.set_setting(key, manifest['gsettings'][key])
                done.append(f'gsettings:{key}')
        after = classify(live, manifest)
        if set(after.values()) != {'active'}:
            raise RuntimeError('Activation did not verify: ' + ', '.join(k for k, v in after.items() if v != 'active'))
    except BaseException:
        for item in reversed(done):
            remove(live, manifest, item)
        if aside is not None:
            os.rename(aside, live.icons/manifest['icon_theme'])
        if old_css is not None:
            write_css(live, old_css)
        raise
    if aside is not None:
        shutil.rmtree(aside)
        sync_directory(live.icons)
    return done


def rollback(live, manifest):
    """Theme switch first, then settings, stylesheet and icons. Values the user
    has since changed are left alone and reported."""
    state = classify(live, manifest)
    order = ([f'gsettings:{k}' for k in reversed(manifest['gsettings'])] +
             [f'xfconf:{n}' for n in manifest['xfconf']] + ['css', 'icons'])
    for item in order:
        if state[item] in ('active', 'previous'):
            remove(live, manifest, item)
    return sorted(k for k, v in state.items() if v == 'unknown')


def candidate(manifest):
    theme = tomllib.loads((ROOT/'themes/rhapsody.toml').read_text())
    css = render_css(theme).encode()
    files, links = render_icons(theme)
    if digest(css) != manifest['css_sha256'] or tree_digest(files, links) != manifest['icons_sha256']:
        raise RuntimeError('Generated Limux Files appearance differs from the pinned approved version')
    if gsettings(theme) != manifest['gsettings'] or {k: list(v) for k, v in thunar_settings(theme).items()} != manifest['xfconf']:
        raise RuntimeError('Generated Limux Files settings differ from the pinned approved version')
    return css, files, links


def preflight(manifest):
    if not os.environ.get('DBUS_SESSION_BUS_ADDRESS'):
        raise RuntimeError('No session bus; run from Foot in the desktop session. No changes made.')
    version = subprocess.check_output(['thunar', '--version'], text=True)
    if f"thunar {manifest['thunar_version']} " not in version:
        raise RuntimeError('Thunar version changed; review selectors before activation')
    theme = Path('/usr/share/themes')/manifest['gsettings']['gtk-theme']/'gtk-3.0/gtk.css'
    if subprocess.run(['pacman', '-Q', manifest['gtk_package']], capture_output=True).returncode != 0 or not theme.is_file():
        raise RuntimeError(f"Install the GTK theme first: sudo pacman -S {manifest['gtk_package']}")
    family = subprocess.check_output(['fc-match', '-f', '%{family}', manifest['font']], text=True)
    if manifest['font'] not in family.split(','):
        raise RuntimeError('Approved font unavailable; refusing silent fallback')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['check', 'activate', 'rollback', 'verify'])
    args = parser.parse_args()
    manifest = json.loads(MANIFEST.read_text())
    live = Live()
    if args.action in ('check', 'verify'):
        candidate(manifest)
        state = classify(live, manifest)
        summary = ('Limux Files active' if set(state.values()) == {'active'} else
                   'previous defaults' if set(state.values()) == {'original'} else
                   'mixed: ' + ', '.join(f'{k}={v}' for k, v in state.items() if v != 'original'))
        if args.action == 'verify':
            preflight(manifest)
            if summary != 'Limux Files active':
                raise RuntimeError(f'Limux Files is not fully active: {summary}')
        print(f'Approval pin and generated output verified. Live: {summary}.')
        return
    if args.action == 'activate':
        css, files, links = candidate(manifest)
        preflight(manifest)
    runtime = Path(os.environ['XDG_RUNTIME_DIR'])
    with (runtime/'limux-gtk-activation.lock').open('w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if args.action == 'activate':
            activate(live, manifest, css, files, links)
            print('Activated Limux Files. Close every Thunar window (or run `thunar -q`), then reopen.')
            print('Firefox follows the GTK theme and colours; restart it to see its final appearance.')
        else:
            kept = rollback(live, manifest)
            print('Restored default GTK theme, icons and Thunar view settings.')
            if kept:
                print('Left unchanged because you changed them after activation: ' + ', '.join(kept))
            print('Close every Thunar window (or run `thunar -q`), then reopen.')


if __name__ == '__main__':
    def interrupted(signum, frame):
        raise InterruptedError('Activation interrupted')
    signal.signal(signal.SIGTERM, interrupted)
    try:
        main()
    except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as exc:
        raise SystemExit(str(exc))
