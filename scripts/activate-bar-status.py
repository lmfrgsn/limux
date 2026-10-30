#!/usr/bin/env python3
"""Activate, verify or roll back bar status icons and agent indicators.

A layer over the active Quiet Workspace Strip: it replaces the patched Mangobar
binary, bar config and CSS, updates the Wi-Fi script, installs the Tabler icon
font with one fontconfig rule, and adds Codex and Claude Code status hooks. Exact
previous bytes are kept in ~/.local/state/limux/bar-status-activation so rollback
restores the Quiet Strip as it was; run rollback here before any
activate-quiet-bar.py action. Run from Foot in the desktop session.
"""
import argparse
import base64
import fcntl
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
import tomllib
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
HOME = Path.home()
MANIFEST = ROOT/'themes/recovery/bar-status.json'
STATE = HOME/'.local/state/limux/bar-status-activation'
QUIET_STATE = HOME/'.local/state/limux/quiet-bar-activation'
CONFIG = HOME/'.config/mangobar/config.jsonc'
CSS = HOME/'.config/mangobar/style.css'
LAUNCHER = HOME/'.local/bin/limux-bar'
PATCHED = HOME/'.local/libexec/limux/mangobar-0.2.2-quiet/mangobar'
WIFI = HOME/'.local/share/limux/mangobar/wifi-status.py'
WIFI_SOURCE = ROOT/'machine/home/.local/share/limux/mangobar/wifi-status.py'
FONT = HOME/'.local/share/fonts/limux/tabler-icons-3.49.0.ttf'
RULE = HOME/'.config/fontconfig/conf.d/60-limux-bar-icons.conf'
CLAUDE = HOME/'.claude/settings.json'
CODEX = HOME/'.codex/hooks.json'
AGENT = ROOT/'scripts/agent-status.py'
CLAUDE_EVENTS = ('SessionStart', 'UserPromptSubmit', 'PreToolUse', 'PostToolUse', 'PostToolUseFailure',
                 'PermissionRequest', 'Notification', 'Stop', 'StopFailure', 'SessionEnd')
CODEX_EVENTS = ('SessionStart', 'UserPromptSubmit', 'PreToolUse', 'PermissionRequest', 'PostToolUse',
                'Stop', 'Interrupt', 'SessionEnd')
FILES = ('config', 'css', 'binary', 'wifi')

sys.path.insert(0, str(ROOT/'scripts'))
import bar_status  # noqa: E402
from mangobar import render_quiet  # noqa: E402


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def digest(data):
    return hashlib.sha256(data).hexdigest()


def atomic_write(path, data, mode=0o644):
    if path.is_symlink() or (path.exists() and not path.is_file()):
        raise RuntimeError(f'unsafe destination: {path}')
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix='.limux-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            os.fchmod(stream.fileno(), mode)
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
    finally:
        Path(name).unlink(missing_ok=True)


def command(agent):
    return f'python3 {AGENT} hook {agent}'


# --- Generated outputs -------------------------------------------------------

def generate(quiet_config):
    """Bar config and CSS from the tokens, layered on the given Quiet Strip config."""
    theme = tomllib.loads((ROOT/'themes/rhapsody.toml').read_text())
    quiet = load('quiet_bar', ROOT/'scripts/quiet-bar.py')
    with tempfile.TemporaryDirectory() as folder:
        source = Path(folder)/'config.jsonc'
        source.write_bytes(quiet_config)
        data = quiet.candidate_config(theme, source)
    data = bar_status.modules(theme, data, AGENT)
    config = (json.dumps(data, indent=2, ensure_ascii=False) + '\n').encode()
    css = (render_quiet(theme) + bar_status.css(theme)).encode()
    return config, css, bar_status.fontconfig(theme).encode()


def build_binary():
    builder = load('quiet_build', ROOT/'scripts/quiet-mangobar-build.py')
    patches = builder.PATCHES + (ROOT/'patches/mangobar/03-hide-empty-custom-modules.patch',)
    return builder.build(patches, ROOT/'build/bar-status').read_bytes()


