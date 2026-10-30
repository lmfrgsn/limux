#!/usr/bin/env python3
"""Initialize only the MacBookPro15,1 DSP path, leaving playback muted."""
import json
from pathlib import Path
import subprocess as sp
import time

assert Path('/sys/class/dmi/id/product_name').read_text().strip() == 'MacBookPro15,1'
name = 'audio_effect.t2-151-speakers'
for _ in range(50):
    objects = json.loads(sp.check_output(['pw-dump']))
    nodes = [o for o in objects if o['type'].endswith(':Node') and
             o.get('info', {}).get('props', {}).get('node.name') == name]
    if len(nodes) == 1:
        break
    for obj in objects:
        if obj['type'].endswith(':Device') and obj.get('info', {}).get('props', {}).get('alsa.card_name') == 'Apple T2 Audio':
            routes = obj['info'].get('params', {}).get('Route', [])
            if any(r.get('name') == '[Out] Headphones' and r.get('direction') == 'Output' for r in routes):
                print('Headphones active; leaving headphone routing unchanged.')
                raise SystemExit(0)
    time.sleep(.2)
else:
    raise SystemExit('DSP speaker sink is unavailable; no hardware gain changed')
sp.run(['pactl', 'set-sink-mute', name, '1'], check=True)
sp.run(['pactl', 'set-sink-volume', name, '0%'], check=True)
sp.run(['pw-cli', 'set-param', str(nodes[0]['id']), 'Props', '{ volume = 1.0 }'],
       check=True, stdout=sp.DEVNULL)
# The hidden raw adapter is a fixed-unity hardware stage, as required by the
# upstream profile. Its input is the processed DSP, never a direct test player.
device = next(o for o in objects if o['type'].endswith(':Device') and
              o.get('info', {}).get('props', {}).get('alsa.card_name') == 'Apple T2 Audio')
route = next(r for r in device['info']['params']['Route'] if
             r.get('name') == '[Out] Speaker' and r.get('direction') == 'Output')
value = {'index': route['index'], 'device': route['device'], 'save': True,
         'props': {'mute': False, 'channelVolumes': [1.0, 1.0, 1.0, 1.0]}}
sp.run(['pw-cli', 'set-param', str(device['id']), 'Route', json.dumps(value)],
       check=True, stdout=sp.DEVNULL)
sp.run(['pactl', 'set-default-sink', name], check=True)
sp.run(['pactl', 'set-sink-volume', name, '25%'], check=True)
sp.run(['pactl', 'set-sink-mute', name, '1'], check=True)
print('T2 model-specific DSP ready: 25%, muted. Hardware adapter remains hidden.')
