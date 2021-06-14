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
BINS_TONE = 64
BINS_NOISE = 64
C = 1 / SAMPLE_RATE * BINS_STFT

GAIN_LO = 2e3
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
                'tone': {
                    'amp': stats(params, ['tone', 'amp']),
                    'formants': [
                        {
                            'freq': stats(params, ['tone', 'formants', i, 'freq']),
                            'amp': stats(params, ['tone', 'formants', i, 'amp']),
                        }
                        for i in range(len(FORMANT_BIN_RANGES))
                    ],
                    'spectrum': [
                        stats(params, ['tone', 'spectrum', i])
                        for i in range(BINS_TONE)
                    ],
                },
                'noise': {
                    'amp': stats(params, ['noise', 'amp']),
                    'freq_lo': stats(params, ['noise', 'freq_lo']),
                    'freq_peak': stats(params, ['noise', 'freq_peak']),
                    'amp_peak': stats(params, ['noise', 'amp_peak']),
                    'freq_hi': stats(params, ['noise', 'freq_hi']),
                    'spectrum': [
                        stats(params, ['noise', 'spectrum', i])
                        for i in range(BINS_NOISE)
                    ],
                },
            },
        ]
    else:
        return [
            {
                'tone': {
                    'amp': stats([k], ['tone', 'amp']),
                    'formants': [
                        {
                            'freq': stats([k], ['tone', 'formants', i, 'freq']),
                            'amp': stats([k], ['tone', 'formants', i, 'amp']),
                        }
                        for i in range(len(FORMANT_BIN_RANGES))
                    ],
                    'spectrum': [
                        stats([k], ['tone', 'spectrum', i])
                        for i in range(BINS_TONE)
                    ],
                },
                'noise': {
                    'amp': stats([k], ['noise', 'amp']),
                    'freq_lo': stats([k], ['noise', 'freq_lo']),
                    'freq_peak': stats([k], ['noise', 'freq_peak']),
                    'amp_peak': stats([k], ['noise', 'amp_peak']),
                    'freq_hi': stats([k], ['noise', 'freq_hi']),
                    'spectrum': [
                        stats([k], ['noise', 'spectrum', i])
                        for i in range(BINS_NOISE)
                    ],
                },
                'duration': RUN_SIZE,
            }
            for k in params
        ]

def find_formant(spectrum, bin_i, bin_f, amp_tone):
    spread = 2
    window = spectrum[bin_i:bin_f]
    amp_peak = max(window)
    bin_peak = window.index(amp_peak) + bin_i
    bin_formant = bin_peak
    if bin_peak >= spread and bin_peak < len(spectrum) - spread:
        bins = [
            (i, spectrum[i])
            for i in range(bin_peak - spread, bin_peak + spread + 1)
        ]
        s = sum(v ** 2 for i, v in bins)
        if s != 0:
            bin_formant = sum(i * v ** 2 for i, v in bins) / s
    return {
        'freq': bin_formant / C,
        'amp': amp_peak * amp_tone,
    }

def find_tone(spectrum, amp_tone, phonetic=None):
    formants = [
        find_formant(spectrum, *i, amp_tone)
        for i in FORMANT_BIN_RANGES
    ]
    if not phonetic or phonetic in VOICED:
        spectrum = [i * amp_tone for i in spectrum[:BINS_TONE]]
    else:
        spectrum = [0] * BINS_TONE
    return {
        'amp': amp_tone,
        'formants': formants,
        'spectrum': spectrum,
    }

def find_noise(spectrum, amp_noise, phonetic=None):
    thresh = sorted(spectrum)[len(spectrum) * 3 // 4]
    for i, v in enumerate(spectrum):
        if v >= thresh:
            lo = i
            break
    for i, v in reversed(list(enumerate(spectrum))):
        if v >= thresh:
            hi = i
            break
    amp_peak = max(spectrum[lo:hi+1])
    peak = spectrum.index(amp_peak)
    if not phonetic or phonetic in FRICATIVES:
        spectrum = [
            spectrum[i * len(spectrum) // BINS_NOISE] * amp_noise
            for i in range(BINS_NOISE)
        ]
    else:
        spectrum = [0] * BINS_NOISE
    return {
        'amp': amp_noise,
        'freq_lo': lo / C,
        'freq_peak': peak / C,
        'amp_peak': amp_peak * amp_noise,
        'freq_hi': hi / C,
        'spectrum': spectrum,
    }

def parameterize(spectrum, amp_tone, amp_noise, phonetic=None):
    return {
        'tone': find_tone(spectrum, amp_tone, phonetic),
        'noise': find_noise(spectrum, amp_noise, phonetic),
    }

def sample_system():
    spectrum = stft.spectrum()
    lo = math.sqrt(sum(i ** 2 for i in spectrum[1:6]))
    hi = math.sqrt(sum(i ** 2 for i in spectrum[6:]))
    return (
        spectrum,
        lo * GAIN_LO,
        hi * GAIN_HI,
    )

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
            'fricative': phonetic in FRICATIVES,
            'frames': frames_from_params(self.params[0], stop)  # for stops, just take the first recital
        }
        self.params.clear()

    def add_0(self):
        self.info['0'] = {
            'type': 'continuant',
            'voiced': False,
            'fricative': False,
            'frames': frames_from_params([{
                'tone': find_tone([0] * BINS_STFT, 0),
                'noise': find_noise([0] * BINS_STFT, 0),
            }]),
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