def fetch_font(manifest):
    """Download the pinned Tabler release and return the verified font bytes."""
    font = manifest['font']
    with urllib.request.urlopen(font['tarball'], timeout=60) as response:
        tarball = response.read()
    algorithm, expected = font['integrity'].split('-', 1)
    if base64.b64encode(hashlib.new(algorithm, tarball).digest()).decode() != expected:
        raise RuntimeError('Tabler package integrity check failed')
    with tarfile.open(fileobj=io.BytesIO(tarball)) as archive:
        data = archive.extractfile(font['member']).read()
    if digest(data) != font['sha256']:
        raise RuntimeError('Tabler font checksum mismatch')
    return data


# --- Hooks -------------------------------------------------------------------

def claude_with(settings):
    hooks = settings.setdefault('hooks', {})
    for event in CLAUDE_EVENTS:
        groups = hooks.setdefault(event, [])
        if not any(h.get('command') == command('claude') for g in groups for h in g.get('hooks', [])):
            groups.append({'hooks': [{'type': 'command', 'command': command('claude'), 'async': True}]})
    return settings


def claude_without(settings):
    hooks = settings.get('hooks', {})
    for event in list(hooks):
        groups = []
        for group in hooks[event]:
            kept = [h for h in group.get('hooks', []) if h.get('command') != command('claude')]
            if kept:
                groups.append(dict(group, hooks=kept))
        if groups:
            hooks[event] = groups
        else:
            del hooks[event]
    if 'hooks' in settings and not settings['hooks']:
        del settings['hooks']
    return settings


def claude_state(settings):
    present = {event for event, groups in settings.get('hooks', {}).items()
               if any(h.get('command') == command('claude') for g in groups for h in g.get('hooks', []))}
    return 'active' if present == set(CLAUDE_EVENTS) else 'original' if not present else 'unknown'


def codex_document():
    hook = lambda event: {'type': 'command', 'command': command('codex'),  # noqa: E731
                          **({} if event == 'SessionEnd' else {'async': True})}
    return (json.dumps({'hooks': {event: [{'hooks': [hook(event)]}] for event in CODEX_EVENTS}},
                       indent=2) + '\n').encode()


# --- State ---------------------------------------------------------------------

def quiet_pins():
    manifest = json.loads((QUIET_STATE/'manifest.json').read_text())
    return manifest['candidate'], manifest['binary']


def classify(manifest):
    quiet, quiet_binary = quiet_pins()
    previous = {'config': quiet['config'], 'css': quiet['css'], 'binary': quiet_binary,
                'wifi': manifest['wifi_previous_sha256']}
    paths = {'config': CONFIG, 'css': CSS, 'binary': PATCHED, 'wifi': WIFI}
    state = {}
    for name in FILES:
        path = paths[name]
        found = None if path.is_symlink() or not path.is_file() else digest(path.read_bytes())
        state[name] = ('active' if found == manifest[name] else 'original' if found == previous[name]
                       else 'unknown')
    for name, path, pin in (('font', FONT, manifest['font']['sha256']), ('rule', RULE, manifest['rule'])):
        state[name] = ('original' if not path.exists() and not path.is_symlink() else
                       'active' if path.is_file() and not path.is_symlink() and digest(path.read_bytes()) == pin
                       else 'unknown')
    try:
        state['claude'] = claude_state(json.loads(CLAUDE.read_text())) if CLAUDE.exists() else 'original'
    except ValueError:
        state['claude'] = 'unknown'
    state['codex'] = ('original' if not CODEX.exists() else
                      'active' if CODEX.read_bytes() == codex_document() else 'unknown')
    return state


def candidate(manifest):
    """Regenerate every output from the Quiet Strip backup and check the pins."""
    base = STATE/'config' if (STATE/'config').exists() else CONFIG
    quiet_config = base.read_bytes()
    if digest(quiet_config) != quiet_pins()[0]['config']:
        raise RuntimeError('Quiet Strip config is not the pinned active candidate; inspect first')
    config, css, rule = generate(quiet_config)
    if (digest(config), digest(css), digest(rule)) != (manifest['config'], manifest['css'], manifest['rule']):
        raise RuntimeError('generated bar status output differs from the approved pin')
    if digest(WIFI_SOURCE.read_bytes()) != manifest['wifi']:
        raise RuntimeError('Wi-Fi script source differs from the approved pin')
    if digest(codex_document()) != manifest['codex']:
        raise RuntimeError('Codex hook document differs from the approved pin')
    return config, css, rule


