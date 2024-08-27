import dlal

# add
audio = dlal.Audio(driver=True, mic=True)
comm = dlal.Comm()
buf_mic = dlal.Buf(name='buf_mic')
gain_mic = dlal.Gain(0, name='gain_mic')
train = dlal.Train()
osc = dlal.Osc('noise')
iir = dlal.Iir()
buf = dlal.Buf()

# connect
dlal.connect(
    audio,
    [buf_mic, '<+', gain_mic],
    [],
    [buf_mic, train, osc],
    [buf, '<+', iir],
    audio,
)

# command
osc.midi([0x90, 60, 0x40])

# run
dlal.typical_setup()
