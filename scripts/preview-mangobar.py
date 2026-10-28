#!/usr/bin/env python3
"""Capture a temporary candidate alongside the original bar; never apply it."""
import subprocess
import time
from pathlib import Path

root = Path(__file__).resolve().parents[1]
out = root / 'build/rhapsody-candidate2'
subprocess.run(['python3', str(root/'scripts/theme.py'), 'render', str(root/'themes/rhapsody.toml'), '--output', str(out)], check=True)
# Fail before launch if the session cannot capture screenshots.
try:
    subprocess.run(['grim', str(out/'before.png')], check=True)
except (OSError, subprocess.CalledProcessError):
    raise SystemExit('Cannot capture the Wayland display. Run this script from Foot in the desktop session. No preview was started.')
bar = subprocess.Popen([str(Path.home()/'.local/bin/mangobar'), '-c', str(Path.home()/'.config/mangobar/config.jsonc'), '-s', str(out/'mangobar.css')])
try:
    time.sleep(3)
    if bar.poll() is not None:
        raise RuntimeError('Candidate exited before capture')
    subprocess.run(['grim', str(out/'candidate.png')], check=True)
    print('Candidate visible for 20 seconds; Ctrl+C closes only this preview.', flush=True)
    time.sleep(20)
finally:
    if bar.poll() is None:
        bar.terminate()
        try:
            bar.wait(timeout=5)
        except subprocess.TimeoutExpired:
            bar.kill()
            bar.wait()
    print(f'Screenshots: {out}. Original bar and its files untouched.')
