import dlal

audio = dlal.Audio()
comm = dlal.Comm()
midi = dlal.Midi()
gain = dlal.Gain()
buf = dlal.Buf()
tape = dlal.Tape(1 << 17)

buf.load_all()
gain.set(0)

audio.add(comm)
audio.add(midi)
audio.add(gain)
audio.add(buf)
audio.add(tape)

midi.connect(buf)
gain.connect(buf)
buf.connect(audio)
buf.connect(tape)

dlal.typical_setup()
