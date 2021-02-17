from . import _skeleton
from ._skeleton import connect as _connect
from . import _utils

import midi

import glob
import json
import math
import os
import re

class Subsystem:
    def __init__(self, *args, **kwargs):
        driver = _skeleton.driver_set(None)
        self.init(*args, **kwargs)
        if driver:
            self.add_to(driver)
            _skeleton.driver_set(driver)

    def init(self, components={}, inputs=[], outputs=[], name=None):
        if not hasattr(self, 'name'):
            if name == None: name = _utils.upper_camel_to_snake_case(self.__class__.__name__)
            self.name = name
            self.components = {}
            self.inputs = []
            self.outputs = []
        for name, spec in components.items():
            args = []
            kwargs = {}
            if type(spec) == str:
                kind = spec
            elif type(spec) == tuple:
                if len(spec) >= 1:
                    kind = spec[0]
                if len(spec) >= 2:
                    args = spec[1]
                if len(spec) >= 3:
                    kwargs = spec[2]
            self.add(name, kind, args, kwargs)
        self.inputs.extend(self.components[i] for i in inputs)
        self.outputs.extend(self.components[i] for i in outputs)

    def __repr__(self):
        return self.name

    def add(self, name, kind=None, args=[], kwargs={}):
        if kind == None:
            kind = name
        if type(kind) == str:
            build = _skeleton.component_class(kind)
        else:
            build = kind
        component = build(
            *args,
            **kwargs,
            name=self.name + '.' + kwargs.get('name', name),
        )
        self.components[name] = component
        setattr(self, name, component)

    def add_to(self, driver):
        for i in self.components.values():
            driver.add(i)

    def connect_inputs(self, other):
        _connect(other, self.inputs)

    def connect_outputs(self, other):
        _connect(self.outputs, other)

    def disconnect_inputs(self, other):
        _skeleton.disconnect(other, self.inputs)

    def disconnect_outputs(self, other):
        _skeleton.disconnect(self.outputs, other)

class IirBank(Subsystem):
    def init(self, order, name=None):
        components = {}
        for i in range(order):
            components[f'iirs[{i}]'] = 'iir'
            components[f'bufs[{i}]'] = 'buf'
        bufs = [f'bufs[{i}]' for i in range(order)]
        Subsystem.init(self, components, bufs, bufs, name=name)
        self.iirs = []
        self.bufs = []
        for i in range(order):
            self.iirs.append(self.components[f'iirs[{i}]'])
            self.bufs.append(self.components[f'bufs[{i}]'])
            self.iirs[-1].connect(self.bufs[-1])

