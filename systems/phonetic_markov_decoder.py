import dlal

import json
import time

# components
audio = dlal.Audio(driver=True)
comm = dlal.Comm()

sinbank = dlal.Sinbank(44100 / 512)
noisebank = dlal.Noisebank()
gain_tone = dlal.Gain(name='gain_tone')
gain_noise = dlal.Gain(name='gain_noise')
mul = dlal.Mul(1)
buf_tone = dlal.Buf(name='buf_tone')
buf_noise = dlal.Buf(name='buf_noise')

buf = dlal.Buf()
tape = dlal.Tape(1 << 17)

# connect
dlal.connect(
    (gain_tone, gain_noise),
    (buf_tone, buf_noise),
    [],
    mul,
    [buf_tone, buf_noise],
    [],
    (sinbank, noisebank),
    (buf_tone, buf_noise),
    buf,
    [audio, tape],
)

# phonetics
with open('assets/phonetics/markov.json') as f:
    model = json.loads(f.read())

def say(phonetic):
    phonetic = model[phonetic]
    with dlal.Detach():
        sinbank.spectrum([i['mean'] for i in phonetic['spectrum_tone']])
        noisebank.spectrum([i['mean'] for i in phonetic['spectrum_noise']])
        gain_tone.set(phonetic['amp_tone']['mean'])
        gain_noise.set(phonetic['amp_noise']['mean'])

def say_all():
    for phonetic in model.keys():
        print(phonetic)
        say(phonetic)
        time.sleep(1)

# command
sinbank.midi([0x90, 41, 0x40])
gain_tone.set(0)
gain_noise.set(0)

dlal.typical_setup()
