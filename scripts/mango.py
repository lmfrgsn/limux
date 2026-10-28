"""MangoWM visual-only adapter and lossless replacement of owned values."""
import re

METRICS = ('border_px', 'border_radius', 'gap_inner_horizontal', 'gap_inner_vertical',
           'gap_outer_horizontal', 'gap_outer_vertical')
COLORS = ('root_color', 'border_color', 'focus_color', 'urgent_color', 'drop_color',
          'split_color', 'maximized_screen_color', 'scratchpad_color', 'global_color', 'overlay_color')
KEYS = METRICS + COLORS
LINE = re.compile(rb'(?m)^([ \t]*)([a-z_]+)([ \t]*=[ \t]*)([^#\r\n]*?)([ \t]*(?:#[^\r\n]*)?)(\r?)$')


def values(theme):
    t, colors = theme['mango'], theme['colors']
    result = {}
    for key in METRICS:
        n = t[key]
        if type(n) is not int or not 0 <= n <= 64:
            raise ValueError(f'invalid Mango geometry: {key}')
        result[key] = str(n)
    alpha = t['drop_alpha']
    if type(alpha) is not int or not 0 <= alpha <= 255:
        raise ValueError('invalid drop alpha')
    for key in COLORS:
        color = colors[t[key]]
        if not re.fullmatch(r'#[0-9a-fA-F]{6}', color):
            raise ValueError(f'invalid Mango colour: {key}')
        result[key] = '0x' + color[1:] + (f'{alpha:02X}' if key == 'drop_color' else 'FF')
    return result


def validate_values(replacements):
    if set(replacements) != set(KEYS):
        raise ValueError('Mango replacements must contain exactly the owned visual keys')
    for key, value in replacements.items():
        if key in METRICS:
            if not re.fullmatch(r'\d{1,2}', value) or not 0 <= int(value) <= 64:
                raise ValueError(f'invalid Mango geometry: {key}')
        elif not re.fullmatch(r'0x[0-9a-fA-F]{8}', value):
            raise ValueError(f'invalid Mango RGBA: {key}')


def extract(config):
    found = {}
    for match in LINE.finditer(config):
        key = match[2].decode()
        if key in ('source', 'source_optional'):
            raise ValueError('Included configs require ownership review before visual replacement')
        if key in KEYS:
            if key in found:
                raise ValueError(f'duplicate Mango visual setting: {key}')
            found[key] = match[4].decode()
    validate_values(found)
    return found


def merge(config, replacements):
    extract(config)  # Refuse missing/duplicate keys and hidden sources.
    validate_values(replacements)
    def replace(match):
        key = match[2].decode()
        if key not in replacements:
            return match[0]
        return b''.join((match[1], match[2], match[3], replacements[key].encode(), match[5], match[6]))
    return LINE.sub(replace, config)


def render(theme):
    v = values(theme)
    validate_values(v)
    return '# Generated MangoWM appearance fragment; not a standalone config.\n' + ''.join(f'{key}={v[key]}\n' for key in KEYS)
