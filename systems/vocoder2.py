'A vocoder built around stft, sinbank, and noisebank.'

import dlal

import time

audio = dlal.Audio(driver=True)
comm = dlal.Comm()
audio.add(audio)

hpf = dlal.Hpf()
peak = dlal.Peak()
oracle = dlal.Oracle(m=100, format=('set', '%'))

stft = dlal.Stft(512)
noisebank = dlal.Noisebank()
gain_noise = dlal.Gain()
sinbank = dlal.Sinbank(44100 / 512)
buf = dlal.Buf()
tape = dlal.Tape(1 << 17)

dlal.connect(
    audio,
    [peak, '<+', hpf],
    oracle,
    gain_noise,
    [],
    audio,
    stft,
    [sinbank, noisebank],
    [buf, '<+', gain_noise],
    [audio, tape],
)

sinbank.midi([0x90, 41, 0x40])

dlal.typical_setup()

def rec(duration=5, pause=3):
    print('recording in')
    for i in range(pause, 0, -1):
        print(i)
        time.sleep(1)
    print('recording')
    tape.to_file_i16le_start()
    for i in range(duration):
        print(f'{i} / {duration}')
        time.sleep(1)
    tape.to_file_i16le_stop()
    print('done')
