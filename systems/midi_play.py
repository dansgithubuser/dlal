import dlal

import sys

audio = dlal.Audio()
sonics = [dlal.Sonic() for i in range(8)]
liner = dlal.Liner()

liner.load(sys.argv[1])
audio.add(liner)
for sonic in sonics:
    sonic.i1(0, 1)
    sonic.o(0, 0.1)
    audio.add(sonic)
    liner.connect(sonic)
    sonic.connect(audio)

dlal.typical_setup()
