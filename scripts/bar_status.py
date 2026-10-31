"""Bar status readings and agent indicators from [bar_status] tokens: Mangobar
module definitions and CSS for the Quiet Workspace Strip. Needs Tabler Icons as
the bar font's fallback and patches/mangobar/03-hide-empty-custom-modules.patch,
so a state module with no text takes no space, and 04-spin-custom-modules.patch,
so the working icon rotates, and 05-icon-glyphs.patch, which centres icons on
the text and scales the Wi-Fi and battery glyphs."""
import re

# Tabler Icons 3.49.0 code points (dist/tabler-icons.css).
TABLER = {
    'wifi-1': '', 'wifi-2': '', 'wifi': '', 'wifi-off': '',
    'battery': '', 'battery-1': '', 'battery-2': '', 'battery-3': '',
    'battery-4': '', 'battery-charging': '',
    'volume-2': '', 'volume': '', 'volume-3': '',
}
AGENTS = ('codex', 'claude')
# Must match SLOTS in scripts/agent-status.py; each slot is one coloured module.
# The working icon has its own slot so only it rotates (spin_period).
SLOTS = (('icon', 'agent_quiet'), ('icon-spin', 'agent_quiet'), ('icon-input', 'agent_input'),
         ('icon-error', 'agent_error'),
         ('name', 'agent_quiet'), ('name-input', 'agent_name_alert'))
DISPLAYS = ('text', 'icon-value', 'icons')


def tokens(theme):
    t = theme['bar_status']
    if t['display'] not in DISPLAYS:
        raise ValueError('invalid bar_status display')
    if not re.fullmatch(r'[\w -]+', t['icon_font']):
        raise ValueError('invalid bar_status icon font')
    for key in ('pair_gap', 'item_gap', 'group_gap', 'edge'):
        if type(t[key]) is not int or not 0 <= t[key] <= 64 or t[key] % 2:
            raise ValueError(f'invalid bar_status {key}: even 0–64 px')
    if t['group_gap'] < t['item_gap']:
        raise ValueError('bar_status group gap must not be smaller than the item gap')
    if type(t['refresh_signal']) is not int or not 1 <= t['refresh_signal'] <= 20:
        raise ValueError('invalid bar_status refresh signal')
    for key in ('wifi_icon_scale', 'battery_icon_scale'):
        if type(t[key]) not in (int, float) or not 1 <= t[key] <= 2:
            raise ValueError(f'invalid bar_status {key}: 1–2')
    if type(t['spin_period']) is not int or not 400 <= t['spin_period'] <= 4000:
        raise ValueError('invalid bar_status spin period: 400–4000 ms')
    for key in ('agent_quiet', 'agent_name_alert', 'agent_input', 'agent_error'):
        if not re.fullmatch(r'#[0-9A-Fa-f]{6}', theme['colors'][t[key]]):
            raise ValueError(f'invalid bar_status colour: {key}')
    return t


def modules(theme, data, agent_script, runtime='$XDG_RUNTIME_DIR/limux/agents/bar'):
    """Return a copy of the bar config with agent modules and the status display."""
    t = tokens(theme)
    data = dict(data)
    right = [m for m in data['modules-right'] if not m.startswith('custom/agent-')]
    agents = [f'custom/agent-{agent}-{slot}' for agent in AGENTS for slot, _ in SLOTS]
    data['modules-right'] = right[:right.index('custom/wifi')] + agents + right[right.index('custom/wifi'):]
    for agent in AGENTS:
        for slot, _ in SLOTS:
            data[f'custom/agent-{agent}-{slot}'] = {
                'exec': f'cat "{runtime}/{agent}-{slot}" 2>/dev/null', 'interval': 30,
                'signal': t['refresh_signal'], 'format': '{}', 'on-click': f'python3 {agent_script} focus {agent}'}
            if slot == 'icon-spin':
                data[f'custom/agent-{agent}-{slot}']['spin-period'] = t['spin_period']
    if t['display'] == 'text':
        return data
    sep = ' ' if t['display'] == 'icon-value' else ''
    value = (lambda v: v) if t['display'] == 'icon-value' else (lambda v: '')
    g = TABLER
    # Keep the configured Wi-Fi script; only its output format changes.
    script = data['custom/wifi']['exec'].split(' --')[0]
    data['custom/wifi'] = dict(data['custom/wifi'], exec=(
        f"{script} --levels {g['wifi-1']}{g['wifi-2']}{g['wifi']} --off {g['wifi-off']} "
        f"--format '{{icon}}{sep}{value('{signal}%')}'"))
    data['battery'] = dict(data['battery'], **{
        'format': f'{{icon}}{sep}{value("{percent}%")}',
        'icon-charging': g['battery-charging'], 'icon-full': g['battery-4'], 'icon-discharging': '',
        'icons': [g['battery'], g['battery-1'], g['battery-2'], g['battery-3'], g['battery-4']]})
    data['pulseaudio'] = dict(data['pulseaudio'], **{
        'format': f'{{icon}}{sep}{value("{volume}%")}', 'format-muted': '{icon}',
        'icon-muted': g['volume-3'], 'icons': [g['volume-2'], g['volume']]})
    # Short, wide glyphs drawn larger so they match the text (05-icon-glyphs.patch).
    scales = {**{g[n]: t['wifi_icon_scale'] for n in TABLER if n.startswith('wifi')},
              **{g[n]: t['battery_icon_scale'] for n in TABLER if n.startswith('battery')}}
    scales = {glyph: k for glyph, k in scales.items() if k != 1}
    if scales:
        data['glyph-scale'] = scales
    else:
        data.pop('glyph-scale', None)
    return data


def css(theme):
    """CSS appended after the Quiet Workspace Strip rules."""
    t, c = tokens(theme), theme['colors']
    half_pair, half_item = t['pair_gap'] // 2, t['item_gap'] // 2
    group = half_item + t['group_gap'] - t['item_gap']
    lines = ['/* Bar status and agent indicators: [bar_status] tokens. */']
    for agent in AGENTS:
        for slot, colour in SLOTS:
            left, right = (half_item, half_pair) if slot.startswith('icon') else (half_pair, half_item)
            lines.append(f'#custom-agent-{agent}-{slot} {{ color: {c[t[colour]]}; background: {c["surface"]}; '
                         f'padding-left: {left}px; padding-right: {right}px; }}')
    if t['display'] != 'text':
        lines += [f'#custom-wifi {{ padding-left: {group}px; padding-right: {half_item}px; }}',
                  f'#battery {{ padding-left: {half_item}px; padding-right: {half_item}px; }}',
                  f'#volume {{ padding-left: {half_item}px; padding-right: {t["edge"]}px; }}']
    return '\n'.join(lines) + '\n'


def fontconfig(theme):
    """User fontconfig rule: the icon font follows the interface font as its
    fallback, so the bar's single font draws Tabler's private-use glyphs."""
    t = tokens(theme)
    sans = theme['typography']['sans']
    return ('<?xml version="1.0"?>\n<!DOCTYPE fontconfig SYSTEM "urn:fontconfig:fonts.dtd">\n'
            '<!-- Generated by Limux from themes/rhapsody.toml ([bar_status]); '
            'scripts/activate-bar-status.py owns this file. -->\n<fontconfig>\n'
            f'  <match target="pattern">\n    <test name="family"><string>{sans}</string></test>\n'
            f'    <edit name="family" mode="append" binding="strong"><string>{t["icon_font"]}</string></edit>\n'
            '  </match>\n</fontconfig>\n')
