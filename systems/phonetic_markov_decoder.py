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

def say_one(params):
    with dlal.Detach():
        sinbank.spectrum(params['spectrum_tone'])
        noisebank.spectrum(params['spectrum_noise'])
        gain_tone.set(params['amp_tone'])
        gain_noise.set(params['amp_noise'])

def say_all():
    for phonetic, label in model['labels'].items():
        print(phonetic)
        say_one(model['params'][label])
        time.sleep(1)

def find_path(a, b):
    queue = [[model['labels'][a]]]
    dst = model['labels'][b]
    visited = set([a])
    while queue:
        i = queue.pop(0)
        for j in model['params'][i[-1]]['next']:
            if j in visited: continue
            if j == dst:
                return i + [j]
            visited.add(j)
            queue.append(i + [j])
    raise Exception(f'No path from [{a}] to [{b}].')

def say_with_transient(phonetic):
    if say_with_transient.current != None:
        path = find_path(say_with_transient.current, phonetic)
        for i in path:
            say_one(model['params'][i])
            time.sleep(0.001)
    else:
        label = model['labels'][phonetic]
        say_one(model['params'][label])
    say_with_transient.current = phonetic
say_with_transient.current = '0'

def say(phonetics):
    phonetics += '0'
    i = 0
    while i < len(phonetics):
        if phonetics[i] == '[':
            i += 1
            phonetic = ''
            while phonetics[i] != ']':
                phonetic += phonetics[i]
                i += 1
        else:
            phonetic = phonetics[i]
        i += 1
        say_with_transient(phonetic)
        time.sleep(0.25)

# command
sinbank.midi([0x90, 41, 0x40])
gain_tone.set(0)
gain_noise.set(0)

dlal.typical_setup()
