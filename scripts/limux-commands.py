#!/usr/bin/env python3
"""Limux Commands: read-only shortcut index and small action registry."""
import argparse
import configparser
import datetime
import fcntl
import hashlib
import os
from pathlib import Path
import subprocess
import sys
import tomllib
import uuid

HOME = Path.home()
MANGO = HOME / '.config/mango/config.conf'
FOOT = HOME / '.config/foot/foot.ini'
SNIPPETS = HOME / '.config/limux/commands.toml'
THEME = HOME / '.config/rofi/charcoal.rasi'
PROJECT = Path(__file__).resolve().parents[1]
EXAMPLE = PROJECT / 'examples/commands.toml'
TOKENS = PROJECT / 'themes/rhapsody.toml'
APPEARANCE_STATE = HOME / '.local/state/limux/commands-appearance'
MOD = {'super': '⌘', 'alt': '⌥', 'ctrl': '⌃', 'control': '⌃', 'shift': '⇧', 'none': ''}
ACTION = {
    'reload_config': ('System', 'Reload MangoWM configuration'),
    'quit': ('System', 'Quit MangoWM'), 'killclient': ('Windows', 'Close focused window'),
    'focusstack': ('Windows', 'Focus next window'), 'focusdir': ('Windows', 'Focus window'),
    'move_client': ('Windows', 'Move window'), 'toggleglobal': ('Windows', 'Toggle global window'),
    'togglejump': ('Windows', 'Jump to previous window'), 'togglefloating': ('Windows', 'Toggle floating'),
    'togglemaximizescreen': ('Windows', 'Toggle maximized'), 'togglefullscreen': ('Windows', 'Toggle fullscreen'),
    'togglefakefullscreen': ('Windows', 'Toggle fake fullscreen'), 'minimized': ('Windows', 'Minimize window'),
    'restore_minimized': ('Windows', 'Restore minimized window'), 'toggleoverlay': ('Windows', 'Toggle overlay'),
    'toggle_scratchpad': ('Windows', 'Toggle scratchpad'), 'set_proportion': ('Layout', 'Reset split proportion'),
    'switch_proportion_preset': ('Layout', 'Change split proportion'), 'scroller_stack': ('Layout', 'Scroll stack'),
    'dwindle_toggle_split_direction': ('Layout', 'Toggle split direction'),
    'switch_layout': ('Layout', 'Change layout'), 'viewtoleft': ('Workspaces', 'View workspace to the left'),
    'viewtoright': ('Workspaces', 'View workspace to the right'),
    'viewtoleft_have_client': ('Workspaces', 'View occupied workspace left'),
    'viewtoright_have_client': ('Workspaces', 'View occupied workspace right'),
    'tagtoleft': ('Workspaces', 'Move window to workspace left'),
    'tagtoright': ('Workspaces', 'Move window to workspace right'),
    'view': ('Workspaces', 'View workspace'), 'tag': ('Workspaces', 'Move window to workspace'),
    'focusmon': ('Windows', 'Focus monitor'), 'tagmon': ('Windows', 'Move window to monitor'),
    'incgaps': ('Layout', 'Adjust gaps'), 'togglegaps': ('Layout', 'Toggle gaps'),
    'movewin': ('Windows', 'Nudge window'), 'resizewin': ('Windows', 'Resize window'),
    'moveresize': ('Mouse', 'Move or resize window'), 'viewprev_have_client': ('Gestures', 'Previous occupied workspace'),
    'viewnext_have_client': ('Gestures', 'Next occupied workspace'),
    'enteroverview': ('Gestures', 'Open overview'), 'leaveoverview': ('Gestures', 'Close overview'),
}
SPAWN = {'rofi -show drun': ('Apps', 'Open application launcher'), 'foot': ('Apps', 'Open terminal'),
         'thunar': ('Apps', 'Open files')}
LOREM = 'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.'


def key(modifiers, name):
    parts = [MOD.get(x.lower(), x) for x in modifiers.split('+') if x.lower() != 'none']
    names = {'space': 'Space', 'Return': '↵', 'Left': '←', 'Right': '→', 'Up': '↑', 'Down': '↓',
             'backslash': '\\', 'Tab': 'Tab'}
    return ''.join(parts) + names.get(name, name.upper() if len(name) == 1 else name)