class Phonetizer(Subsystem):
    def init(
        self,
        phonetics_path='assets/phonetics',
        sample_rate=44100,
        continuant_wait=44100//8,
        name=None,
    ):
        Subsystem.init(self,
            {
                'comm': 'comm',
                'tone_buf': 'buf',
                'noise_buf': 'buf',
                'tone_filter': (IirBank, [5]),
                'noise_filter': (IirBank, [5]),
            },
            name=name,
        )
        _connect(
            (self.tone_buf, self.noise_buf),
            (self.tone_filter, self.noise_filter),
        )
        self.outputs = self.tone_filter.outputs + self.noise_filter.outputs
        # phonetics
        self.phonetics = {}
        for path in glob.glob(os.path.join(phonetics_path, '*.phonetic.json')):
            phonetic = os.path.basename(path).split('.')[0]
            with open(path) as file:
                self.phonetics[phonetic] = json.loads(file.read())
        self.phonetic_name = '0'
        # sample rate
        self.sample_rate = sample_rate
        self.grace = sample_rate // 100
        # continuant_wait
        self.continuant_wait = continuant_wait
        self.say('z', 0, 0)
        self.say('0', 0, 0)

    def say(self, phonetic_name, continuant_wait=None, smooth=None, speed=1):
        phonetic = self.phonetics[phonetic_name]
        if continuant_wait == None:
            continuant_wait = self.continuant_wait
        if smooth == None:
            if speed > 1:
                smooth = 0.5
            elif any([
                self.phonetic_name == '0',  # starting from silence
                phonetic_name == '0',  # moving to silence
                phonetic['type'] == 'stop',  # moving to stop
                self.phonetics[self.phonetic_name]['type'] == 'stop',  # moving from stop
            ]):
                smooth = 0.7
            else:  # moving between continuants
                smooth = 0.9
        wait = int(phonetic.get('duration', continuant_wait) / len(phonetic['frames']) / speed)
        with _skeleton.UseComm(self.comm):
            for frame in phonetic['frames']:
                if 'tone_formants' in frame:
                    for iir, formant in zip(self.tone_filter.iirs, frame['tone_formants']):
                        w = formant['freq'] / self.sample_rate * 2 * math.pi
                        iir.command_detach('single_pole_bandpass', [w, 0.01, formant['amp'], smooth])
                else:
                    for iir in self.tone_filter.iirs:
                        iir.command_detach('gain', [0, smooth])
                if 'noise_formants' in frame:
                    for iir, formant in zip(self.noise_filter.iirs, frame['noise_formants']):
                        w = formant['freq'] / self.sample_rate * 2 * math.pi
                        iir.command_detach('single_pole_bandpass', [w, 0.01, formant['amp'], 0])
                else:
                    for iir in self.noise_filter.iirs:
                        iir.command_detach('gain', [0, smooth])
                self.comm.wait(wait)
        self.phonetic_name = phonetic_name
        return wait * len(phonetic['frames'])

    def prep_syllables(self, syllables, notes, advance=0, anticipation=None):
        if anticipation == None:
            anticipation = self.sample_rate // 8
        self.comm.resize(len(syllables) * (3 + 2 * len(self.iirs)))
        self.sample = 0
        for syllable, note in zip(syllables.split(), notes):
            segments = [
                [
                    i.translate({ord('['): None, ord(']'): None})
                    for i in re.findall(r'\w|\[\w+\]', segment)
                ]
                for segment in syllable.split('.')
            ]
            if len(segments) == 1:
                onset, nucleus, coda = [], segments[0], []
            elif len(segments) == 2:
                onset, nucleus, coda = segments[0], segments[1], []
            elif len(segments) == 3:
                onset, nucleus, coda = segments 
            else:
                raise Exception(f'invalid syllable {syllable}')
            start = note['on'] - advance
            if start < 0: continue
            if start - anticipation <= self.sample:  # not silence before this syllable
                start -= anticipation
            normal_durations = [self.phonetics_duration(i) for i in [onset, nucleus, coda]]
            normal_duration = sum(normal_durations)
            end = note['off'] - anticipation - advance
            if normal_duration < end - start:
                # enough time to say nucleus normally or extended
                coda_start = end - normal_durations[2]
                self.prep_phonetics(onset, start)
                self.prep_phonetics(nucleus, total_continuant_wait=(coda_start - self.sample))
                self.prep_phonetics(coda, coda_start)
            else:
                # need speed-up
                speed = normal_duration / (end - start)
                self.prep_phonetics(onset, start, speed=speed)
                self.prep_phonetics(nucleus, speed=speed)
                self.prep_phonetics(coda, speed=speed)

    def phonetics_duration(self, phonetics, continuant_wait=None):
        if continuant_wait == None:
            continuant_wait = self.continuant_wait
        return sum(
            self.phonetics[phonetic].get('duration', continuant_wait)
            for phonetic in phonetics
        )

    def prep_phonetics(self, phonetics, start=None, total_continuant_wait=None, speed=1):
        if start == None:
            start = self.sample
        if total_continuant_wait != None:
            continuant_wait = (
                total_continuant_wait
                //
                len([i for i in phonetics if self.phonetics[i]['type'] == 'continuant'])
            )
        else:
            continuant_wait = None
        if start - self.sample > self.grace:
            self.say('0', continuant_wait=0)
            self.comm.wait(start - self.sample)
            self.sample = start
        for phonetic in phonetics:
            self.sample += self.say(phonetic, continuant_wait=continuant_wait, speed=speed)

class Portamento(Subsystem):
    def init(self, name, slowness=0.999):
        Subsystem.init(self,
            {
                'rhymel': 'rhymel',
                'lpf': ('lpf', [slowness]),
                'oracle': ('oracle', [], {
                    'mode': 'pitch_wheel',
                    'm': 0x4000,
                    'format': ('midi', [0xe0, '%l', '%h']),
                }),
            },
            ['rhymel'],
            ['rhymel', 'oracle'],
            name=name,
        )
        _connect(
            [self.rhymel, self.lpf],
            self.oracle,
        )

    def connect_outputs(self, other):
        other.midi(midi.Msg.pitch_bend_range(64))
        Subsystem.connect_outputs(self, other)

class Voices(Subsystem):
    def init(self, name, spec, n=3, cents=0.1, vol=0.25, randomize_phase=None):
        Subsystem.init(
            self,
            dict(
                midi='midi',
                **{f'voice{i}': spec for i in range(n)},
                gain=('gain', [vol/n]),
                buf='buf',
            ),
            ['midi'],
            ['buf'],
            name=name,
        )
        _connect(
            self.components['midi'],
            [self.components[f'voice{i}'] for i in range(n)],
            [self.components['buf'],
                '<+', self.components['gain'],
            ],
        )
        if n == 1: return
        for i in range(n):
            synth = self.components[f'voice{i}']
            if randomize_phase: randomize_phase(synth)
            bend = 0x2000 + int(0x500 * cents * (2*i/(n-1) - 1))
            l = bend & 0x7f
            h = bend >> 7
            synth.midi([0xe1, l, h])
