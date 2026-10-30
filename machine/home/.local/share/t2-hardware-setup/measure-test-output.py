#!/usr/bin/env python3
"""Measure the explicitly targeted digital sink monitor; no microphone input."""
import ctypes as c
import ctypes.util
import json
from pathlib import Path
import sys

class Info(c.Structure):
    _fields_ = [('frames', c.c_int64), ('samplerate', c.c_int),
                ('channels', c.c_int), ('format', c.c_int),
                ('sections', c.c_int), ('seekable', c.c_int)]

lib = c.CDLL(ctypes.util.find_library('sndfile'))
lib.sf_open.argtypes = [c.c_char_p, c.c_int, c.POINTER(Info)]
lib.sf_open.restype = c.c_void_p
lib.sf_readf_float.argtypes = [c.c_void_p, c.POINTER(c.c_float), c.c_int64]
lib.sf_readf_float.restype = c.c_int64
lib.sf_close.argtypes = [c.c_void_p]
path = Path(sys.argv[1]); info = Info()
handle = lib.sf_open(str(path).encode(), 0x10, c.byref(info))
assert handle, 'Cannot read digital monitor capture'
try:
    assert info.channels == 4 and 0 < info.frames <= 480000
    data = (c.c_float * (info.frames * info.channels))()
    frames = lib.sf_readf_float(handle, data, info.frames)
finally:
    lib.sf_close(handle)
peaks = [max(abs(data[i]) for i in range(ch, frames * 4, 4)) for ch in range(4)]
result = {'frames': frames, 'rate': info.samplerate, 'channel_peaks': peaks,
          'digital_signal_present': any(x > 1e-7 for x in peaks)}
path.with_suffix('.json').write_text(json.dumps(result, indent=2) + '\n')
print('Digital speaker-monitor measurement:', json.dumps(result))
