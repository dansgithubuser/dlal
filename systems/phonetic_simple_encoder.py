import dlal

import argparse
import json
import math

try:
    import dansplotcore as dpc
except:
    pass

parser = argparse.ArgumentParser()
parser.add_argument('recording_path', nargs='?', default='assets/phonetics/phonetics.flac')
parser.add_argument('--plot-stft-params', '--psp', action='store_true')
args = parser.parse_args()

# consts
SAMPLE_RATE = 44100
RUN_SIZE = 64
STFT_BINS = 512
C = 1 / SAMPLE_RATE * STFT_BINS

PHONETICS = [
    'ae', 'ay', 'a', 'e', 'y', 'i', 'o', 'w', 'uu', 'u',
    'sh', 'sh_v', 'h', 'f', 'v', 'th', 'th_v', 's', 'z', 'm', 'n', 'ng', 'r', 'l',
    'p', 'b', 't', 'd', 'k', 'g', 'ch', 'j',
]
STOPS = [
    'p', 'b', 't', 'd', 'k', 'g', 'ch', 'j',
]

GAIN_LO = 20
GAIN_HI = 2e4

F0_BIN_RANGE = [math.floor(i * C) for i in [0, 200]]
F1_BIN_RANGE = [math.floor(i * C) for i in [200, 1000]]
F2_BIN_RANGE = [math.floor(i * C) for i in [1000, 2000]]
F3_BIN_RANGE = [math.floor(i * C) for i in [2000, 3000]]

NOISE_L_BIN_RANGE = [math.floor(i * C) for i in [2000, 4000]]
NOISE_M_BIN_RANGE = [math.floor(i * C) for i in [4000, 8000]]
NOISE_H_BIN_RANGE = [math.floor(i * C) for i in [8000, 16000]]

# components
audio = dlal.Audio(driver=True)
filea = dlal.Filea(args.recording_path)
buf = dlal.Buf()

lpf1 = dlal.Lpf(0.99)
lpf2 = dlal.Lpf(0.99)
peak_lo = dlal.Peak(name='peak_lo')
hpf1 = dlal.Hpf()
hpf2 = dlal.Hpf()
peak_hi = dlal.Peak(name='peak_hi')
stft = dlal.Stft(STFT_BINS)

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
def mean(l):
    return sum(l) / len(l)

def stats(l, k):
    m = mean([i[k] for i in l])
    return (
        m,
        math.sqrt(mean([(i[k] - m) ** 2 for i in l])),
    )

def find_formant(spectrum, bin_i, bin_f):
    spectrum = spectrum[bin_i:bin_f]
    amp = max(spectrum)
    return {
        'amp': amp,
        'freq': (spectrum.index(amp) + bin_i) / C,
    }

def find_noise(spectrum, bin_i, bin_f):
    return mean(spectrum[bin_i:bin_f])

class Model:
    path = 'assets/phonetics/simple.json'
    phonetic_0 = {
        'f0_amp': (0, 0),
        'f0_freq': (0, 0),
        'f1_amp': (0, 0),
        'f1_freq': (600, 0),
        'f2_amp': (0, 0),
        'f2_freq': (1000, 0),
        'f3_amp': (0, 0),
        'f3_freq': (2500, 0),
        'noise_l': (0, 0),
        'noise_m': (0, 0),
        'noise_h': (0, 0),
        'amp_tone': (0, 0),
        'amp_noise': (0, 0),
    }

    def __init__(self):
        self.new = True
        self.samples = []
        self.params = {}

    def sample_system(self):
        return (
            stft.spectrum(),
            peak_lo.value() * GAIN_LO,
            peak_hi.value() * GAIN_HI,
        )

    def add_pre(self):
        self.new = True

    def add(self, phonetic, remaining, plot=False):
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
        f0 = find_formant(spectrum, *F0_BIN_RANGE)
        f1 = find_formant(spectrum, *F1_BIN_RANGE)
        f2 = find_formant(spectrum, *F2_BIN_RANGE)
        f3 = find_formant(spectrum, *F3_BIN_RANGE)
        self.samples.append({
            'f0_amp': f0['amp'],
            'f0_freq': f0['freq'],
            'f1_amp': f1['amp'],
            'f1_freq': f1['freq'],
            'f2_amp': f2['amp'],
            'f2_freq': f2['freq'],
            'f3_amp': f3['amp'],
            'f3_freq': f3['freq'],
            'noise_l': find_noise(spectrum, *NOISE_L_BIN_RANGE),
            'noise_m': find_noise(spectrum, *NOISE_M_BIN_RANGE),
            'noise_h': find_noise(spectrum, *NOISE_H_BIN_RANGE),
            'amp_tone': amp_tone,
            'amp_noise': amp_noise,
        })
        self.new = False
        if plot:
            s = self.samples[-1]
            plot = dpc.Plot()
            for i, v in enumerate(spectrum[:STFT_BINS // 2 + 1]):
                plot.rect(i, 0, i+1, v)
            # formants
            plot.rect(s['f0_freq'] * C - 2, 0, s['f0_freq'] * C + 2, s['f0_amp'], g=0, b=0, a=0.5)
            plot.rect(s['f1_freq'] * C - 2, 0, s['f1_freq'] * C + 2, s['f1_amp'], g=0, b=0, a=0.5)
            plot.rect(s['f2_freq'] * C - 2, 0, s['f2_freq'] * C + 2, s['f2_amp'], g=0, b=0, a=0.5)
            plot.rect(s['f3_freq'] * C - 2, 0, s['f3_freq'] * C + 2, s['f3_amp'], g=0, b=0, a=0.5)
            # noise
            plot.rect(NOISE_L_BIN_RANGE[0], 0, NOISE_L_BIN_RANGE[1], s['noise_l'], r=0, g=0, a=0.5)
            plot.rect(NOISE_M_BIN_RANGE[0], 0, NOISE_M_BIN_RANGE[1], s['noise_m'], r=0, g=0, a=0.5)
            plot.rect(NOISE_H_BIN_RANGE[0], 0, NOISE_H_BIN_RANGE[1], s['noise_h'], r=0, g=0, a=0.5)
            # amps
            plot.rect(-2, 0, -3/2, amp_tone, g=0, b=0)
            plot.rect(-3/2, 0, -1, amp_noise, r=0, g=0)
            # show
            plot.show()

    def add_post(self, phonetic):
        self.params[phonetic] = {k: stats(self.samples, k) for k in Model.phonetic_0.keys()}
        self.samples.clear()

    def add_0(self):
        self.params['0'] = Model.phonetic_0

    def save(self):
        with open(Model.path, 'w') as f:
            f.write(json.dumps(
                self.params,
                indent=2,
            ))

# runner
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
for phonetic in PHONETICS:
    print(phonetic)
    runner.run(3)
    model.add_pre()
    runner.run(6, lambda remaining: model.add(phonetic, remaining, args.plot_stft_params))
    model.add_post(phonetic)
    runner.run(1)
model.add_0()
model.save()
