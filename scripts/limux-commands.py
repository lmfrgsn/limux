#!/usr/bin/env python3
"""Limux Commands: read-only shortcut index and small action registry."""
import argparse
import configparser
import datetime
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
EXAMPLE = Path(__file__).resolve().parents[1] / 'examples/commands.toml'
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


def snippets(path=SNIPPETS):
    if not path.exists():
        return []
    if path.stat().st_mode & 0o077:
        raise ValueError(f'{path} must be private (chmod 600)')
    data = tomllib.loads(path.read_text())
    rows = data.get('snippets', {})
    if not isinstance(rows, dict) or any(not isinstance(k, str) or not isinstance(v, str) for k, v in rows.items()):
        raise ValueError('snippets must be a table of text values')
    return [('Snippets', name, 'Copy snippet', ('copy', value)) for name, value in rows.items()]


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
                                  ('Quicklinks', 'Limux project', 'Open in file manager', ('open', str(HOME / 'limux')))]))
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
        labels.append(f'{category.upper()}\0nonselectable\x1ftrue')
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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=['preview', 'list', 'check', 'init-snippets'])
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
        print(f'{sum(len(items) for _, items in groups)} commands valid; Command+K remains unassigned')
        return
    if args.mode == 'list':
        print('\n'.join(labels))
        return
    if not os.environ.get('WAYLAND_DISPLAY'):
        raise RuntimeError('Run preview from Foot in the MangoWM session')
    theme_override = ('textbox-heading {\n content: "COMMANDS";\n}\n'
                      'entry {\n placeholder: "Search commands";\n}\n'
                      'window {\n width: 700px;\n}\n'
                      'listview {\n lines: 11;\n}')
    result = subprocess.run(['rofi', '-dmenu', '-i', '-no-custom', '-no-sort', '-matching', 'fuzzy',
                             '-format', 'i', '-theme', str(THEME),
                             '-theme-str', theme_override, '-p', ''],
                            input='\n'.join(labels) + '\n', text=True, capture_output=True)
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
