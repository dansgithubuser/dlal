'''
`phonetic` - symbol representing a sound
`sample` - a single audio run's worth of sound information about a phonetic
`params` - phonetic parameters derived from a `sample`
`frames` - aggregated and focused `params` ready for use in synthesis
`info` - `frames` and prior information for a `phonetic`
'''

import json as _json
import math as _math

PHONETICS = [
    'ae', 'ay', 'a', 'e', 'y', 'i', 'o', 'w', 'uu', 'u',
    'sh', 'sh_v', 'h', 'f', 'v', 'th', 'th_v', 's', 'z', 'm', 'n', 'ng', 'r', 'l',
    'p', 'b', 't', 'd', 'k', 'g', 'ch', 'j',
]

VOICED = [
    'ae', 'ay', 'a', 'e', 'y', 'i', 'o', 'w', 'uu', 'u',
    'sh_v', 'v', 'th_v', 'z', 'm', 'n', 'ng', 'r', 'l',
]

FRICATIVES = [
    'sh', 'sh_v', 'h', 'f', 'v', 'th', 'th_v', 's', 'z',
    'p', 'b', 't', 'd', 'k', 'g', 'ch', 'j',
]

STOPS = [
    'p', 'b', 't', 'd', 'k', 'g', 'ch', 'j',
]

RECORD_DURATION_PREP = 3
RECORD_DURATION_GO = 6
RECORD_DURATION_STOP = 1

FORMANT_RANGES = [
    [0, 200],
    [200, 1000],
    [1000, 2300],
    [2300, 3000],
]

class Model:
    def mean(l):
        return sum(l) / len(l)

    def descend(x, ks):
        for k in ks: x = x[k]
        return x

    def aggregate(x, ks, reject_outliers=False):
        x = [Model.descend(i, ks) for i in x]
        m = Model.mean(x)
        if reject_outliers:
            r = max(x) - min(x)
            x2 = [i for i in x if abs(i-m) <= r/4]
            if len(x2):
                m = Model.mean(x2)
        return m

    def __init__(
        self,
        path=None,
        stft_bins=512,
        tone_bins=64,
        noise_bins=64,
        sample_rate=44100,
    ):
        self.stft_bins = stft_bins
        self.tone_bins = tone_bins
        self.noise_bins = noise_bins
        self.sample_rate = sample_rate
        self.freq_per_bin = sample_rate / stft_bins
        self.phonetics = {}
        if path: self.load(path)

    def find_formant(self, spectrum, freq_i, freq_f, amp_tone, formant_freq_prev=0):
        bin_i = _math.floor(freq_i / self.freq_per_bin)
        bin_f = _math.floor(freq_f / self.freq_per_bin)
        bin_i = min(
            max(
                bin_i,
                _math.floor(formant_freq_prev / self.freq_per_bin) + 4
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
            'freq': bin_formant * self.freq_per_bin,
            'amp': _math.sqrt(e_window) * amp_tone,
        }

    def find_tone(self, spectrum, amp_tone, phonetic=None):
        # find formants
        formants = []
        formant_freq_prev = 0
        for [freq_i, freq_f] in FORMANT_RANGES:
            formant = self.find_formant(spectrum, freq_i, freq_f, amp_tone, formant_freq_prev)
            formant_freq_prev = formant['freq']
            formants.append(formant)
        # normalize so highest formant has amp=1
        f = max(i['amp'] for i in formants)
        if f:
            for i in formants:
                i['amp'] /= f
        # find tone spectrum, remove from full spectrum
        if not phonetic or phonetic in VOICED:
            # take all bins with amplitudes above twice median
            spectrum_tone = []
            median = sorted(spectrum)[len(spectrum) // 2]
            threshold = 2 * median
            for i in range(self.tone_bins):
                v = 0
                if spectrum[i] > threshold:
                    v = spectrum[i] * amp_tone
                    spectrum[i] -= v
                    if spectrum[i] < 0: spectrum[i] = 0
                spectrum_tone.append(v)
        else:
            spectrum_tone = [0] * self.tone_bins
        #
        return {
            'formants': formants,
            'spectrum': spectrum_tone,
        }

    def find_noise(self, spectrum, amp_noise, phonetic=None):
        f = 0  # amplitude-weighted sum of frequencies (to find center frequency)
        s = 0  # sum of amplitudes (to find center frequency)
        hi = 0  # high-frequency energy
        s2 = 0  # squared sum of amplitudes (to normalize high-frequency energy)
        for i, v in enumerate(spectrum):
            freq = i * self.freq_per_bin
            if freq < 2000: continue
            f += freq * v
            s += v
            if freq > 12000: hi += v ** 2
            s2 += v ** 2
        # find noise spectrum
        spectrum_noise = [0] * self.noise_bins
        if not phonetic or phonetic in FRICATIVES:
            for i, amp in enumerate(spectrum):
                spectrum_noise[_math.floor(i / len(spectrum) * self.noise_bins)] += amp * amp_noise
        #
        return {
            'freq_c': f / s if s else 0,
            'hi': hi / s2 if s2 else 0,
            'spectrum': spectrum_noise,
        }

    def parameterize(self, spectrum, amp_tone, amp_noise, phonetic=None):
        if phonetic and phonetic not in VOICED:
            amp_tone = 0
        spectrum = [i for i in spectrum]
        tone = self.find_tone(spectrum, amp_tone, phonetic)
        noise = self.find_noise(spectrum, amp_noise, phonetic)
        f = _math.sqrt(sum([
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
            'f': f,
        }

    def frames_from_params(self, params, continuant=True):
        if continuant:
            return [{
                'toniness': Model.aggregate(params, ['toniness']),
                'tone': {
                    'formants': [
                        {
                            'freq': Model.aggregate(params, ['tone', 'formants', i, 'freq'], True),
                            'amp': Model.aggregate(params, ['tone', 'formants', i, 'amp']),
                        }
                        for i in range(len(FORMANT_RANGES))
                    ],
                    'spectrum': [
                        Model.aggregate(params, ['tone', 'spectrum', i])
                        for i in range(self.tone_bins)
                    ],
                },
                'noise': {
                    'freq_c': Model.aggregate(params, ['noise', 'freq_c']),
                    'hi': Model.aggregate(params, ['noise', 'hi']),
                    'spectrum': [
                        Model.aggregate(params, ['noise', 'spectrum', i])
                        for i in range(self.noise_bins)
                    ],
                },
                'amp': 1,
            }]
        else:
            f_max = max([i['f'] for i in params]) or 1
            return [
                {
                    **i,
                    'amp': i['f'] / f_max,
                }
                for i in params
            ]

    def add(self, phonetic, samples):
        params = [self.parameterize(*i, phonetic) for i in samples]
        continuant = phonetic not in STOPS
        frames = self.frames_from_params(params, continuant)
        if not continuant:
            i_start = next(i for i, frame in enumerate(frames) if frame['amp'] > 0.9)
            frames = frames[i_start:]
            i_end = next(i for i, frame in enumerate(frames) if frame['amp'] < 0.1)
            frames = frames[:i_end]
        self.phonetics[phonetic] = {
            'type': 'continuant' if continuant else 'stop',
            'voiced': phonetic in VOICED,
            'fricative': phonetic in FRICATIVES,
            'frames': frames,
        }

    def add_0(self):
        self.add('0', [[[0] * self.stft_bins, 0, 0]])

    def save(self, path):
        with open(path, 'w') as f:
            _json.dump(self.phonetics, f, indent=2)

    def load(self, path):
        with open(path, 'r') as f:
            self.phonetics = _json.load(f)
