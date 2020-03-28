import dlal

import atexit

audio = dlal.Audio()
comm = dlal.Comm()
midi = dlal.Midi()
gain = dlal.Gain()
sonic = dlal.Sonic()
buf = dlal.Buf()

gain.set(0)

audio.add(comm)
audio.add(midi)
audio.add(gain)
audio.add(sonic)
audio.add(buf)

midi.connect(sonic)
gain.connect(buf)
sonic.connect(buf)
buf.connect(audio)

audio.start()
dlal.queue_set(comm)
dlal.serve()
atexit.register(lambda: audio.stop())