def managed_binary():
    pids = subprocess.run(['pgrep', '-u', str(os.getuid()), '-x', 'mangobar'],
                          capture_output=True, text=True).stdout.split()
    if len(pids) != 1:
        raise RuntimeError(f'expected one Mangobar, found {len(pids)}')
    return Path(f'/proc/{pids[0]}/exe').resolve()


def refresh_bar(expected):
    subprocess.run([str(LAUNCHER), 'refresh'], check=True, timeout=25, capture_output=True)
    time.sleep(1)
    if managed_binary() != PATCHED.resolve() or digest(PATCHED.read_bytes()) != expected:
        raise RuntimeError('managed bar is not the expected binary after refresh')


def fc_cache():
    subprocess.run(['fc-cache', '-f', str(FONT.parent.parent)], check=True, capture_output=True)


# --- Actions -----------------------------------------------------------------

def activate(manifest):
    state = classify(manifest)
    unknown = sorted(k for k, v in state.items() if v == 'unknown')
    if unknown:
        raise RuntimeError('unrecognised existing values; refusing to overwrite: ' + ', '.join(unknown))
    if set(state.values()) == {'active'}:
        print('Bar status already active.')
        return
    if STATE.exists():
        raise RuntimeError(f'activation state exists at {STATE}; roll back or inspect first')
    if set(state.values()) != {'original'}:
        raise RuntimeError('partially active; run rollback first: ' +
                           ', '.join(f'{k}={v}' for k, v in state.items() if v != 'original'))
    subprocess.run([sys.executable, str(ROOT/'scripts/activate-quiet-bar.py'), 'check'], check=True)
    config, css, rule = candidate(manifest)
    binary = build_binary()
    if digest(binary) != manifest['binary']:
        raise RuntimeError('patched Mangobar build differs from the approved pin')
    font = fetch_font(manifest)
    claude_before = CLAUDE.read_bytes() if CLAUDE.exists() else None

    staged = Path(tempfile.mkdtemp(prefix='.bar-status-', dir=STATE.parent))
    for name, path in (('config', CONFIG), ('css', CSS), ('binary', PATCHED), ('wifi', WIFI)):
        (staged/name).write_bytes(path.read_bytes())
    if claude_before is not None:
        (staged/'claude-settings.json').write_bytes(claude_before)
    os.replace(staged, STATE)

    done = []
    try:
        atomic_write(FONT, font)
        done.append('font')
        atomic_write(RULE, rule)
        done.append('rule')
        fc_cache()
        atomic_write(WIFI, WIFI_SOURCE.read_bytes())
        done.append('wifi')
        atomic_write(PATCHED, binary, 0o755)
        atomic_write(CONFIG, config)
        atomic_write(CSS, css)
        done.append('bar')
        refresh_bar(manifest['binary'])
        settings = json.loads(claude_before) if claude_before else {}
        atomic_write(CLAUDE, (json.dumps(claude_with(settings), indent=2) + '\n').encode())
        done.append('claude')
        atomic_write(CODEX, codex_document())
        done.append('codex')
        subprocess.run([sys.executable, str(AGENT), 'render'], check=True)
        after = classify(manifest)
        if set(after.values()) != {'active'}:
            raise RuntimeError('activation did not verify: ' + ', '.join(k for k, v in after.items() if v != 'active'))
    except BaseException as failure:
        try:
            undo(done, claude_before)
            shutil.rmtree(STATE)
        except BaseException as recovery:
            raise RuntimeError(f'activation failed and recovery failed; backup kept at {STATE}: {recovery}') from failure
        raise RuntimeError('activation failed; previous bar, fonts and hooks restored') from failure
    print('Bar status active: Tabler icons, agent indicators and hooks installed; one managed bar verified.')
    print('In Codex, open /hooks once and trust the Limux agent status hooks.')


