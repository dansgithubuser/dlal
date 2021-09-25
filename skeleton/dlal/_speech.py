import json as _json
import math as _math
import re as _re

FEATURES = [
    'toniness',
    'f1_freq',
    'f2_freq',
    'f2_amp',
    'f3_amp',
    'freq_c',
    'hi',
]

class _Code:
    def __init__(self, code):
        m = _re.match(r'(-)?(\w+)', code)
        self.glide = m.group(1)
        self.phonetic = m.group(2)

class Phonetizer:
    def __init__(
        self,
        synthesize,
        continuant_wait=44100//8,
        grace = 44100//100,
        model_path='assets/phonetics/model.json',
        transamses_path='assets/phonetics/transamses.json',
        sample_rate=44100,
    ):
        '''
        `synthesize` is a function that takes:
            - tone_spectrum (64 bins from 0 to 5512.5)
            - noise_spectrum (64 bins from 0 to 22050)
            - wait (number of samples to synthesize for)
        and synthesizes the corresponding sound.

        `grace` is how much time is allowed between notes without synthesizing a silence
        '''
        self.synthesize = synthesize
        self.continuant_wait = continuant_wait
        self.grace = grace
        with open(model_path) as file:
            self.model = _json.loads(file.read())
        self.sample_rate = sample_rate
        self.phonetic = '0'
        with open(transamses_path) as f:
            self.transamses = _json.loads(f.read())
        self._smoother = Smoother()

    def say_params(self, info, frame_i, wait, smooth):
        for i in range(0, wait, 64):
            params = self._smoother.smooth(info['frames'][frame_i], smooth)
            d_min = _math.inf
            transams_min = None
            for transams in self.transamses:
                d = params_distance(params, transams)
                if d < d_min:
                    transams_min = transams
                    d_min = d
            self.synthesize(
                transams_min['tone']['spectrum'],
                transams_min['noise']['spectrum'],
                64,
            )

    def say_code(self, code, continuant_wait=None, speed=1):
        if type(code) == str: code = _Code(code)
        if continuant_wait == None:
            continuant_wait = self.continuant_wait
        info = self.model[code.phonetic]
        if code.glide:
            smooth = 0.9
        else:
            smooth = 0.8
        # say
        total_wait = 0
        for i in range(len(info['frames'])):
            if info['type'] == 'continuant':
                wait = continuant_wait
            else:
                wait = info['frames'][i]['duration']
            wait /= speed
            wait = int(wait)
            total_wait += wait
            self.say_params(info, i, wait, smooth)
        self.phonetic = code.phonetic
        return total_wait

    def say_code_string(self, code_string, end='0'):
        code_string += end
        codes = Phonetizer._parse_code_string(code_string)
        for code in codes:
            self.say_code(code)

    def say_syllables(self, syllables, notes, advance=0):
        # translate into onset, nucleus, coda
        syllables = [syllable.split('.') for syllable in syllables.split()]
        for i in range(len(syllables)):
            syllable = syllables[i]
            if len(syllable) == 1:
                onset, nucleus, coda = '', syllable[0], ''
            elif len(syllable) == 2:
                onset, nucleus, coda = syllable[0], syllable[1], ''
            elif len(syllable) == 3:
                onset, nucleus, coda = syllable
            else:
                raise Exception(f'invalid syllable {syllable}')
            syllables[i] = [onset, nucleus, coda]
        # move onsets into codas
        for i in range(1, len(syllables)):
            if not syllables[i][0]: continue
            syllables[i-1][2] += syllables[i][0]
            syllables[i][0] = ''
        # say
        self.sample = 0
        for syllable, note in zip(syllables, notes):
            # parse phonetics
            onset, nucleus, coda = [
                Phonetizer._parse_code_string(code_string)
                for code_string in syllable
            ]
            # figure timing and say
            start = note['on'] - advance
            if start < 0: continue
            normal_durations = [self._durate_codes(codes) for codes in [onset, nucleus, coda]]
            normal_duration = sum(normal_durations)
            end = note['off'] - advance
            if normal_duration < end - start:
                # enough time to say nucleus normally or extended
                coda_start = end - normal_durations[2]
                self._say_codes(onset, start)
                self._say_codes(nucleus, total_continuant_wait=(coda_start - self.sample))
                self._say_codes(coda, coda_start)
            else:
                # need speed-up
                speed = normal_duration / (end - start)
                self._say_codes(onset, start, speed=speed)
                self._say_codes(nucleus, speed=speed)
                self._say_codes(coda, speed=speed)
        self._say_codes(['0'], start)

    def _say_codes(self, codes, start=None, total_continuant_wait=None, speed=1):
        for i in range(len(codes)):
            if type(codes[i]) == str:
                codes[i] = _Code(codes[i])
        # figure arguments
        if start == None:
            start = self.sample
        if total_continuant_wait != None:
            continuant_wait = (
                total_continuant_wait
                //
                len([code for code in codes if self.model[code.phonetic]['type'] == 'continuant'])
            )
        else:
            continuant_wait = None
        # synthesize silence if there's sufficient space between phonetics
        if start - self.sample > self.grace:
            self.say_code('0', continuant_wait=start - self.sample)
            self.sample = start
        # say
        for code in codes:
            self.sample += self.say_code(code, continuant_wait=continuant_wait, speed=speed)

    def _durate_codes(self, codes):
        result = 0
        for code in codes:
            if type(code) == str: code = _Code(code)
            info = self.model[code.phonetic]
            if info['type'] == 'continuant':
                result += self.continuant_wait
            else:
                result += sum(i['duration'] for i in info['frames'])
        return result

    def _parse_code_string(code_string):
        not_brackets = r'[^\[\]]'
        return [
            _Code(i.translate({ord('['): None, ord(']'): None}))
            for i in _re.findall(f'{not_brackets}|\[{not_brackets}+\]', code_string)
        ]

