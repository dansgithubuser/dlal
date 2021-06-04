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
            self.iirs[-1].command_immediate('gain', [0])

class SpeechSynth(Subsystem):
    def init(self, sample_rate=44100, name=None):
        self.sample_rate = sample_rate
        Subsystem.init(self,
            {
                'comm': ('comm', [1 << 12]),
                'tone': 'train',
                'tone_gain': ('gain', [100]),
                'tone_buf': 'buf',
                'tone_filter': (IirBank, [4]),
                'noise': 'noisebank',
                'mul': ('mul', [1]),
                'buf_tone': 'buf',
                'buf_noise': 'buf',
            },
            name=name,
        )
        _connect(
            self.tone,
            [self.tone_buf, '<+', self.tone_gain],
            self.tone_filter,
            self.buf_tone,
            [],
            self.noise,
            self.buf_noise,
            [],
            self.mul,
            [self.buf_tone, self.buf_noise],
        )
        self.outputs = [self.buf_tone, self.buf_noise]

    def synthesize(self, info, frame_i, wait, smooth, warp_formants):
        frame = info['frames'][frame_i]
        with _skeleton.Detach():
            with self.comm:
                if info['voiced']:
                    for i, formant in enumerate(frame['formants']):
                        if warp_formants:
                            self.tone_filter.iirs[i].pole_pairs_bandpass(
                                formant['freq'][0] / self.sample_rate * 2 * math.pi,
                                0.01,
                                0,
                                0,
                                2,
                            )
                        self.tone_filter.iirs[i].pole_pairs_bandpass(
                            formant['freq'][0] / self.sample_rate * 2 * math.pi,
                            0.01,
                            formant['amp'][0],
                            smooth,
                            2,
                        )
                else:
                    for iir in self.tone_filter.iirs:
                        iir.gain(0, smooth)
                spectrum = []
                c = 64 / (self.sample_rate / 2)
                lo = frame['noise']['freq_lo'][0] * c
                peak = frame['noise']['freq_peak'][0] * c
                amp_peak = frame['noise']['amp_peak'][0]
                hi = frame['noise']['freq_hi'][0] * c
                for i in range(64):
                    if i < lo or i > hi:
                        spectrum.append(0)
                    elif i < peak:
                        spectrum.append(amp_peak * (i - lo) / (peak - lo))
                    else:
                        spectrum.append(amp_peak * (1 - (i - peak) / (hi - peak)))
                self.noise.spectrum(spectrum, smooth)
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
