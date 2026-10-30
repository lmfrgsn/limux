#!/usr/bin/env python3
"""Read-only NetworkManager Wi-Fi state, refreshed by Mangobar."""
import subprocess
try:
    state = subprocess.check_output(['nmcli', '-g', 'GENERAL.STATE', 'device', 'show', 'wlp3s0'], text=True, timeout=3).strip()
    if state.startswith('100 '):
        rows = subprocess.check_output(['nmcli', '-t', '-f', 'IN-USE,SIGNAL', 'device', 'wifi', 'list', 'ifname', 'wlp3s0', '--rescan', 'no'], text=True, timeout=3)
        signal = next((r.split(':')[1] for r in rows.splitlines() if r.startswith('*:')), None)
        print('Wi-Fi ' + (signal + '%' if signal else 'connected'))
    else:
        print('Wi-Fi offline')
except (OSError, subprocess.SubprocessError):
    print('Wi-Fi unavailable')
