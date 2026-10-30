#!/usr/bin/env python3
"""Temporarily mute existing inputs of the DSP under test; preserve app state."""
import json
from pathlib import Path
import subprocess
import sys

mode, filename = sys.argv[1:]
path = Path(filename)
saved = json.loads(path.read_text()) if path.exists() else {}
inputs = json.loads(subprocess.check_output(['pactl', '-f', 'json', 'list', 'sink-inputs']))
if mode == 'mute':
    sinks = json.loads(subprocess.check_output(['pactl', '-f', 'json', 'list', 'sinks']))
    indices = {s['index'] for s in sinks if s['name'] == 'audio_effect.t2-151-speakers'}
    for stream in inputs:
        if stream['sink'] not in indices:
            continue
        key = str(stream['index'])
        if key not in saved:
            saved[key] = bool(stream['mute'])
            # Write before muting so cleanup can recover from interruptions.
            path.write_text(json.dumps(saved))
        subprocess.run(['pactl', 'set-sink-input-mute', key, '1'], check=True)
        print('Temporarily muted:', stream.get('properties', {}).get('application.name', key))
elif mode == 'restore':
    active = {str(s['index']) for s in inputs}
    for key, mute in saved.items():
        if key in active:
            subprocess.run(['pactl', 'set-sink-input-mute', key, str(int(mute))], check=True)
else:
    raise SystemExit('Unknown operation')
