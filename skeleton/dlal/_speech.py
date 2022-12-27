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

PHONETIC_DESCRIPTIONS = {
    'ae': 'a as in apple',
    'ay': 'a as in day',
    'a': 'a as in aw',
    'e': 'e as in bed',
    'y': 'e as in eat',
    'i': 'i as in it',
    'o': 'o as in oh',
    'w': 'oo as in zoo',
    'uu': 'oo as in foot',
    'u': 'u as in uh',
    'sh': 'sh as in shock',
    'sh_v': 's as in fusion',
    'h': 'h as in heel',
    'f': 'f as in foot',
    'v': 'v as in vine',
    'th': 'th as in thin',
    'th_v': 'th as in the',
    's': 's as in soon',
    'z': 'z as in zoo',
    'm': 'm as in map',
    'n': 'n as in nap',
    'ng': 'ng as in thing',
    'r': 'r as in run',
    'l': 'l as in left',
    'p': 'p as in pine (repeat)',
    'b': 'b as in bin (repeat)',
    't': 't as in tag (repeat)',
    'd': 'd as in day (repeat)',
    'k': 'k as in cook (repeat)',
    'g': 'g as in go (repeat)',
    'ch': 'ch as in choose (repeat)',
    'j': 'j as in jog (repeat)',
}

RECORD_DURATION_UNSTRESSED_VOWEL = 1
RECORD_DURATION_TRANSITION = 1
RECORD_DURATION_GO = 4

