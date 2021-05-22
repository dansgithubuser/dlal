'A vocoder built around stft, sinbank, and noisebank.'

import dlal

import time

# components
audio = dlal.Audio(driver=True)
comm = dlal.Comm()
audio.add(audio)

lpf1 = dlal.Lpf(0.99)
lpf2 = dlal.Lpf(0.99)
peak_lo = dlal.Peak(name='peak_lo')
oracle_lo = dlal.Oracle(m=20, format=('set', '%'), name='oracle_lo')
hpf1 = dlal.Hpf()
hpf2 = dlal.Hpf()
peak_hi = dlal.Peak(name='peak_hi')
oracle_hi = dlal.Oracle(m=2e4, format=('set', '%'), name='oracle_hi')

stft = dlal.Stft(512)
noisebank = dlal.Noisebank()
gain_noise = dlal.Gain(name='gain_noise')
buf_noise = dlal.Buf(name='buf_noise')
sinbank = dlal.Sinbank(44100 / 512)
gain_tone = dlal.Gain(name='gain_tone')
buf_tone = dlal.Buf(name='buf_tone')

buf = dlal.Buf()
tape = dlal.Tape(1 << 17)

# connect
dlal.connect(
    audio,
    [peak_lo, peak_hi],
    [],
    (lpf1, hpf1),
    (peak_lo, peak_hi),
    (oracle_lo, oracle_hi),
    (gain_tone, gain_noise),
    (buf_tone, buf_noise),
    [],
    (lpf2, hpf2),
    (peak_lo, peak_hi),
    [],
    audio,
    stft,
    (sinbank, noisebank),
    (buf_tone, buf_noise),
    buf,
    [audio, tape],
)

# command
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