def shortcuts(path=MANGO):
    entries = []
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if line.startswith('#') or '=' not in line:
            continue
        kind, _, value = line.partition('=')
        if kind not in ('bind', 'mousebind', 'axisbind', 'gesturebind'):
            continue
        fields = [x.strip() for x in value.split(',')]
        if kind == 'gesturebind':
            if len(fields) < 4 or fields[3] not in ACTION:
                continue
            category, description = ACTION[fields[3]]
            entries.append((category, f'{fields[2]}-finger swipe {fields[1]}', description, None))
            continue
        if len(fields) < 3:
            continue
        modifiers, name, action = fields[:3]
        if action == 'spawn':
            command = ','.join(fields[3:]).strip()
            if command in SPAWN:
                category, description = SPAWN[command]
            elif 'mango-screenshot' in command:
                category, description = 'System', 'Capture ' + command.split()[-1] + ' screenshot'
            elif 't2-hardware-control' in command:
                category, description = 'Hardware', command.split()[-1].replace('-', ' ').capitalize()
            else:
                continue
        elif action in ACTION:
            category, description = ACTION[action]
            if action in ('view', 'tag') and len(fields) > 3:
                description += ' ' + fields[3]
            elif action in ('focusdir', 'move_client', 'focusmon', 'tagmon') and len(fields) > 3:
                description += ' ' + fields[3]
            elif action == 'incgaps' and len(fields) > 3:
                description = 'Increase gaps' if fields[3].startswith('+') or fields[3] == '1' else 'Decrease gaps'
        else:
            continue
        if kind == 'gesturebind':
            continue
        label = key(modifiers, name)
        if kind == 'mousebind':
            label += ' click'
            category = 'Mouse'
        elif kind == 'axisbind':
            label += ' scroll'
            category = 'Mouse'
        entries.append((category, label, description, None))
    return entries


def foot_shortcuts(path=FOOT):
    parser = configparser.ConfigParser(interpolation=None)
    parser.read(path)
    result = []
    for action, binding in parser.items('key-bindings') if parser.has_section('key-bindings') else []:
        for shortcut in binding.split():
            pieces = shortcut.split('+')
            result.append(('Foot', key('+'.join(pieces[:-1]), pieces[-1]),
                           action.replace('-', ' ').capitalize() + ' in Foot', None))
    return result


def personal_config(path=SNIPPETS):
    if not path.exists():
        return {}, {}
    if path.stat().st_mode & 0o077:
        raise ValueError(f'{path} must be private (chmod 600)')
    data = tomllib.loads(path.read_text())
    snippets = data.get('snippets', {})
    links = data.get('quicklinks', {})
    if not isinstance(snippets, dict) or any(not isinstance(k, str) or not isinstance(v, str) for k, v in snippets.items()):
        raise ValueError('snippets must be a table of text values')
    if not isinstance(links, dict) or any(not isinstance(k, str) or not isinstance(v, str) for k, v in links.items()):
        raise ValueError('quicklinks must be a table of text values')
    for name, target in links.items():
        if not target.startswith(('https://', 'http://', '/')):
            raise ValueError(f'quicklink {name} must be an http(s) URL or absolute path')
    for name in (*snippets, *links):
        if any(char in name for char in ('\n', '\r', '\0', '\x1f')):
            raise ValueError('names cannot contain control separators')
    return snippets, links


def snippets(path=SNIPPETS):
    values, _ = personal_config(path)
    return [('Snippets', name, 'Copy snippet', ('copy', value)) for name, value in values.items()]


def quicklinks(path=SNIPPETS):
    _, values = personal_config(path)
    return [('Quicklinks', name, 'Open quicklink', ('open', target)) for name, target in values.items()]


