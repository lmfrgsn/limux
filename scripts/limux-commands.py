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
    rows = shortcuts() + foot_shortcuts() + snippets()
    rows += [('Quicklinks', 'Home folder', 'Open in file manager', ('open', str(HOME))),
             ('Quicklinks', 'Limux project', 'Open in file manager', ('open', str(HOME / 'limux'))),
             ('Utilities', 'Lorem Ipsum', 'Copy placeholder paragraph', ('copy', LOREM)),
             ('Utilities', 'New UUID', 'Copy UUID', ('uuid', None)),
             ('Utilities', 'Current date', 'Copy ISO date', ('date', None))]
    return rows


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
    parser.add_argument('mode', choices=['preview', 'list', 'check'])
    args = parser.parse_args()
    rows = registry()
    if args.mode == 'check':
        print(f'{len(rows)} commands valid; Command+K remains unassigned')
        return
    labels = [f'{shortcut:<22}  {category:<11}  {description}' for category, shortcut, description, _ in rows]
    if args.mode == 'list':
        print('\n'.join(labels))
        return
    if not os.environ.get('WAYLAND_DISPLAY'):
        raise RuntimeError('Run preview from Foot in the MangoWM session')
    result = subprocess.run(['rofi', '-dmenu', '-i', '-no-custom', '-matching', 'fuzzy',
                             '-format', 'i', '-theme', str(THEME),
                             '-theme-str', 'textbox-heading {\n content: "COMMANDS";\n}\nentry {\n placeholder: "Search commands";\n}\nelement-text {\n font: "DejaVu Sans Mono 11";\n}',
                             '-p', ''], input='\n'.join(labels) + '\n', text=True, capture_output=True)
    if result.returncode == 1:
        return  # Escape
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or 'Rofi failed')
    execute(rows[int(result.stdout.strip())][3])


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as exc:
        print(f'limux-commands: {exc}', file=sys.stderr)
        sys.exit(1)
