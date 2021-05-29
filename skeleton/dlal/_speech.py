import json as _json
import re as _re

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
        sample_rate=44100,
    ):
        '''
        `synthesize` is a function that takes:
            - info (full phonetic information)
            - frame_i (frame number to synthesize)
            - wait (number of samples to synthesize for)
            - smooth (how smoothly to interpolate from previous parameters)
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

    def say_code(self, code, continuant_wait=None, speed=1):
        if type(code) == str: code = _Code(code)
        if continuant_wait == None:
            continuant_wait = self.continuant_wait
        info = self.model[code.phonetic]
        # smooth
        if speed > 1:
            smooth = 0.5
        elif code.glide:
            smooth = 0.98
        elif any([
            not self.model[self.phonetic]['voiced'],  # starting from unvoiced
            not info['voiced'],  # moving to unvoiced
            self.model[self.phonetic]['type'] == 'stop',  # starting from stop
        ]):
            smooth = 0.9
        elif any([
            info['type'] == 'stop',  # moving to (voiced) stop
        ]):
            smooth = 0.7
        else:  # moving between continuants
            smooth = 0.9
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
            self.synthesize(info=info, frame_i=i, wait=wait, smooth=smooth)
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
        if len(syllables) and syllables[0][0]:
            syllables.insert(0, ['', '0', syllables[0][0]])
            syllables[0][0] = ''
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
