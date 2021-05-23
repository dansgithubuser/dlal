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
        self.new = True

    def add(self, spectrum, tone, noise, phonetic, stop, remaining):
        if stop:
            if self.new and remaining < 0.2:
                return
            s = sum(spectrum[:len(spectrum) // 2])
            if self.new:
                if s < 0.2:
                    return
            else:
                if s < 0.01:
                    self.new = True
                    return
            if sum(spectrum[:len(spectrum) // 2]) < 0.1:
                self.new = True
                return
        if self.new:
            self.samples.setdefault(phonetic, []).append([])
            self.new = False
        self.samples[phonetic][-1].append({
            'spectrum_tone': spectrum[0:80],
            'spectrum_noise': [spectrum[i * len(spectrum) // 64] for i in range(64)],
            'amp_tone': tone,
            'amp_noise': noise,
        })

    def save(self):
        with open('assets/phonetics/markov.json', 'w') as f:
            f.write(json.dumps(self.samples, indent=2))

# consts
SAMPLE_RATE = 44100
RUN_SIZE = 64
PHONETICS = [
    'ae', 'ay', 'a', 'e', 'y', 'i', 'o', 'w', 'uu', 'u',
    'sh', 'sh_v', 'h', 'f', 'v', 'th', 'th_v', 's', 'z', 'm', 'n', 'ng', 'r', 'l',
    'p', 'b', 't', 'd', 'k', 'g', 'ch', 'j',
]
STOPS = [
    'p', 'b', 't', 'd', 'k', 'g', 'ch', 'j',
]

# helpers
class Runner:
    def __init__(self):
        self.sample = 0
        self.seconds = 0

    def run(self, seconds, callback=None):
        self.seconds += seconds
        elapsed = 0
        while elapsed < self.seconds:
            audio.run()
            self.sample += RUN_SIZE
            elapsed = self.sample / SAMPLE_RATE
            if callback: callback(self.seconds - elapsed)

# run
model = Model()
runner = Runner()
for phonetic in PHONETICS:
    print(phonetic)
    runner.run(3)
    model.new = True
    runner.run(6, lambda remaining: model.add(
        stft.spectrum(),
        peak_lo.value() * 20,
        peak_hi.value() * 2e4,
        phonetic,
        phonetic in STOPS,
        remaining,
    ))
    runner.run(1)
model.save()
