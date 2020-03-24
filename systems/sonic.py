import dlal

import atexit

audio = dlal.Audio()
midi = dlal.Midi()
sonic = dlal.Sonic()

audio.add(midi)
audio.add(sonic)

midi.connect(sonic)
sonic.connect(audio)

audio.command('start')
atexit.register(lambda: audio.command('stop'))
