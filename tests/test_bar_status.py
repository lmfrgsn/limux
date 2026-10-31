import copy
import importlib.util
import json
from pathlib import Path
import re
import sys
import tomllib
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
import bar_status as b  # noqa: E402

spec = importlib.util.spec_from_file_location('agent_status', ROOT/'scripts/agent-status.py')
agent_status = importlib.util.module_from_spec(spec)
spec.loader.exec_module(agent_status)
THEME = tomllib.loads((ROOT/'themes/rhapsody.toml').read_text())
LIVE = {'modules-left': ['workspaces', 'window'], 'workspaces': {'hide-empty': False},
        'modules-right': ['tray', 'custom/wifi', 'battery', 'pulseaudio'],
        'custom/wifi': {'exec': 'python3 /home/x/.local/share/limux/mangobar/wifi-status.py', 'interval': 5},
        'battery': {'device': 'BAT0', 'format': 'Bat {percent}%{icon}'},
        'pulseaudio': {'format': 'Vol {volume}%', 'on-click': 'mute'}}


class BarStatusTests(unittest.TestCase):
    def test_agent_modules_sit_between_tray_and_wifi_and_match_the_writer(self):
        data = b.modules(THEME, LIVE, '/repo/scripts/agent-status.py')
        right = data['modules-right']
        self.assertEqual(right[0], 'tray')
        self.assertEqual(right[-3:], ['custom/wifi', 'battery', 'pulseaudio'])
        self.assertEqual(len(right), 4 + len(b.AGENTS) * len(b.SLOTS))
        self.assertEqual([s for s, _ in b.SLOTS], list(agent_status.SLOTS))
        self.assertEqual(tuple(b.AGENTS), tuple(agent_status.AGENTS))
        module = data['custom/agent-claude-icon-input']
        self.assertEqual(module['signal'], THEME['bar_status']['refresh_signal'])
        self.assertIn('focus claude', module['on-click'])
        # Only the working icon rotates.
        spinning = [k for k, v in data.items() if isinstance(v, dict) and 'spin-period' in v]
        self.assertEqual(spinning, [f'custom/agent-{a}-icon-spin' for a in b.AGENTS])
        self.assertEqual(data['custom/agent-codex-icon-spin']['spin-period'],
                         THEME['bar_status']['spin_period'])
        self.assertTrue(data['workspaces']['hide-empty'])
        self.assertNotIn('window', data['modules-left'])
        # Mangobar keeps CSS selectors and click actions in 32-byte buffers.
        self.assertTrue(all(len(m.replace('custom/', 'custom-')) <= 31 for m in right))
        # Regenerating does not duplicate agent modules.
        self.assertEqual(b.modules(THEME, data, '/repo/scripts/agent-status.py')['modules-right'], right)

    def test_icon_value_display_keeps_behaviour_and_wifi_script(self):
        data = b.modules(THEME, LIVE, '/s')
        self.assertTrue(data['custom/wifi']['exec'].startswith(LIVE['custom/wifi']['exec'] + ' --levels'))
        self.assertEqual(data['pulseaudio']['on-click'], 'mute')
        self.assertEqual(data['battery']['device'], 'BAT0')
        # Mangobar's own banding (percent * n // 101) lands on the nearest quarter.
        icons = data['battery']['icons']
        level = lambda pct: icons[min(pct * len(icons) // 101, len(icons) - 1)]  # noqa: E731
        bars = [b.TABLER[n] for n in ('battery', 'battery-1', 'battery-2', 'battery-3', 'battery-4')]
        starts = {0: 0, 13: 1, 38: 2, 64: 3, 89: 4}
        for pct in range(101):
            expected = bars[max(v for k, v in starts.items() if k <= pct)]
            self.assertEqual(level(pct), expected, pct)
        self.assertEqual(data['battery']['format'], '{icon} {percent}%')
        self.assertEqual(LIVE['battery']['format'], 'Bat {percent}%{icon}')  # input untouched

    def test_text_and_icons_displays(self):
        theme = copy.deepcopy(THEME)
        theme['bar_status']['display'] = 'text'
        self.assertEqual(b.modules(theme, LIVE, '/s')['battery'], LIVE['battery'])
        theme['bar_status']['display'] = 'icons'
        self.assertEqual(b.modules(theme, LIVE, '/s')['battery']['format'], '{icon}')

    def test_css_spacing_follows_tokens(self):
        css = b.css(THEME)
        t = THEME['bar_status']
        self.assertIn(f'#custom-wifi {{ padding-left: {t["item_gap"] // 2 + t["group_gap"] - t["item_gap"]}px;', css)
        self.assertIn(f'padding-right: {t["edge"]}px; }}', css)
        icon = re.search(r'#custom-agent-codex-icon \{[^}]*\}', css).group()
        self.assertIn(f'padding-left: {t["item_gap"] // 2}px; padding-right: {t["pair_gap"] // 2}px;', icon)
        self.assertNotIn('padding: ', css)  # Mangobar reads only two padding values
        self.assertIn(THEME['colors']['workspace_orange'], re.search(r'#custom-agent-claude-icon-input \{[^}]*\}', css).group())

    def test_invalid_tokens_are_refused(self):
        for key, value in (('display', 'fancy'), ('item_gap', 21), ('group_gap', 10), ('refresh_signal', 40),
                           ('spin_period', 100)):
            theme = copy.deepcopy(THEME)
            theme['bar_status'][key] = value
            with self.assertRaises(ValueError):
                b.tokens(theme)

    def test_glyphs_match_between_writer_and_generator(self):
        self.assertTrue(all('' <= g <= '' for g in agent_status.GLYPHS.values()))
        self.assertTrue(all('' <= g <= '' for g in b.TABLER.values()))
        json.dumps(b.modules(THEME, LIVE, '/s'), ensure_ascii=False)


if __name__ == '__main__':
    unittest.main()
