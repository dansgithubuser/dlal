from ._skeleton import connect as _connect, driver_set as _driver_set, UseComm as _UseComm

import glob
import json
import math
import os
import re

class Subsystem:
    def __init__(self, *args, **kwargs):
        driver = _driver_set(None)
        self.init(*args, **kwargs)
        if driver:
            self.add_to(driver)
            _driver_set(driver)

    def init(self, name, components={}, inputs=[], outputs=[]):
        if name:
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
        from ._skeleton import component_class
        if kind == None:
            kind = name
        component = component_class(kind)(
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
        for i in self.inputs:
            other.connect(i)

    def connect_outputs(self, other):
        for i in self.outputs:
            i.connect(other)

    def disconnect_inputs(self, other):
        for i in self.inputs:
            other.disconnect(i)

    def disconnect_outputs(self, other):
        for i in self.outputs:
            i.disconnect(other)

class IirBank(Subsystem):
    def init(self, name, order):
        components = {}
        for i in range(order):
            components[f'iirs[{i}]'] = 'iir'
            components[f'bufs[{i}]'] = 'buf'
        bufs = [f'bufs[{i}]' for i in range(order)]
        Subsystem.init(self, name, components, bufs, bufs)
        self.iirs = []
        self.bufs = []
        for i in range(order):
            self.iirs.append(self.components[f'iirs[{i}]'])
            self.bufs.append(self.components[f'bufs[{i}]'])
            self.iirs[-1].connect(self.bufs[-1])

class Phonetizer(IirBank):
    def init(
        self,
        name,
        tone_pregain=1,
        noise_pregain=1,
        phonetics_path='assets/phonetics',
        sample_rate=44100,
        continuant_wait=44100//8,
    ):
        Subsystem.init(self, name, {
            'comm': 'comm',
            'tone_gain': ('gain', [0]),
            'tone_buf': 'buf',
            'noise_gain': ('gain', [0]),
            'noise_buf': 'buf',
        })
        IirBank.init(self, None, 5)
        _connect(
            (self.tone_gain, self.noise_gain),
            (self.tone_buf, self.noise_buf),
            self,
        )
        # inputs must be explicit
        self.inputs = None
        # pregains
        self.tone_pregain = tone_pregain
        self.noise_pregain = noise_pregain
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

    def say(self, phonetic_name, continuant_wait=None, smooth=None, speed=1):
        phonetic = self.phonetics[phonetic_name]
        if continuant_wait == None:
            continuant_wait = self.continuant_wait
        if smooth == None:
            if speed > 1:
                smooth = 0.5
            elif any([
                self.phonetic_name == '0',  # starting from silence
                phonetic['type'] == 'stop',  # moving to stop
                self.phonetics[self.phonetic_name]['type'] == 'stop',  # moving from stop
            ]):
                smooth = 0.7
            else:  # moving between continuants
                smooth = 0.9
        wait = int(phonetic.get('duration', continuant_wait) / len(phonetic['frames']) / speed)
        with _UseComm(self.comm):
            for frame in phonetic['frames']:
                self.tone_gain.command_detach('set', [frame['tone_amp'] * self.tone_pregain, smooth])
                self.noise_gain.command_detach('set', [frame['noise_amp'] * self.noise_pregain, smooth])
                for iir, formant in zip(self.iirs, frame['formants']):
                    w = formant['freq'] / self.sample_rate * 2 * math.pi
                    iir.command_detach('single_pole_bandpass', [w, 0.01, formant['amp'], smooth])
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
