#!/usr/bin/env python3
"""Read-only NetworkManager Wi-Fi state, refreshed by Mangobar.

Without options it prints the original text ("Wi-Fi 62%"). Limux's icon display
passes --format with {icon} and {signal}, --levels (one glyph per signal third)
and --off (the glyph for offline or unavailable).
"""
import argparse
import subprocess

parser = argparse.ArgumentParser()
parser.add_argument('--format')
parser.add_argument('--levels', default='')
parser.add_argument('--off', default='')
args = parser.parse_args()
try:
    state = subprocess.check_output(['nmcli', '-g', 'GENERAL.STATE', 'device', 'show', 'wlp3s0'], text=True, timeout=3).strip()
    if state.startswith('100 '):
        rows = subprocess.check_output(['nmcli', '-t', '-f', 'IN-USE,SIGNAL', 'device', 'wifi', 'list', 'ifname', 'wlp3s0', '--rescan', 'no'], text=True, timeout=3)
        signal = next((r.split(':')[1] for r in rows.splitlines() if r.startswith('*:')), None)
        if args.format:
            levels = args.levels or ' '
            icon = levels[min(int(signal or 100) * len(levels) // 101, len(levels) - 1)]
            print(args.format.format(icon=icon, signal=signal or '?').strip())
        else:
            print('Wi-Fi ' + (signal + '%' if signal else 'connected'))
    else:
        print(args.off if args.format else 'Wi-Fi offline')
except (OSError, subprocess.SubprocessError):
    print(args.off if args.format else 'Wi-Fi unavailable')
