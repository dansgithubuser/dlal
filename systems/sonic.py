import dlal

import atexit

audio = dlal.Audio()
comm = dlal.Comm()
midi = dlal.Midi()
gain = dlal.Gain()
sonic = dlal.Sonic()
buf = dlal.Buf()
tape = dlal.Tape()

gain.set(0)
sonic.i1(0, 1)

audio.add(comm)
audio.add(midi)
audio.add(gain)
audio.add(sonic)
audio.add(buf)
audio.add(tape)

midi.connect(sonic)
gain.connect(buf)
sonic.connect(buf)
buf.connect(audio)
buf.connect(tape)

audio.start()
dlal.queue_set(comm)
dlal.serve()
atexit.register(lambda: audio.stop())