def undo(done, claude_before):
    """Reverse completed steps from the state backup."""
    if 'codex' in done:
        CODEX.unlink(missing_ok=True)
    if 'claude' in done:
        if claude_before is None:
            CLAUDE.unlink(missing_ok=True)
        else:
            atomic_write(CLAUDE, claude_before)
    if 'bar' in done:
        atomic_write(CONFIG, (STATE/'config').read_bytes())
        atomic_write(CSS, (STATE/'css').read_bytes())
        atomic_write(PATCHED, (STATE/'binary').read_bytes(), 0o755)
        refresh_bar(digest((STATE/'binary').read_bytes()))
    if 'wifi' in done:
        atomic_write(WIFI, (STATE/'wifi').read_bytes())
    if 'rule' in done:
        RULE.unlink(missing_ok=True)
    if 'font' in done:
        FONT.unlink(missing_ok=True)
        try:
            FONT.parent.rmdir()
        except OSError:
            pass
    if {'rule', 'font'} & set(done):
        fc_cache()


def rollback(manifest):
    if not STATE.exists():
        state = classify(manifest)
        if set(state.values()) == {'original'}:
            print('Bar status is not active; nothing to roll back.')
            return
        raise RuntimeError('no activation backup, but bar status items are present: ' +
                           ', '.join(f'{k}={v}' for k, v in state.items() if v != 'original'))
    for name, path in (('config', CONFIG), ('css', CSS), ('binary', PATCHED), ('wifi', WIFI)):
        current = digest(path.read_bytes()) if path.is_file() else None
        if current not in (manifest[name], digest((STATE/name).read_bytes())):
            raise RuntimeError(f'{name} has unreviewed edits; refusing rollback overwrite')
    claude_before = (STATE/'claude-settings.json').read_bytes() if (STATE/'claude-settings.json').exists() else None
    if CLAUDE.exists():
        current = json.loads(CLAUDE.read_text())
        restored = claude_without(current)
        # Restore the exact original when nothing else changed; otherwise keep the user's edits.
        if claude_before is not None and json.loads(claude_before) == restored:
            atomic_write(CLAUDE, claude_before)
        elif restored or claude_before is not None:
            atomic_write(CLAUDE, (json.dumps(restored, indent=2) + '\n').encode())
        else:
            CLAUDE.unlink()
    if CODEX.exists() and CODEX.read_bytes() == codex_document():
        CODEX.unlink()
    undo(['bar', 'wifi', 'rule', 'font'], claude_before)
    shutil.rmtree(STATE)
    subprocess.run([sys.executable, str(ROOT/'scripts/activate-quiet-bar.py'), 'check'], check=True)
    print('Previous Quiet Strip bar, Wi-Fi script and fonts restored; agent hooks removed.')


def verify(manifest):
    state = classify(manifest)
    candidate(manifest)
    summary = ('active' if set(state.values()) == {'active'} else 'not active' if set(state.values()) == {'original'}
               else 'mixed: ' + ', '.join(f'{k}={v}' for k, v in state.items()))
    if summary == 'active' and managed_binary() != PATCHED.resolve():
        raise RuntimeError('the running bar is not the managed patched binary')
    print(f'Approval pins verified. Bar status {summary}.')
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('action', choices=['check', 'activate', 'verify', 'rollback'])
    action = parser.parse_args().action
    manifest = json.loads(MANIFEST.read_text())
    runtime = Path(os.environ['XDG_RUNTIME_DIR'])
    with (runtime/'limux-bar-status-activation.lock').open('w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if action == 'check':
            verify(manifest)
        elif action == 'verify':
            if verify(manifest) != 'active':
                raise SystemExit('Bar status is not fully active.')
        elif action == 'activate':
            activate(manifest)
        else:
            rollback(manifest)


if __name__ == '__main__':
    try:
        main()
    except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as exc:
        raise SystemExit(f'Bar status: {exc}')
