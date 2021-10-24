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
    'p', 'b', 't', 'd', 'k', 'g', 'ch', 'j',
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

def stats(l, ks, reject_outliers=False):
    l = [descend(i, ks) for i in l]
    m = mean(l)
    if reject_outliers:
        r = max(l) - min(l)
        l2 = [i for i in l if abs(i-m) <= r/4]
        if len(l2):
            l = l2
            m = mean(l)
    return (
        m,
        math.sqrt(mean([(i - m) ** 2 for i in l])),
    )

def frames_from_params(params, stop=False):
    if not stop:
        return [
            {
                'toniness': stats(params, ['toniness']),
                'tone': {
                    'formants': [
                        {
                            'freq': stats(params, ['tone', 'formants', i, 'freq'], True),
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
                    'freq_c': stats(params, ['noise', 'freq_c']),
                    'hi': stats(params, ['noise', 'hi']),
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
                'toniness': stats([k], ['toniness']),
                'tone': {
                    'formants': [
                        {
                            'freq': stats([k], ['tone', 'formants', i, 'freq'], True),
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
                    'freq_c': stats([k], ['noise', 'freq_c']),
                    'hi': stats([k], ['noise', 'hi']),
                    'spectrum': [
                        stats([k], ['noise', 'spectrum', i])
                        for i in range(BINS_NOISE)
                    ],
                },
                'duration': RUN_SIZE,
            }
            for k in params
        ]

def find_formant(spectrum, bin_i, bin_f, amp_tone, formant_freq_prev=0):
    bin_i = min(
        max(
            bin_i,
            math.floor(formant_freq_prev * C) + 4
        ),
        bin_f - 1,
    )
    window = spectrum[bin_i:bin_f]
    bin_peak = window.index(max(window)) + bin_i
    bin_formant = bin_peak
    spread = 2
    if bin_peak >= spread and bin_peak < len(spectrum) - spread:
        bins = [
            (i, spectrum[i])
            for i in range(bin_peak - spread, bin_peak + spread + 1)
        ]
        s = sum(v ** 2 for i, v in bins)
        if s != 0:
            bin_formant = sum(i * v ** 2 for i, v in bins) / s
    e_window = sum(i ** 2 for i in window)
    return {
        'freq': bin_formant / C,
        'amp': math.sqrt(e_window) * amp_tone,
    }

def find_tone(spectrum, amp_tone, phonetic=None):
    formants = []
    formant_freq_prev = 0
    for i in FORMANT_BIN_RANGES:
        formant = find_formant(spectrum, *i, amp_tone, formant_freq_prev)
        formant_freq_prev = formant['freq']
        formants.append(formant)
    f = max(i['amp'] for i in formants)
    if f:
        for i in formants:
            i['amp'] /= f
    spectrum_tone = [0] * BINS_TONE
    if not phonetic or phonetic in VOICED:
        spectrum_tone = []
        median = sorted(spectrum)[len(spectrum) // 2]
        threshold = 2 * median
        for i in range(BINS_TONE):
            v = 0
            if spectrum[i] > threshold:
                v = spectrum[i] * amp_tone
                spectrum[i] -= v
                if spectrum[i] < 0: spectrum[i] = 0
            spectrum_tone.append(v)
    return {
        'formants': formants,
        'spectrum': spectrum_tone,
    }

def find_noise(spectrum, amp_noise, phonetic=None):
    f = 0
    s = 0
    hi = 0
    s2 = 0
    for i, v in enumerate(spectrum):
        freq = i / C
        if freq < 2000: continue
        f += freq * v
        s += v
        if freq > 12000: hi += v ** 2
        s2 += v ** 2
    spectrum_noise = [0] * BINS_NOISE
    if not phonetic or phonetic in FRICATIVES:
        for i, amp in enumerate(spectrum):
            spectrum_noise[math.floor(i / len(spectrum) * BINS_NOISE)] += amp * amp_noise
    return {
        'freq_c': f / s if s else 0,
        'hi': hi / s2 if s2 else 0,
        'spectrum': spectrum_noise,
    }

def parameterize(spectrum, amp_tone, amp_noise, phonetic=None):
    tone = find_tone(spectrum, amp_tone, phonetic)
    noise = find_noise(spectrum, amp_noise, phonetic)
    f = math.sqrt(sum([
        sum(i ** 2 for i in tone['spectrum']),
        sum(i ** 2 for i in noise['spectrum']),
    ]))
    if f:
        tone['spectrum'] = [i/f for i in tone['spectrum']]
        noise['spectrum'] = [i/f for i in noise['spectrum']]
    amp = amp_tone + amp_noise
    if amp:
        toniness = amp_tone / amp
    else:
        toniness = 0
    return {
        'toniness': toniness,
        'tone': tone,
        'noise': noise,
    }

def sample_system():
    spectrum = stft.spectrum()
    amp_tone = 1e2 * math.sqrt(sum(i ** 2 for i in spectrum[1:6]))
    amp_noise = 1e2 * math.sqrt(sum(i ** 2 for i in spectrum[32:]))
    return (spectrum, amp_tone, amp_noise)

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
                'toniness': 0,
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
        runner.run(4)
        model.add_pre()
        runner.run(5, lambda remaining: model.add(phonetic, remaining))
        model.add_post(phonetic)
        runner.run(1)
    model.add_0()
    model.save()
