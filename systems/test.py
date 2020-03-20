import dlal

audio = dlal.Component('audio')
midi = dlal.Component('midi')

import ctypes
void_p = ctypes.cast(midi.lib.command, ctypes.c_void_p)
func_p = ctypes.cast(void_p, ctypes.CFUNCTYPE(ctypes.c_char_p, ctypes.c_void_p, ctypes.c_char_p))
print(func_p(midi.raw, b'{"name": "asdf"}'))

audio.command('add', str(midi.raw), str(void_p.value))
