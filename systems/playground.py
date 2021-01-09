import dlal

import midi as mid

import math
import threading
import time

audio = dlal.Audio()
dlal.driver_set(audio)
comm = dlal.Comm()
midi = dlal.Midi()
train = dlal.Train()
iir = dlal.Iir()
buf = dlal.Buf()
tape = dlal.Tape(1 << 17)

dlal.connect(
    midi,
    train,
    [buf, '<+', iir],
    [audio, tape],
)

iir.single_pole_bandpass(0, 0.1)
def sweep():
    low_freq = 440
    sweep_speed = 0.02
    sweep.w = low_freq
    sweep.m = 1 + sweep_speed
    while True:
        sweep.w *= sweep.m
        if sweep.w > audio.sample_rate() / 2:
            sweep.m = 1 - sweep_speed
        elif sweep.w < low_freq:
            sweep.m = 1 + sweep_speed
        iir.single_pole_bandpass(
            sweep.w / audio.sample_rate() * 2 * math.pi,
            math.sin(20*time.time())*0.1 + 0.11,
            smooth=0.9,
        )
        time.sleep(0.01)
sweep_thread = threading.Thread(target=sweep)
sweep_thread.start()

train.midi([0x90, 0x3c, 0x40])

dlal.typical_setup()
