'A vocoder built around vocoder component.'

import dlal

# add
audio = dlal.Audio(driver=True, mic=True)
comm = dlal.Comm()

carrier = dlal.Sonic('big_bass_1')
modulator = dlal.Buf()
vocoder = dlal.Vocoder()
voc_gain = dlal.Gain()
voc_buf = dlal.Buf()

pass_gain = dlal.Gain(0.2)
pass_buf = dlal.Buf()

reverb = dlal.Reverb()
buf = dlal.Buf()

# connect
dlal.connect(
    carrier,
    [voc_buf, '<+', vocoder, modulator, audio],
    [buf, '<+', voc_gain],
)
dlal.connect(
    carrier,
    [pass_buf, '<+', pass_gain],
    buf,
)
dlal.connect(
    reverb,
    buf,
    audio,
)

# run
dlal.typical_setup()
