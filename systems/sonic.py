import dlal

import atexit

audio = dlal.Audio()
midi = dlal.Midi()
sonic = dlal.Sonic()
comm = dlal.Comm()

audio.add(midi)
audio.add(sonic)
audio.add(comm)

midi.connect(sonic)
sonic.connect(audio)

audio.start()
atexit.register(lambda: audio.stop())