def registry():
    """Ordered groups; a binding appears once, and only if present in live config."""
    live = shortcuts() + foot_shortcuts()
    priority = {'Open application launcher', 'Focus next window', 'Close focused window',
                'Open terminal', 'Open files', 'Capture full screenshot', 'Capture area screenshot'}
    groups = []
    common = [row for row in live if row[2] in priority and row[1] not in ('⌥Space', 'XF86Search')]
    rank = {'Open application launcher': 0, 'Focus next window': 1, 'Close focused window': 2,
            'Open files': 3, 'Open terminal': 4, 'Capture area screenshot': 5,
            'Capture full screenshot': 6}
    common.sort(key=lambda row: rank[row[2]])
    used = {id(row) for row in common}
    groups.append(('Everyday', common))
    personal = snippets()
    groups.append(('Snippets', personal or [('Snippets', 'Set up snippets', 'Open snippet instructions',
                                             ('open', str(HOME / 'limux/docs/commands.md')))]))
    groups.append(('Quicklinks', [('Quicklinks', 'Home folder', 'Open in file manager', ('open', str(HOME))),
                                  ('Quicklinks', 'Limux project', 'Open in file manager', ('open', str(HOME / 'limux')))]
                   + quicklinks()))
    groups.append(('Utilities', [('Utilities', 'Lorem Ipsum', 'Copy placeholder paragraph', ('copy', LOREM)),
                                 ('Utilities', 'New UUID', 'Copy UUID', ('uuid', None)),
                                 ('Utilities', 'Current date', 'Copy ISO date', ('date', None))]))
    for category in ('Workspaces', 'Windows', 'Gestures', 'Foot', 'Apps', 'Hardware', 'Layout', 'Mouse', 'System'):
        items = [row for row in live if row[0] == category and id(row) not in used]
        if items:
            groups.append((category, items))
    return groups


def display_rows(groups):
    """Rofi rows: plain action-first text; metadata keeps categories searchable."""
    labels, actions = [], []
    for category, items in groups:
        labels.append(f'{category.upper()}\0nonselectable\x1ftrue\x1factive\x1ftrue')
        actions.append(None)
        for _, shortcut, description, action in items:
            # Rofi's tab stop clipped even short keys. Keep the full key in one text run.
            shown = (f'{description} — {shortcut}' if action is None
                     else f'{shortcut} — {description}')
            search_terms = category + (' email address phone signature' if shortcut == 'Set up snippets' else '')
            labels.append(shown + f'\0meta\x1f{search_terms}')
            actions.append(action)
    return labels, actions


def execute(action):
    if action is None:
        return
    kind, value = action
    if kind == 'open':
        subprocess.Popen(['xdg-open', value], start_new_session=True)
        return
    if kind == 'uuid':
        value = str(uuid.uuid4())
    elif kind == 'date':
        value = datetime.date.today().isoformat()
    subprocess.run(['wl-copy', '--', value], check=True)


def preview_theme(tokens_path=TOKENS, candidate=False):
    tokens = tomllib.loads(tokens_path.read_text())
    font = tokens['typography']['sans']
    colors = tokens['colors']
    overrides = tokens['limux_commands_candidate'] if candidate else {}
    metrics = {**tokens['limux_commands'],
               **{key: value for key, value in overrides.items() if key != 'heading_text_color'}}
    quiet = colors[overrides['heading_text_color']] if candidate else colors['text_secondary']
    if not font.replace(' ', '').isalpha() or not quiet.startswith('#') or len(quiet) != 7:
        raise ValueError('invalid Rhapsody heading tokens')
    for name, value in metrics.items():
        minimum = 1 if name in ('width', 'list_lines', 'heading_size') else 0
        if type(value) is not int or not minimum <= value <= (1600 if name == 'width' else 100):
            raise ValueError(f'invalid Commands geometry: {name}')
    heading_states = ('element normal.active, element alternate.active, element selected.active'
                      if candidate else 'element normal.active, element alternate.active')
    heading_text_states = ('element-text normal.active, element-text alternate.active, element-text selected.active'
                           if candidate else 'element-text normal.active, element-text alternate.active')
    base = ('textbox-heading {\n content: "COMMANDS";\n}\n'
            'entry {\n placeholder: "Search commands";\n}\n'
            f'window {{\n width: {metrics["width"]}px;\n}}\n'
            f'listview {{\n lines: {metrics["list_lines"]};\n}}\n'
            f'{heading_states} {{\n'
            f' margin: {metrics["heading_margin_top"]}px 0px 0px 0px;\n'
            f' padding: {metrics["heading_padding_top"]}px {metrics["heading_padding_horizontal"]}px {metrics["heading_padding_bottom"]}px {metrics["heading_padding_horizontal"]}px;\n'
            f' text-color: {quiet};\n' ' }\n'
            f'{heading_text_states} {{\n'
            f' font: "{font} {metrics["heading_size"]}";\n' ' }')
    if not candidate:
        return base
    semantics = tokens['semantics']
    selection = colors[semantics['list_selected_neutral']]
    selected_ink = colors[semantics['on_list_selected_neutral']]
    if not all(value.startswith('#') and len(value) == 7 for value in (selection, selected_ink)):
        raise ValueError('invalid Commands selection tokens')
    return (base + '\n'
            'mainbox {\n children: [ box-search, listview, message ];\n'
            f' spacing: {metrics["mainbox_spacing"]}px;\n}}\n'
            f'window {{\n padding: {metrics["window_padding"]}px;\n}}\n'
            f'inputbar {{\n padding: {metrics["search_padding"]}px;\n}}\n'
            f'element {{\n padding: {metrics["row_padding"]}px;\n border: 0px;\n}}\n'
            'element selected.normal {\n'
            f' background-color: {selection};\n border-color: {selection};\n'
            f' text-color: {selected_ink};\n}}\n'
            'element normal.active, element alternate.active, element selected.active {\n'
            f' background-color: transparent;\n border-color: transparent;\n'
            f' text-color: {quiet};\n cursor: default;\n}}\n')


