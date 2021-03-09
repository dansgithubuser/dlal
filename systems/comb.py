import dlal

audio = dlal.Audio(driver=True)
comm = dlal.Comm()
audio.add(audio)
delay = dlal.Delay(size=1024, gain_y=0.8, gain_i=1.0)

dlal.connect(
    delay,
    audio,
    audio,
)

dlal.typical_setup()
