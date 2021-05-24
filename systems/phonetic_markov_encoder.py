import dlal

import argparse
import json
import math

try:
    import dansplotcore as dpc
except:
    pass

parser = argparse.ArgumentParser()
parser.add_argument('flac_path', nargs='?', default='assets/phonetics/phonetics.flac')
parser.add_argument('--unlabeled', '-u', action='store_true')
parser.add_argument('--inspect', '-i', action='store_true')
args = parser.parse_args()

# components
audio = dlal.Audio(driver=True)
filea = dlal.Filea(args.flac_path)
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
BINS_TONE = 80
BINS_NOISE = 64
GAIN_LO = 20
GAIN_HI = 2e4

# model
def mean(l): return sum(l) / len(l)

def split_spectrum(spectrum):
    return (
        spectrum[:BINS_TONE],
        [spectrum[i * len(spectrum) // BINS_NOISE] for i in range(BINS_NOISE)],
    )

def distance_params(a, b, plot=False):
    ssta = sum(a['spectrum_tone'])
    ssna = sum(a['spectrum_noise'])
    saa = a['amp_tone'] + a['amp_noise']
    sstb = sum(b['spectrum_tone'])
    ssnb = sum(b['spectrum_noise'])
    sab = b['amp_tone'] + b['amp_noise']
    b_norm = {
        'spectrum_tone': [i / sstb * ssta for i in b['spectrum_tone']],
        'spectrum_noise': [i / ssnb * ssna for i in b['spectrum_noise']],
        'amp_tone': b['amp_tone'] / sab * saa,
        'amp_noise': b['amp_noise'] / sab * saa,
    }
    components = [
        *[abs(i - j) for i, j in zip(a['spectrum_tone'], b_norm['spectrum_tone'])],
        *[abs(i - j) for i, j in zip(a['spectrum_noise'], b_norm['spectrum_noise'])],
        abs(a['amp_tone'] - b_norm['amp_tone']),
        abs(a['amp_noise'] - b_norm['amp_noise']),
    ]
    if plot: model.plot(params=[a, b])
    return math.sqrt(sum(i ** 2 for i in components))

class Model:
    path = 'assets/phonetics/markov.json'

    def __init__(self):
        self.new = True
        self.samples = []
        self.label = None
        self.params = []
        self.labels = {}

    def sample_system(self):
        return (
            stft.spectrum(),
            peak_lo.value() * GAIN_LO,
            peak_hi.value() * GAIN_HI,
        )

    def add(self, phonetic, remaining):
        spectrum, amp_tone, amp_noise = self.sample_system()
        if phonetic in STOPS:
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
        if self.new and self.samples:
            self.params.append({
                'spectrum_tone' : [mean([i['spectrum_tone' ][j] for i in self.samples]) for j in range(BINS_TONE)],
                'spectrum_noise': [mean([i['spectrum_noise'][j] for i in self.samples]) for j in range(BINS_NOISE)],
                'amp_tone'      :  mean([i['amp_tone'      ]    for i in self.samples]),
                'amp_noise'     :  mean([i['amp_noise'     ]    for i in self.samples]),
            })
            self.labels[self.label] = len(self.params) - 1
            self.samples.clear()
        spectrum_tone, spectrum_noise = split_spectrum(spectrum)
        self.samples.append({
            'spectrum_tone': spectrum_tone,
            'spectrum_noise': spectrum_noise,
            'amp_tone': amp_tone,
            'amp_noise': amp_noise,
        })
        self.label = phonetic
        self.new = False

    def add_0(self):
        self.params.append({
            'spectrum_tone': [0 for i in range(BINS_TONE)],
            'spectrum_noise': [0 for i in range(BINS_NOISE)],
            'amp_tone': 0,
            'amp_noise': 0,
        })
        self.labels['0'] = len(self.params) - 1

    def update(self, remaining):
        spectrum, amp_tone, amp_noise = self.sample_system()
        spectrum_tone, spectrum_noise = split_spectrum(spectrum)
        self.params.append({
            'spectrum_tone': spectrum_tone,
            'spectrum_noise': spectrum_noise,
            'amp_tone': amp_tone,
            'amp_noise': amp_noise,
        })
        distances = []
        for label in self.labels.values():
            d = distance_params(self.params[label], self.params[-1])
            distances.append((d, label))
        for _, label in [i for i in sorted(distances)[:5]]:
            self.link(len(self.params) - 1, label)
            self.link(label, len(self.params) - 1)
        self.new = False

    def link(self, label_a, label_b):
        self.params[label_a].setdefault('next', []).append(label_b)

    def save(self):
        with open(Model.path, 'w') as f:
            f.write(json.dumps(
                {
                    'params': self.params,
                    'labels': self.labels,
                },
                indent=2,
            ))

    def load(self):
        with open(Model.path) as f:
            model = json.loads(f.read())
            self.params = model['params']
            self.labels = model['labels']

    def plot(self, params=[]):
        plot = dpc.Plot()
        dx = len(params) + 1
        for i, params in enumerate(params):
            for j, v in enumerate(params['spectrum_tone']):
                plot.rect(j*dx+i, 0, j*dx+i+1, +v, g=0.0, b=0.0)
            for j, v in enumerate(params['spectrum_noise']):
                plot.rect(j*dx+i, 0, j*dx+i+1, -v)
            plot.rect(-2*dx+i, 0, -2*dx+i+1, +params['amp_tone'], g=0.0, b=0.0)
            plot.rect(-2*dx+i, 0, -2*dx+i+1, -params['amp_noise'])
        plot.show()

# helpers
class Runner:
    def __init__(self):
        self.sample = 0
        self.seconds = 0

    def run(self, seconds=None, callback=None):
        if seconds == None: seconds = (filea.duration() - RUN_SIZE) / SAMPLE_RATE
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
if args.inspect:
    model.load()
elif args.unlabeled:
    model.load()
    runner.run(callback=lambda remaining: model.update(remaining))
    model.save()
else:
    for phonetic in PHONETICS:
        print(phonetic)
        runner.run(3)
        model.new = True
        runner.run(6, lambda remaining: model.add(phonetic, remaining))
        runner.run(1)
    model.add_0()
    model.save()
