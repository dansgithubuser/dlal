'''
`phonetic` - symbol representing a sound
`params` - set of low-level instructions for how to synthesize a sound
`frame` - params with mean and deviation
`info` - frames and prior information for a `phonetic`
'''

import dlal

import argparse
import json
import math
import os

try:
    import dansplotcore as dpc
except:
    pass

parser = argparse.ArgumentParser()
parser.add_argument('recording_path', nargs='?', default='assets/phonetics/phonetics.flac')
if __name__ == '__main__':
    args = parser.parse_args()
else:
    class EnvArgs:
        def __init__(self):
            self.recording_path = os.environ.get(
                'PHONETIC_ENCODER_RECORDING_PATH',
                'assets/phonetics/phonetics.flac',
            )
    args = EnvArgs()

# consts
SAMPLE_RATE = 44100
RUN_SIZE = 64
BINS_STFT = 512
BINS_NOISE = 64
C = 1 / SAMPLE_RATE * BINS_STFT

GAIN_LO = 200
GAIN_HI = 1e4

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
FRICATIVES = [
    'sh', 'sh_v', 'h', 'f', 'v', 'th', 'th_v', 's', 'z',
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

# functions
def mean(l):
    return sum(l) / len(l)

def descend(x, ks):
    for k in ks: x = x[k]
    return x

def stats(l, ks):
    l = [descend(i, ks) for i in l]
    m = mean(l)
    return (
        m,
        math.sqrt(mean([(i - m) ** 2 for i in l])),
    )

def frames_from_params(params, stop=False):
    if not stop:
        return [
            {
                'formants': [
                    {
                        'freq': stats(params, ['formants', i, 'freq']),
                        'amp': stats(params, ['formants', i, 'amp']),
                    }
                    for i in range(len(FORMANT_BIN_RANGES))
                ],
                'noise': [
                    stats(params, ['noise', i])
                    for i in range(BINS_NOISE)
                ]
            },
        ]
    else:
        return [
            {
                'formants': [
                    {
                        'freq': stats([k], ['formants', i, 'freq']),
                        'amp': stats([k], ['formants', i, 'amp']),
                    }
                    for i in range(len(FORMANT_BIN_RANGES))
                ],
                'noise': [
                    stats([k], ['noise', i])
                    for i in range(BINS_NOISE)
                ],
                'duration': RUN_SIZE,
            }
            for k in params
        ]

def find_formant(spectrum, bin_i, bin_f, pregain):
    spectrum = spectrum[bin_i:bin_f]
    amp = max(spectrum)
    return {
        'freq': (spectrum.index(amp) + bin_i) / C,
        'amp': amp * pregain,
    }

def find_noise(spectrum, amp_noise):
    return [
        spectrum[i * len(spectrum) // BINS_NOISE] * amp_noise
        for i in range(BINS_NOISE)
    ]

def sample_system():
    return (
        stft.spectrum(),
        peak_lo.value() * GAIN_LO,
        peak_hi.value() * GAIN_HI,
    )

def parameterize(spectrum, amp_tone, amp_noise, phonetic=None):
    if phonetic and phonetic not in VOICED:
        amp_tone = 0
    formants = [
        find_formant(spectrum, *i, amp_tone)
        for i in FORMANT_BIN_RANGES
    ]
    if not phonetic or phonetic in FRICATIVES:
        noise = find_noise(spectrum, amp_noise)
    else:
        noise = [0] * BINS_NOISE
    return {
        'formants': formants,
        'noise': noise,
    }

# model
class Model:
    path = 'assets/phonetics/model.json'

    def __init__(self):
        self.new = True
        self.params = []
        self.info = {}

    def add_pre(self):
        self.new = True

    def add(self, phonetic, remaining):
        spectrum, amp_tone, amp_noise = sample_system()
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
            self.params.append([])
        params = parameterize(spectrum, amp_tone, amp_noise, phonetic)
        self.params[-1].append(params)
        self.new = False

    def add_post(self, phonetic):
        stop = phonetic in STOPS
        self.info[phonetic] = {
            'type': 'stop' if stop else 'continuant',
            'voiced': phonetic in VOICED,
            'frames': frames_from_params(self.params[0], stop)  # for stops, just take the first recital
        }
        self.params.clear()

    def add_0(self):
        self.info['0'] = {
            'type': 'continuant',
            'voiced': False,
            'frames': frames_from_params([
                {
                    'formants': [
                        {
                            'freq': (i[0] + i[1]) / 2,
                            'amp': 0,
                        }
                        for i in FORMANT_BIN_RANGES
                    ],
                    'noise': [0] * BINS_NOISE,
                },
            ]),
        }

    def save(self):
        with open(Model.path, 'w') as f:
            f.write(json.dumps(
                self.info,
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
if __name__ == '__main__':
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
