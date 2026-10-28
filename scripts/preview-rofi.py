#!/usr/bin/env python3
"""Preview the generated Rofi theme without writing live configuration.

Uses existing drun behaviour. Escape cancels; selecting an app launches it as
usual. Only this invocation is terminated after 45 seconds. No autostart edits.
"""
from pathlib import Path
import os
import subprocess
import time


def main():
    root = Path(__file__).resolve().parents[1]
    out = root/'build/rofi-candidate2'
    subprocess.run(['python3', str(root/'scripts/theme.py'), 'render',
                    str(root/'themes/rhapsody.toml'), '--output', str(out)], check=True)
    command = ['rofi', '-config', str(Path.home()/'.config/rofi/config.rasi'),
               '-theme', str(out/'rofi.rasi')]
    with (out/'parsed.rasi').open('w') as parsed:
        subprocess.run(command + ['-dump-theme'], stdout=parsed, check=True)
    processes = subprocess.run(['pgrep', '-u', str(os.getuid()), '-x', 'rofi'], capture_output=True)
    if processes.returncode not in (0, 1):
        raise RuntimeError('Could not check existing Rofi processes')
    if processes.returncode == 0:
        raise RuntimeError('An existing Rofi is open; close it before this preview')
    try:
        subprocess.run(['grim', str(out/'before.png')], check=True)
    except (OSError, subprocess.CalledProcessError):
        raise RuntimeError('Cannot capture Wayland. Run from Foot in the desktop session; no preview started.')
    with (out/'preview.log').open('w') as log:
        app = subprocess.Popen(command + ['-show', 'drun'], stdout=log, stderr=subprocess.STDOUT)
        try:
            time.sleep(1)
            if app.poll() is None:
                subprocess.run(['grim', str(out/'candidate.png')], check=True)
                print('Rofi preview: Escape closes; normal app selection works. Timeout: 45 seconds.', flush=True)
                try:
                    app.wait(timeout=44)
                except subprocess.TimeoutExpired:
                    pass
            elif app.returncode not in (0, 1):
                raise RuntimeError(f'Rofi exited with {app.returncode}; see {out}/preview.log')
        finally:
            if app.poll() is None:
                app.terminate()
                try:
                    app.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    app.kill()
                    app.wait()
    print(f'Preview closed; permanent Rofi configuration untouched. Artifacts: {out}')


if __name__ == '__main__':
    try:
        main()
    except (OSError, RuntimeError, subprocess.SubprocessError) as exc:
        raise SystemExit(str(exc))
