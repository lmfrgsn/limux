#!/usr/bin/env python3
"""Stage model-specific speaker data, preserving the upstream signal graph."""
import json
import pathlib
import shutil
import sys
import ctypes
import ctypes.util

source, stage = map(pathlib.Path, sys.argv[1:])
model = source / 'configs/15_1'
graph = json.loads((model / 'graph.json').read_text())
assert graph['capture.props']['node.name'] == 'audio_effect.t2-151-speakers'
assert graph['playback.props']['audio.channels'] in ('4', 4)
assert graph['playback.props']['audio.position'] == ['FL', 'FR', 'RL', 'RR']
nodes = graph['filter.graph']['nodes']
uris = {n['plugin'] for n in nodes if n['type'] == 'lv2'}
assert uris == {
    'https://chadmed.au/bankstown',
    'http://lsp-plug.in/plugins/lv2/compressor_stereo',
    'http://lsp-plug.in/plugins/lv2/loud_comp_mono',
    'http://plugin.org.uk/swh-plugins/fastLookaheadLimiter',
}, 'DSP changed; review its dependencies before installing'
limiter = next(n for n in nodes if n['name'] == 'limiter')
assert limiter['control'] == {'ingain': 0, 'limit': -1, 'release': 0.8}
assert graph['filter.graph']['outputs'] == [
    'convLW:Out', 'convRW:Out', 'convLT:Out', 'convRT:Out']
assert {'output': 'compressor:out_l', 'input': 'limiter:in_1'} in graph['filter.graph']['links']
assert {'output': 'compressor:out_r', 'input': 'limiter:in_2'} in graph['filter.graph']['links']
assert graph['playback.props']['target.object'] == 'alsa_output.platform-sound.RawSpeakers'
stage.mkdir(parents=True, exist_ok=True)
data = stage / '15_1'
data.mkdir(exist_ok=True)
for band in ('tweeters', 'woofers'):
    for suffix, rate in [('44k', 44100), ('48k', 48000), ('96k', 96000)]:
        p = model / f'{band}-{suffix}.wav'
        # FIRs may be float WAVs, which Python's wave module cannot read.
        class Info(ctypes.Structure):
            _fields_ = [('frames', ctypes.c_int64), ('samplerate', ctypes.c_int),
                        ('channels', ctypes.c_int), ('format', ctypes.c_int),
                        ('sections', ctypes.c_int), ('seekable', ctypes.c_int)]
        lib = ctypes.CDLL(ctypes.util.find_library('sndfile'))
        lib.sf_open.argtypes = [ctypes.c_char_p, ctypes.c_int, ctypes.POINTER(Info)]
        lib.sf_open.restype = ctypes.c_void_p
        lib.sf_close.argtypes = [ctypes.c_void_p]
        info = Info()
        handle = lib.sf_open(str(p).encode(), 0x10, ctypes.byref(info))
        assert handle, f'Cannot read FIR: {p}'
        lib.sf_close(handle)
        assert info.samplerate == rate and info.frames > 0 and info.channels == 1
        shutil.copy2(p, data / p.name)
# Keep the DSP input silent as well as the raw output. No gain is raised.
graph['capture.props']['state.default-volume'] = 0.0
graph['capture.props']['state.restore-props'] = False
graph['capture.props']['node.param.Props'] = '{ mute = true }'
graph['capture.props'].pop('channelmix.lock-volumes', None)
# An explicit zero-gain gate keeps every physical output silent independently
# of the adapter's volume/mute implementation. Release requires permission.
for n in nodes:
    if n.get('label') == 'convolver':
        n['config']['gain'] = 0.0
(data / 'graph.json').write_text(json.dumps(graph, indent=2) + '\n')
local_graph = pathlib.Path.home() / '.config/pipewire/t2-151-speakers-locked.json'
local_graph.parent.mkdir(parents=True, exist_ok=True)
local_graph.write_text(json.dumps(graph, indent=2) + '\n')
shutil.copy2(source / 'LICENSE', data / 'LICENSE')
# Match this driver's four-channel UCM node; do not rename cards or touch drivers.
(stage / '51-t2-151-speaker-dsp.conf').write_text('''# Managed T2 MacBookPro15,1 speaker DSP; audio remains locked silent.
monitor.alsa.rules = [
  {
    matches = [ { alsa.card_name = "Apple T2 Audio" node.name = "~alsa_output.*.HiFi__Speaker__sink" } ]
    actions = { update-props = {
      node.name = "alsa_output.platform-sound.RawSpeakers"
      node.description = "Raw T2 speakers (locked; do not use)"
      node.param.Props = "{ mute = true, volume = 0.0 }"
      channelmix.lock-volumes = true
      state.restore-props = false
      priority.session = 1
    } }
  }
]
node.software-dsp.rules = [
  {
    matches = [ { node.name = "alsa_output.platform-sound.RawSpeakers" } ]
    actions = { create-filter = {
      filter-path = "/home/liam/.config/pipewire/t2-151-speakers-locked.json"
      hide-parent = true
    } }
  }
]
wireplumber.profiles = { main = { node.software-dsp = required } }
''')