def get_param(params, ks):
    x = params
    for k in ks: x = x[k]
    if type(x) == list: x = x[0]
    return x

def get_features(params, normalized=True):
    features = (
        get_param(params, ['toniness']),
        get_param(params, ['tone', 'formants', 1, 'freq']),
        get_param(params, ['tone', 'formants', 2, 'freq']),
        get_param(params, ['tone', 'formants', 2, 'amp']),
        get_param(params, ['tone', 'formants', 3, 'amp']),
        get_param(params, ['noise', 'freq_c']),
        get_param(params, ['noise', 'hi']),
    )
    if normalized:
        def clamp(x):
            assert 0 <= x <= 1
            return x
        return (
            clamp(features[0]),
            clamp(features[1] / 1250),
            clamp((features[2] - 750) / 1750),
            clamp(features[3]),
            clamp(features[4]),
            clamp(features[5] / 22050),
            clamp(features[6]),
        )
    else:
        return features

def params_distance(a, b):
    return features_distance(get_features(a), get_features(b))

def features_distance(a, b):
    a_toniness, a_f1, a_f2, a_f2_amp, a_f3_amp, a_fn, a_hi = a
    b_toniness, b_f1, b_f2, b_f2_amp, b_f3_amp, b_fn, b_hi = b
    d_tone = (a_f1 - b_f1) ** 2 + (a_f2 - b_f2) ** 2 + (a_f2_amp - b_f2_amp) ** 2 + (a_f3_amp - b_f3_amp) ** 2
    d_noise = (a_fn - b_fn) ** 2 + (a_hi - b_hi) ** 2
    toniness = max(a_toniness, b_toniness)
    noisiness = (1 - min(a_toniness, b_toniness))
    d = d_tone * toniness + d_noise * noisiness + (a_toniness - b_toniness) ** 2
    return d

class Smoother:
    def __init__(self):
        self.fresh = True

    def smooth(self, frame, value):
        if self.fresh:
            self.fresh = False
            self.toniness = get_param(frame, ['toniness'])
            self.f1_freq = get_param(frame, ['tone', 'formants', 1, 'freq'])
            self.f2_freq = get_param(frame, ['tone', 'formants', 2, 'freq'])
            self.f2_amp = get_param(frame, ['tone', 'formants', 2, 'amp'])
            self.f3_amp = get_param(frame, ['tone', 'formants', 3, 'amp'])
            self.fn = get_param(frame, ['noise', 'freq_c'])
            self.hi = get_param(frame, ['noise', 'hi'])
            self.e_toniness = self.toniness
            self.e_f1_freq = self.f1_freq
            self.e_f2_freq = self.f2_freq
            self.e_f2_amp = self.f2_amp
            self.e_f3_amp = self.f3_amp
            self.e_fn = self.fn
            self.e_hi = self.hi
        else:
            self.e_toniness = value * self.e_toniness + (1 - value) * get_param(frame, ['toniness'])
            self.e_f1_freq = value * self.e_f1_freq + (1 - value) * get_param(frame, ['tone', 'formants', 1, 'freq'])
            self.e_f2_freq = value * self.e_f2_freq + (1 - value) * get_param(frame, ['tone', 'formants', 2, 'freq'])
            self.e_f2_amp = value * self.e_f2_amp + (1 - value) * get_param(frame, ['tone', 'formants', 2, 'amp'])
            self.e_f3_amp = value * self.e_f3_amp + (1 - value) * get_param(frame, ['tone', 'formants', 3, 'amp'])
            self.e_fn = value * self.e_fn + (1 - value) * get_param(frame, ['noise', 'freq_c'])
            self.e_hi = value * self.e_hi + (1 - value) * get_param(frame, ['noise', 'hi'])
            self.toniness = value * self.toniness + (1 - value) * self.e_toniness
            self.f1_freq = value * self.f1_freq + (1 - value) * self.e_f1_freq
            self.f2_freq = value * self.f2_freq + (1 - value) * self.e_f2_freq
            self.f2_amp = value * self.f2_amp + (1 - value) * self.e_f2_amp
            self.f3_amp = value * self.f3_amp + (1 - value) * self.e_f3_amp
            self.fn = value * self.fn + (1 - value) * self.e_fn
            self.hi = value * self.hi + (1 - value) * self.e_hi
        return {
            'toniness': self.toniness,
            'tone': {
                'formants': [
                    None,
                    {
                        'freq': self.f1_freq,
                    },
                    {
                        'freq': self.f2_freq,
                        'amp': self.f2_amp,
                    },
                    {
                        'amp': self.f3_amp,
                    },
                ],
            },
            'noise': {
                'freq_c': self.fn,
                'hi': self.hi,
            },
        }