FORMANT_RANGES = [
    [0, 200],
    [200, 1000],
    [800, 2300],
    [1500, 3200],
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
        run_size=64,
    ):
        self.stft_bins = stft_bins
        self.tone_bins = tone_bins
        self.noise_bins = noise_bins
        self.sample_rate = sample_rate
        self.run_size = run_size
        self.freq_per_bin = sample_rate / stft_bins
        self.freq_per_bin_noise = sample_rate / 2 / noise_bins
        self.phonetics = {}
        self.formant_path_plot_data = {}
        if path: self.load(path)

    def find_formant(
        self,
        spectrum,
        freq_i,
        freq_f,
        formant_below_freq=0,
        formant_prev_freq=None,
    ):
        # look for formant near where it was before
        if formant_prev_freq:
            e = 200
            freq_i = max(freq_i, formant_prev_freq - e)
            freq_f = min(freq_f, formant_prev_freq + e)
        # convert freq range to bins
        bin_i = _math.floor(freq_i / self.freq_per_bin)
        bin_f = _math.floor(freq_f / self.freq_per_bin)
        # make sure above formant below, and non-empty window
        bin_i = min(
            max(
                bin_i,
                _math.floor(formant_below_freq / self.freq_per_bin) + 4
            ),
            bin_f - 1,
        )
        # avoid below formant
        spread = 3
        spectrum = spectrum[:]
        if formant_below_freq:
            formant_below_bin = _math.floor(formant_below_freq / self.freq_per_bin)
            a = max(formant_below_bin - spread, 0)
            b = min(formant_below_bin + spread + 1, len(spectrum))
            for i in range(a, b):
                spectrum[i] = 0
        # find peak
        spread = 2
        e_peak = 0
        if formant_prev_freq:
            bin_peak = int(formant_prev_freq / self.freq_per_bin)
        else:
            bin_peak = (bin_i + bin_f) // 2
        for i in range(bin_i, bin_f):
            a = max(i-spread, 0)
            b = min(i+spread+1, len(spectrum))
            for j in range(a, b):
                window = spectrum[a:b]
                e_window = sum(i ** 2 for i in window)
                if e_window > e_peak:
                    e_peak = e_window
                    bin_peak = i
        # adjust based on neighboring bin amps
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
                bin_formant = max(bin_formant, bin_i)
                bin_formant = min(bin_formant, bin_f)
        #
        return {
            'freq': bin_formant * self.freq_per_bin,
            'amp': _math.sqrt(e_peak),
        }

    def find_tone(self, spectrum, phonetic=None, formants_prev=None):
        # find formants
        formants = []
        formant_below_freq = 0
        for i, [freq_i, freq_f] in enumerate(FORMANT_RANGES):
            formant = self.find_formant(
                spectrum,
                freq_i,
                freq_f,
                formant_below_freq,
                formants_prev and formants_prev[i]['freq'],
            )
            formant_below_freq = formant['freq']
            if phonetic and phonetic not in VOICED:
                formant['amp'] = 0
            formants.append(formant)
        # find tone spectrum
        if not phonetic or phonetic in VOICED:
            # take all bins with amplitudes above twice median
            spectrum_tone = []
            median = sorted(spectrum)[len(spectrum) // 2]
            threshold = 2 * median
            for i in range(self.tone_bins):
                v = 0
                if spectrum[i] > threshold:
                    v = spectrum[i]
                spectrum_tone.append(v)
        else:
            spectrum_tone = [0] * self.tone_bins
        #
        return {
            'formants': formants,
            'spectrum': spectrum_tone,
        }

    def find_noise(self, spectrum, phonetic=None):
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
                if i * self.freq_per_bin < 1000: continue
                spectrum_noise[_math.floor(i / len(spectrum) * self.noise_bins)] += amp
        #
        return {
            'freq_c': f / s if s else 0,
            'hi': hi / s2 if s2 else 0,
            'spectrum': spectrum_noise,
        }

    def parameterize(self, spectrum, amp_tone, amp_noise, phonetic=None, formants_prev=None):
        if phonetic and phonetic not in VOICED:
            amp_tone = 0
        tone = self.find_tone(spectrum, phonetic, formants_prev)
        noise = self.find_noise(spectrum, phonetic)
        f = _math.sqrt(sum([
            sum(i ** 2 for i in tone['spectrum']),
            sum(i ** 2 for i in noise['spectrum']),
        ]))
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

    def frames_from_paramses(self, paramses, continuant=True):
        if continuant:
            return [{
                'toniness': Model.aggregate(paramses, ['toniness']),
                'tone': {
                    'formants': [
                        {
                            'freq': Model.aggregate(paramses, ['tone', 'formants', i, 'freq'], True),
                            'amp': Model.aggregate(paramses, ['tone', 'formants', i, 'amp']),
                        }
                        for i in range(len(FORMANT_RANGES))
                    ],
                    'spectrum': [
                        Model.aggregate(paramses, ['tone', 'spectrum', i])
                        for i in range(self.tone_bins)
                    ],
                },
                'noise': {
                    'freq_c': Model.aggregate(paramses, ['noise', 'freq_c']),
                    'hi': Model.aggregate(paramses, ['noise', 'hi']),
                    'spectrum': [
                        Model.aggregate(paramses, ['noise', 'spectrum', i])
                        for i in range(self.noise_bins)
                    ],
                },
                'amp': 1,
            }]
        else:
            f_max = max([i['f'] for i in paramses]) or 1
            return [
                {
                    **i,
                    'amp': i['f'] / f_max,
                }
                for i in paramses
            ]

    def add(self, phonetic, samples):
        continuant = phonetic not in STOPS
        voiced = phonetic in VOICED
        if voiced and continuant:
            # track formants movement from unstressed vowel to phonetic
            stride = int(0.1 * self.sample_rate / self.run_size)  # in speech samples (not audio samples)
            start = int((RECORD_DURATION_UNSTRESSED_VOWEL + RECORD_DURATION_TRANSITION + 1) * self.sample_rate / self.run_size)  # in speech samples (not audio samples)
            formants = [
                {'amp': 0, 'freq': 100},
                {'amp': 0, 'freq': 500},
                {'amp': 0, 'freq': 1000},
                {'amp': 0, 'freq': 2500},
            ]
            plot_data = []
            for i_sample in range(0, start, stride):
                paramses = [self.parameterize(*i, phonetic, formants) for i in samples[i_sample:i_sample+stride]]
                frame = self.frames_from_paramses(paramses, True)[0]
                formants = frame['tone']['formants']
                plot_data.append({
                    'spectrum': frame['tone']['spectrum'],
                    'formants': formants,
                })
            # get this phonetic's formants
            self.formant_path_plot_data[phonetic] = plot_data
            paramses = [self.parameterize(*i, phonetic, formants) for i in samples[start:]]
            frames = self.frames_from_paramses(paramses, continuant)
        else:
            paramses = [self.parameterize(*i, phonetic) for i in samples]
            frames = self.frames_from_paramses(paramses, continuant)
            if not continuant:
                i_start = next(i for i, frame in enumerate(frames) if frame['amp'] > 0.9)
                frames = frames[i_start:]
                try:
                    i_end = next(i for i, frame in enumerate(frames) if frame['amp'] < 0.1)
                except StopIteration:
                    i_end = None
                frames = frames[:i_end]
        self.phonetics[phonetic] = {
            'type': 'continuant' if continuant else 'stop',
            'voiced': voiced,
            'fricative': phonetic in FRICATIVES,
            'frames': frames,
        }

    def add_0(self):
        self.add('0', [[[0] * self.stft_bins, 0, 0]])

    def save(self, path):
        with open(path, 'w') as f:
            _json.dump(self.phonetics, f, indent=2)

    def save_formant_path_plot_data(self, path):
        with open(path, 'w') as f:
            _json.dump(self.formant_path_plot_data, f, indent=2)

    def load(self, path):
        with open(path, 'r') as f:
            self.phonetics = _json.load(f)

    def duration(self, phonetic, default):
        if phonetic in STOPS:
            return len(self.phonetics[phonetic]['frames']) * self.run_size / self.sample_rate
        else:
            return default

class Syllable:
    def __init__(self, onset, nucleus, coda, default_wait, model):
        self.onset = onset
        self.nucleus = nucleus
        self.coda = coda
        self.default_wait = default_wait
        self.model = model
        self.start = None
        self.end = None
        self.speedup = 1

    def __iter__(self):
        if self.speedup == 1:
            for phonetic in self.onset:
                yield phonetic, self.model.duration(phonetic, self.default_wait)
            duration_nucleus = self.duration() - self.duration_segment(self.onset) - self.duration_segment(self.coda)
            for phonetic in self.nucleus:
                yield phonetic, duration_nucleus / len(self.nucleus)
            for phonetic in self.coda:
                yield phonetic, self.model.duration(phonetic, self.default_wait)
        else:
            for segment in self.segments():
                for phonetic in segment:
                    yield phonetic, self.model.duration(phonetic, self.default_wait) / self.speedup

    def from_str(s, default_wait, model):
        split = s.split('.')
        if len(split) == 1:
            segments = '', split[0], ''
        elif len(split) == 2:
            segments = split[0], split[1], ''
        elif len(split) == 3:
            segments = split
        else:
            raise Exception(f'invalid syllable {s}')
        segments = [Utterance.phonetics_from_str(i) for i in segments]
        return Syllable(*segments, default_wait, model)

    def squeeze(self):
        expected_duration = self.end - self.start
        if expected_duration == 0:
            self.speedup = _math.inf
            return
        actual_duration = self.duration()
        if actual_duration > expected_duration:
            self.speedup = actual_duration / expected_duration

    def duration(self):
        return max(
            sum(self.duration_segment(i) for i in self.segments()),
            self.end - self.start,
        )

    def duration_segment(self, phonetics):
        return sum(self.model.duration(i, self.default_wait) for i in phonetics)

    def segments(self):
        return self.onset, self.nucleus, self.coda

class Utterance:
    def __init__(
        self,
        model=None,
        default_wait=1/6,
        default_pitch=42,
    ):
        self.phonetics = []
        self.waits = []
        self.pitches = []
        self.model = model
        self.default_wait = default_wait
        self.default_pitch = default_pitch

    def __iter__(self):
        return iter(zip(self.phonetics, self.waits, self.pitches))

    def from_str(s, *args, **kwargs):
        self = Utterance(*args, **kwargs)
        self.phonetics = Utterance.phonetics_from_str(s.replace(' ', '0'))
        if self.phonetics[-1] != '0':
            self.phonetics.append('0')
        self.infer()
        self.add_prestop_silence()
        return self

    def from_syllables_and_notes(syllables, notes, model, *args, **kwargs):
        self = Utterance(model, *args, **kwargs)
        syllables = [Syllable.from_str(i, self.default_wait, self.model) for i in syllables.split()]
        for syllable, note in zip(syllables, notes):
            syllable.start = note['on'] / self.model.sample_rate
            syllable.end = note['off'] / self.model.sample_rate
            syllable.squeeze()
            silence = syllable.start - sum(self.waits)
            if silence > 1e-2:
                self.phonetics.append('0')
                self.waits.append(silence)
                self.pitches.append(self.pitches[-1] if self.pitches else self.default_pitch)
            for phonetic, wait in syllable:
                self.phonetics.append(phonetic)
                self.waits.append(wait)
                self.pitches.append(note['number'])
        self.add_prestop_silence()
        return self

    def phonetics_from_str(s):
        phonetics = []
        bracketed_phonetic = None
        for c in s:
            if c == '[':
                bracketed_phonetic = ''
            elif c == ']':
                phonetics.append(bracketed_phonetic)
                bracketed_phonetic = None
            elif bracketed_phonetic != None:
                bracketed_phonetic += c
            else:
                phonetics.append(c)
        return phonetics

    def infer(self):
        while len(self.waits) < len(self.phonetics):
            wait = self.default_wait
            if self.model:
                wait = self.model.duration(self.phonetics[len(self.waits)], wait)
            self.waits.append(wait)
        while len(self.pitches) < len(self.phonetics):
            self.pitches.append(self.pitches[-1] if self.pitches else self.default_pitch)

    def add_prestop_silence(self):
        silences = []
        for i, phonetic in enumerate(self.phonetics):
            if i == 0: continue
            if phonetic in STOPS:
                old = self.waits[i-1]
                self.waits[i-1] = max(
                    self.waits[i-1] - 0.05,
                    self.waits[i-1] / 2,
                )
                silences.append((i, old - self.waits[i-1]))
        for i, wait in reversed(silences):
            self.phonetics.insert(i, '0')
            self.waits.insert(i, wait)
            self.pitches.insert(i, self.pitches[i-1])

    def print(self):
        i = 0
        stride = 10
        while i < len(self.phonetics):
            s = min(stride, len(self.phonetics) - i)
            for j in range(s): print(f'{self.phonetics[i+j]:>8}', end='')
            print()
            for j in range(s): print(f'{self.waits[i+j]:>8.2f}', end='')
            print()
            for j in range(s): print(f'{self.pitches[i+j]:>8}', end='')
            print()
            i += stride
