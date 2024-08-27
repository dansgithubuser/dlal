'A vocoder built around vocoder component.'

import dlal

# add
audio = dlal.Audio(driver=True, mic=True)
gain_mod = dlal.Gain(1)
comm = dlal.Comm()
carrier = dlal.Sonic('big_bass_1', name='carrier')
vocoder = dlal.Vocoder()
buf = dlal.Buf()

# connect
gain_mod.connect(vocoder)
dlal.connect(
    carrier,
    [buf, '<+', vocoder, audio],
    audio,
)

# run
dlal.typical_setup()