def appearance_active(path=APPEARANCE_STATE):
    """Read the single activation marker; reject unreviewed appearance drift."""
    if not path.exists() and not path.is_symlink():
        return False
    if path.is_symlink() or not path.is_file() or path.stat().st_uid != os.getuid():
        raise RuntimeError('Commands appearance marker is not an owned regular file')
    if path.stat().st_mode & 0o077:
        raise RuntimeError('Commands appearance marker must have mode 600')
    expected = 'neutral-v1 ' + hashlib.sha256(preview_theme(candidate=True).encode()).hexdigest() + '\n'
    if path.read_text() != expected:
        raise RuntimeError('Commands appearance marker does not match the reviewed candidate')
    return True


def picker_lock():
    """Keep one Commands picker open even if Command+K is pressed repeatedly."""
    lock_dir = HOME / '.cache'
    lock_dir.mkdir(mode=0o700, exist_ok=True)
    lock_path = lock_dir / 'limux-commands-picker.lock'
    fd = os.open(lock_path, os.O_RDWR | os.O_CREAT, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        os.close(fd)
        return None
    return fd


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=['preview', 'candidate', 'list', 'check', 'init-snippets'])
    args = parser.parse_args()
    if args.mode == 'init-snippets':
        SNIPPETS.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        descriptor = os.open(SNIPPETS, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, 'w') as output:
            output.write(EXAMPLE.read_text())
        print(f'Created {SNIPPETS} with dummy values; edit it to add your own snippets')
        return
    groups = registry()
    labels, actions = display_rows(groups)
    if args.mode == 'check':
        print(f'{sum(len(items) for _, items in groups)} commands valid')
        return
    if args.mode == 'list':
        print('\n'.join(labels))
        return
    if not os.environ.get('WAYLAND_DISPLAY'):
        raise RuntimeError('Run preview from Foot in the MangoWM session')
    lock_fd = picker_lock()
    if lock_fd is None:
        return
    theme_override = preview_theme(candidate=args.mode == 'candidate' or
                                   (args.mode == 'preview' and appearance_active()))
    try:
        result = subprocess.run(['rofi', '-dmenu', '-i', '-no-custom', '-no-sort', '-matching', 'fuzzy',
                                 '-format', 'i', '-theme', str(THEME),
                                 '-theme-str', theme_override, '-p', ''],
                                input='\n'.join(labels) + '\n', text=True, capture_output=True)
    finally:
        os.close(lock_fd)
    if result.returncode == 1:
        return  # Escape
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or 'Rofi failed')
    selected = int(result.stdout.strip())
    if not 0 <= selected < len(actions):
        raise RuntimeError('Rofi returned an invalid selection')
    execute(actions[selected])


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as exc:
        print(f'limux-commands: {exc}', file=sys.stderr)
        sys.exit(1)
