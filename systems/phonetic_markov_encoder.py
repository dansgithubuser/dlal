import dlal

import json
import math

# components
audio = dlal.Audio(driver=True)
filea = dlal.Filea('assets/phonetics/phonetics.flac')
buf = dlal.Buf()

lpf1 = dlal.Lpf(0.99)
lpf2 = dlal.Lpf(0.99)
peak_lo = dlal.Peak(name='peak_lo')
hpf1 = dlal.Hpf()
hpf2 = dlal.Hpf()
peak_hi = dlal.Peak(name='peak_hi')
stft = dlal.Stft(512)

# connect
dlal.connect(
    filea,
    buf,
    [peak_lo, peak_hi, stft],
    [],
    [lpf1, lpf2],
    peak_lo,
    [],
    [hpf1, hpf2],
    peak_hi,
)

# model
def stats(l):
    mean = sum(l) / len(l)
    dev = math.sqrt(sum((i - mean) ** 2 for i in l))
    return {
        'mean': mean,
        'dev': dev,
    }

class Model:
    def __init__(self):
        self.samples = {}

    def add(self, spectrum, tone, noise, phonetic):
        self.samples.setdefault(phonetic, []).append({
            'spectrum_tone': spectrum[0:80],
            'spectrum_noise': [spectrum[i * len(spectrum) // 64] for i in range(64)],
            'amp_tone': tone,
            'amp_noise': noise,
        })

    def save(self):
        phonetics = {
            k: {
                'spectrum_tone' : [stats([i['spectrum_tone' ][j] for i in v]) for j in range(80)],
                'spectrum_noise': [stats([i['spectrum_noise'][j] for i in v]) for j in range(64)],
                'amp_tone'      :  stats([i['amp_tone'      ]    for i in v]),
                'amp_noise'     :  stats([i['amp_noise'     ]    for i in v]),
            }
            for k, v in self.samples.items()
        }
        with open('assets/phonetics/markov.json', 'w') as f:
            f.write(json.dumps(phonetics, indent=2))

# consts
SAMPLE_RATE = 44100
RUN_SIZE = 64
PHONETICS = [
    'ae', 'ay', 'a', 'e', 'y', 'i', 'o', 'w', 'uu', 'u',
    'sh', 'sh_v', 'h', 'f', 'v', 'th', 'th_v', 's', 'z', 'm', 'n', 'ng', 'r', 'l',
    'p', 'b', 't', 'd', 'k', 'g', 'ch', 'j',
]

# helpers
class Runner:
    def __init__(self):
        self.sample = 0
        self.seconds = 0

    def run(self, seconds, callback=None):
        self.seconds += seconds
        while self.sample / SAMPLE_RATE < self.seconds:
            audio.run()
            self.sample += RUN_SIZE
            if callback: callback()

# run
model = Model()
runner = Runner()
for phonetic in PHONETICS:
    print(phonetic)
    runner.run(4)
    runner.run(4, lambda: model.add(
        stft.spectrum(),
        peak_lo.value() * 20,
        peak_hi.value() * 2e4,
        phonetic,
    ))
    runner.run(2)
model.save()
