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
args = parser.parse_args()

# consts
SAMPLE_RATE = 44100
RUN_SIZE = 64
BINS_STFT = 512
BINS_NOISE = 64
C = 1 / SAMPLE_RATE * BINS_STFT

GAIN_LO = 200
GAIN_HI = 1e5

FORMANT_BIN_RANGES = [
    [math.floor(i * C) for i in [0, 200]],
    [math.floor(i * C) for i in [200, 1000]],
    [math.floor(i * C) for i in [1000, 2300]],
    [math.floor(i * C) for i in [2300, 3000]],
]

PHONETICS = [
    'ae', 'ay', 'a', 'e', 'y', 'i', 'o', 'w', 'uu', 'u',
    'sh', 'sh_v', 'h', 'f', 'v', 'th', 'th_v', 's', 'z', 'm', 'n', 'ng', 'r', 'l',
    'p', 'b', 't', 'd', 'k', 'g', 'ch', 'j',
]
VOICED = [
    'ae', 'ay', 'a', 'e', 'y', 'i', 'o', 'w', 'uu', 'u',
    'sh_v', 'v', 'th_v', 'z', 'm', 'n', 'ng', 'r', 'l',
    'b', 'd', 'g', 'j',
]
STOPS = [
    'p', 'b', 't', 'd', 'k', 'g', 'ch', 'j',
]

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
stft = dlal.Stft(BINS_STFT)

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

def stats(l):
    m = mean(l)
    return (
        m,
        math.sqrt(mean([(i - m) ** 2 for i in l])),
    )

def find_formant(spectrum, bin_i, bin_f, pregain):
    spectrum = spectrum[bin_i:bin_f]
    amp = max(spectrum)
    return {
        'freq': (spectrum.index(amp) + bin_i) / C,
        'amp': amp * pregain,
    }

class Model:
    path = 'assets/phonetics/model.json'

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

    def add(self, phonetic, remaining):
        spectrum, amp_tone, amp_noise = self.sample_system()
        if phonetic not in VOICED:
            amp_tone = 0
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
        if self.new:
            self.samples.append([])
        self.samples[-1].append({
            'formants': [
                find_formant(spectrum, *i, amp_tone)
                for i in FORMANT_BIN_RANGES
            ],
            'noise_spectrum': [
                spectrum[i * len(spectrum) // BINS_NOISE] * amp_noise
                for i in range(BINS_NOISE)
            ],
        })
        self.new = False

    def add_post(self, phonetic):
        if phonetic not in STOPS:
            self.params[phonetic] = {
                'type': 'continuant',
                'voiced': phonetic in VOICED,
                'frames': [
                    {
                        'formants': [
                            {
                                'freq': stats([
                                    j['formants'][i]['freq']
                                    for j in self.samples[-1]
                                ]),
                                'amp': stats([
                                    j['formants'][i]['amp']
                                    for j in self.samples[-1]
                                ]),
                            }
                            for i in range(len(FORMANT_BIN_RANGES))
                        ],
                        'noise_spectrum': [
                            stats([
                                j['noise_spectrum'][i]
                                for j in self.samples[-1]
                            ])
                            for i in range(BINS_NOISE)
                        ],
                    },
                ],
            }
        else:
            self.params[phonetic] = {
                'type': 'stop',
                'voiced': phonetic in VOICED,
                'frames': [
                    {
                        'formants': [
                            {
                                'freq': (k['formants'][i]['freq'], 0),
                                'amp': (k['formants'][i]['amp'], 0),
                            }
                            for i in range(len(FORMANT_BIN_RANGES))
                        ],
                        'noise_spectrum': [
                            (k['noise_spectrum'][i], 0)
                            for i in range(BINS_NOISE)
                        ],
                        'duration': RUN_SIZE,
                    }
                    for k in self.samples[0]  # just take the first recital of the stop
                ],
            }
        self.samples.clear()

    def add_0(self):
        self.params['0'] = {
            'type': 'continuant',
            'voiced': False,
            'frames': [
                {
                    'formants': [
                        {
                            'freq': ((i[0] + i[1]) / 2, 0),
                            'amp': (0, 0),
                        }
                        for i in FORMANT_BIN_RANGES
                    ],
                    'noise_spectrum': [(0, 0)] * BINS_NOISE,
                },
            ],
        }

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
    runner.run(6, lambda remaining: model.add(phonetic, remaining))
    model.add_post(phonetic)
    runner.run(1)
model.add_0()
model.save()
