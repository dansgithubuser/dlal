import dlal

import time

audio = dlal.Audio(driver=True)
comm = dlal.Comm()
noisebank = dlal.Noisebank()
buf = dlal.Buf()
tape = dlal.Tape(1 << 17)

dlal.connect(
    noisebank,
    buf,
    [audio, tape],
)

noisebank.midi([0x90, 42, 127])

tape.to_file_i16le_start('noisebank.i16le', 1 << 10)

a = 0.25

# sweep
for i in range(64):
    s = [0] * 64
    s[i] = a
    noisebank.spectrum(s)
    for _ in range(256):
        audio.run()

# silence
noisebank.spectrum([0] * 64)
for _ in range(256):
    audio.run()

# sweep in pairs
for i in range(63):
    s = [0] * 64
    s[i] = a
    s[i+1] = a
    noisebank.spectrum(s)
    for _ in range(256):
        audio.run()

# silence
noisebank.spectrum([0] * 64)
for _ in range(256):
    audio.run()

# sweep in split pairs
for i in range(62):
    s = [0] * 64
    s[i] = a
    s[i+2] = a
    noisebank.spectrum(s)
    for _ in range(256):
        audio.run()

# silence
noisebank.spectrum([0] * 64)
for _ in range(256):
    audio.run()

# triangle
for i in range(65):
    noisebank.spectrum([a] * i + [0] * (64 - i))
    for _ in range(256):
        audio.run()

# silence
noisebank.spectrum([0] * 64)
for _ in range(256):
    audio.run()

tape.to_file_i16le_stop()
