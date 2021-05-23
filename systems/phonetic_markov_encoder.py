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
def stats(l):
    mean = sum(l) / len(l)
    dev = math.sqrt(sum((i - mean) ** 2 for i in l))
    return {
        'mean': mean,
        'dev': dev,
    }

def stats_seq(seq):
    return {
        'spectrum_tone' : [stats([i['spectrum_tone' ][j] for i in seq]) for j in range(BINS_TONE)],
        'spectrum_noise': [stats([i['spectrum_noise'][j] for i in seq]) for j in range(BINS_NOISE)],
        'amp_tone'      :  stats([i['amp_tone'      ]    for i in seq]),
        'amp_noise'     :  stats([i['amp_noise'     ]    for i in seq]),
    }

def split_spectrum(spectrum):
    return (
        spectrum[:BINS_TONE],
        [spectrum[i * len(spectrum) // BINS_NOISE] for i in range(BINS_NOISE)],
    )

def distance_params(params, spectrum_tone, spectrum_noise, amp_tone, amp_noise, plot=False):
    a = (
        params['spectrum_tone'],
        params['spectrum_noise'],
        params['amp_tone'],
        params['amp_noise'],
    )
    ssta = sum(i['mean'] for i in a[0])
    ssna = sum(i['mean'] for i in a[1])
    saa = a[2]['mean'] + a[3]['mean']
    sstb = sum(spectrum_tone)
    ssnb = sum(spectrum_noise)
    sab = amp_tone + amp_noise
    b = (
        [i / sstb * ssta for i in spectrum_tone],
        [i / ssnb * ssna for i in spectrum_noise],
        amp_tone / sab * saa,
        amp_noise / sab * saa,
    )
    components = [
        *[abs(i['mean'] - j) / i['dev'] for i, j in zip(a[0], b[0])],
        *[abs(i['mean'] - j) / i['dev'] for i, j in zip(a[1], b[1])],
        abs(a[2]['mean'] - b[2]) / a[2]['dev'],
        abs(a[3]['mean'] - b[3]) / a[3]['dev'],
    ]
    if plot:
        model.plot(params=[
            params_means(params),
            {
                'spectrum_tone': b[0],
                'spectrum_noise': b[1],
                'amp_tone': b[2],
                'amp_noise': b[3],
            },
        ])
    return math.sqrt(sum(i ** 2 for i in components))

def params_means(params):
    return {
        'spectrum_tone' : [i['mean'] for i in params['spectrum_tone' ]],
        'spectrum_noise': [i['mean'] for i in params['spectrum_noise']],
        'amp_tone'      : params['amp_tone' ]['mean'],
        'amp_noise'     : params['amp_noise']['mean'],
    }

class Model:
    path = 'assets/phonetics/markov.json'

    def __init__(self):
        self.seqs = {}
        self.new = True
        if args.unlabeled:
            with open(Model.path) as f:
                self.phonetics = json.loads(f.read())
        self.updates = []

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
        if self.new:
            self.seqs.setdefault(phonetic, []).append([])
            self.new = False
        spectrum_tone, spectrum_noise = split_spectrum(spectrum)
        self.seqs[phonetic][-1].append({
            'spectrum_tone': spectrum_tone,
            'spectrum_noise': spectrum_noise,
            'amp_tone': amp_tone,
            'amp_noise': amp_noise,
        })

    def update(self, remaining):
        spectrum, amp_tone, amp_noise = self.sample_system()
        spectrum_tone, spectrum_noise = split_spectrum(spectrum)
        distances = []
        for phonetic, params in self.phonetics.items():
            if phonetic in STOPS: continue
            d = distance_params(params, spectrum_tone, spectrum_noise, amp_tone, amp_noise)
            distances.append((d, phonetic))
        self.updates.append((
            remaining,
            [i[1] for i in sorted(distances)[:5]],
        ))

    def save(self):
        if not args.unlabeled:
            self.phonetics = {}
            for phonetic, seq in self.seqs.items():
                if phonetic in STOPS: continue
                self.phonetics[phonetic] = stats_seq(seq[0])
        with open(Model.path, 'w') as f:
            f.write(json.dumps(self.phonetics, indent=2))

    def plot(self, phonetics=[], params=[]):
        plot = dpc.Plot()
        dx = len(phonetics) + len(params) + 1

        def plot_params(params, j):
            for i, v in enumerate(params['spectrum_tone']):
                plot.rect(i*dx+j, 0, i*dx+j+1, +v, g=0.0, b=0.0)
            for i, v in enumerate(params['spectrum_noise']):
                plot.rect(i*dx+j, 0, i*dx+j+1, -v)
            plot.rect(-2*dx+j, 0, -2*dx+j+1, +params['amp_tone'], g=0.0, b=0.0)
            plot.rect(-2*dx+j, 0, -2*dx+j+1, -params['amp_noise'])

        for i, phonetic in enumerate(phonetics):
            plot_params(params_means(self.phonetics[phonetic]), i)
        for i, params in enumerate(params):
            plot_params(params, i + len(phonetics))

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

if not args.unlabeled:
    for phonetic in PHONETICS:
        print(phonetic)
        runner.run(3)
        model.new = True
        runner.run(6, lambda remaining: model.add(phonetic, remaining))
        runner.run(1)
else:
    runner.run(callback=lambda remaining: model.update(remaining))

model.save()
