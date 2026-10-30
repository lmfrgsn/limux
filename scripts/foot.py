"""Foot 1.28 appearance adapter. No bindings, shell or window behaviour."""
import re
from mangobar import contrast


def palette(theme):
    f = theme['foot']
    colors = dict(theme['colors'])
    if set(colors) & set(f['colors']):
        raise ValueError('Foot colors must not replace shared tokens')
    colors.update(f['colors'])
    colors.update({role: colors[name] for role, name in theme['semantics'].items()
                   if role in ('terminal_cursor', 'on_terminal_cursor',
                               'terminal_match', 'on_terminal_match')})
    for value in colors.values():
        if not isinstance(value, str) or not re.fullmatch(r'#[0-9A-Fa-f]{6}', value):
            raise ValueError('invalid Foot color')
    for name, (source, destination, amount) in f['blends'].items():
        if name in colors or type(amount) not in (int, float) or not 0 <= amount <= 1:
            raise ValueError('invalid Foot blend')
        a, b = colors[source], colors[destination]
        colors[name] = '#' + ''.join(f'{round(int(a[i:i+2], 16) * (1-amount) + int(b[i:i+2], 16) * amount):02X}' for i in (1, 3, 5))
    return colors


def settings(theme):
    f, c = theme['foot'], palette(theme)
    if not re.fullmatch(r'[\w .-]+', f['font']):
        raise ValueError('invalid Foot font')
    for key, low, high, kinds in [('font_size', 8, 32, (int, float)), ('padding', 0, 32, (int,))]:
        if type(f[key]) not in kinds or not low <= f[key] <= high:
            raise ValueError(f'invalid Foot {key}')
    if len(f['regular']) != 8 or len(f['bright']) != 8:
        raise ValueError('Foot requires eight regular and bright colors')
    # ANSI black is a background/inverse role, not readable body text on graphite.
    for name in [f['foreground'], f['secondary'], *f['regular'][1:], *f['bright']]:
        if contrast(c[name], c[f['background']]) < 4.5:
            raise ValueError(f'insufficient Foot text contrast: {name}')
    for role in ('selection', 'cursor'):
        if contrast(c[f[role + '_foreground']], c[f[role + '_background']]) < 4.5:
            raise ValueError(f'insufficient Foot {role} contrast')
    native = {name.replace('_', '-'): c[f[name]][1:] for name in (
        'foreground', 'background', 'selection_foreground', 'selection_background')}
    native['cursor'] = ' '.join(c[f['cursor_' + role]][1:] for role in ('foreground', 'background'))
    for kind in ('regular', 'bright'):
        native.update({f'{kind}{i}': c[name][1:] for i, name in enumerate(f[kind])})
    def pair(ink, surface):
        if contrast(c[ink], c[surface]) < 4.5:
            raise ValueError('insufficient Foot indicator contrast')
        return f'{c[ink][1:]} {c[surface][1:]}'
    s = theme['semantics']
    native.update({
        'jump-labels': pair(s['on_terminal_match'], s['terminal_match']),
        'search-box-match': pair(s['on_terminal_match'], s['terminal_match']),
        'search-box-no-match': pair(s['on_urgent'], s['urgent']),
        'scrollback-indicator': pair(f['background'], f['secondary']),
        'urls': c[s['terminal_match']][1:], 'alpha': '1.0',
    })
    return {'main': {'font': f"{f['font']}:size={f['font_size']}",
                     'pad': f"{f['padding']}x{f['padding']}",
                     'initial-color-theme': 'dark'},
            'cursor': {'style': 'block', 'unfocused-style': 'hollow', 'blink': 'no'},
            'colors-dark': native}


def render(theme):
    return '# Generated Foot appearance candidate; do not replace your live config.\n' + '\n'.join(
        f'[{section}]\n' + ''.join(f'{key}={value}\n' for key, value in values.items())
        for section, values in settings(theme).items())


def overrides(theme):
    """Same settings as native fragment, layered onto the existing behaviour file."""
    return [arg for section, values in settings(theme).items()
            for key, value in values.items() for arg in ('-o', f'{section}.{key}={value}')]
