import dlal

import json

# components
audio = dlal.Audio(driver=True)
comm = dlal.Comm()

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
    (gain_tone, gain_noise),
    (buf_tone, buf_noise),
    [],
    (sinbank, noisebank),
    (buf_tone, buf_noise),
    buf,
    [audio, tape],
)

# phonetics
with open('assets/phonetics/markov.json') as f:
    model = json.loads(f.read())

def say(index):
    phonetic = model[index]
    with dlal.Detach():
        sinbank.spectrum(phonetic['spectrum_tone'])
        noisebank.spectrum(phonetic['spectrum_noise'])
        gain_tone.set(phonetic['amp_tone'])
        gain_noise.set(phonetic['amp_noise'])

# command
sinbank.midi([0x90, 41, 0x40])
gain_tone.set(0)
gain_noise.set(0)

dlal.typical_setup()

for i in range(0, len(model), 2757):
    i = (i // 1000 + 1) * 1000
    print(i, model[i]['phonetic'])
