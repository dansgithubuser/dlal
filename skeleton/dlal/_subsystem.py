from . import _skeleton
from ._skeleton import connect as _connect
from . import _speech
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
        self.post_add_init()

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

    def post_add_init(self): pass

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
            self.iirs[-1].command_immediate('gain', [0])

class SpeechSampler(Subsystem):
    def init(
        self,
        stft_bins=512,
        tone_bins=[1, 6],
        tone_factor=1e1,
        noise_bins=[32, 256],
        noise_factor=2e2,
        name=None,
    ):
        self.stft_bins = stft_bins
        self.tone_bins = tone_bins
        self.tone_factor = tone_factor
        self.noise_bins = noise_bins
        self.noise_factor = noise_factor
        Subsystem.init(self,
            {
                'buf': 'buf',
                'stft': ('stft', [self.stft_bins]),
            },
            ['buf'],
            name=name,
        )
        _connect(
            self.buf,
            self.stft,
        )

    def sample(self):
        spectrum = self.stft.spectrum()
        return (
            spectrum,
            self.tone_factor * math.sqrt(sum(i ** 2 for i in spectrum[self.tone_bins[0]:self.tone_bins[1]])),
            self.noise_factor * math.sqrt(sum(i ** 2 for i in spectrum[self.noise_bins[0]:self.noise_bins[1]])),
        )

    def sampleses(self, path, filea, driver):
        sampleses = []
        for phonetic in _speech.PHONETICS:
            print(phonetic)
            filea.open(os.path.join(path, f'{phonetic}.flac'))
            sampleses.append([])
            while filea.playing():
                driver.run()
                sampleses[-1].append(self.sample())
        return sampleses

class SpeechSynth(Subsystem):
    def init(self, name=None):
        freq_per_bin = 44100 / (8 * 64)
        Subsystem.init(self,
            {
                'comm': ('comm', [1 << 12]),
                'forman': ('forman', [freq_per_bin]),
                'tone': ('sinbank', [freq_per_bin, 0.99]),
                'noise': ('noisebank', [0.9]),
                'buf_tone_1': 'buf',
                'peak': ('peak', [0.99]),
                'mul': 'mul',
                'buf_peak': 'buf',
                'buf_tone_o': 'buf',
                'buf_noise_o': 'buf',
            },
            name=name,
        )
        self.tone.zero()
        _connect(
            (self.forman,),
            (self.tone, self.noise),
            (self.buf_tone_1, self.buf_noise_o),
            (self.buf_tone_o,),
            [],
            self.buf_tone_1,
            self.peak,
            self.buf_peak,
            [],
            self.mul,
            [self.buf_peak, self.buf_noise_o],
            [],
            self.buf_tone_o,
        )
        self.outputs = [self.buf_tone_o, self.buf_noise_o]

    def post_add_init(self):
        self.tone.midi([0x90, 42, 127])

    def synthesize(
        self,
        toniness=None,
        tone_spectrum=None,
        tone_formants=None,
        noise_spectrum=None,
        wait=None,
    ):
        with _skeleton.Detach():
            with self.comm:
                if toniness != None:
                    tonal_airflow = min(toniness * 4, 1)
                    # c = 0 => noise is 100% modulated by tone
                    # c = 1 => noise in   0% modulated by tone
                    self.mul.c(1 - tonal_airflow)
                if tone_spectrum:
                    self.tone.spectrum(tone_spectrum)
                elif tone_formants:
                    self.forman.formants(tone_formants)
                if noise_spectrum:
                    self.noise.spectrum(noise_spectrum)
            self.comm.wait(wait)

class Portamento(Subsystem):
    def init(self, slowness=0.999, name=None):
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

class Vibrato(Subsystem):
    def init(self, freq=3.5, amp=0.15, name=None):
        Subsystem.init(self,
            {
                'lfo': ('lfo', [freq, amp]),
                'oracle': ('oracle', [], {
                    'mode': 'pitch_wheel',
                    'm': 0x1fff,
                    'b': 0x2000,
                    'format': ('midi', [0xe0, '%l', '%h']),
                }),
            },
            [],
            ['oracle'],
            name=name,
        )
        _connect(self.lfo, self.oracle)

class Voices(Subsystem):
    def init(self, spec, n=3, cents=0.1, vol=0.25, randomize_phase=None, name=None):
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
