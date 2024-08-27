import dlal

audio = dlal.Audio()
comm = dlal.Comm()
midi = dlal.Midi()
gain = dlal.Gain()
sonic = dlal.Sonic()
buf = dlal.Buf()
tape = dlal.Tape(1 << 17)

gain.set(0)
sonic.from_json({
    "0": {
        "a": 1e-4, "d": 0, "s": 1, "r": 1e-4, "m": 1,
        "i0": 0, "i1": 0.05, "i2": 0.03, "i3": 0.01, "o": 0.125,
    },
    "1": {
        "a": 1, "d": 0, "s": 1, "r": 1e-5, "m": 2,
        "i0": 0, "i1": 0, "i2": 0, "i3": 0, "o": 0,
    },
    "2": {
        "a": 1, "d": 0, "s": 1, "r": 1e-5, "m": 3,
        "i0": 0, "i1": 0, "i2": 0, "i3": 0, "o": 0,
    },
    "3": {
        "a": 1, "d": 0, "s": 1, "r": 1e-5, "m": 5,
        "i0": 0, "i1": 0, "i2": 0, "i3": 0, "o": 0,
    },
})

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

dlal.driver_set(audio)
dlal.typical_setup()
