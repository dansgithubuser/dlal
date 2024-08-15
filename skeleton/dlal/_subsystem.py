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
        self.post_add_init()

    def __del__(self):
        for i in self.components.values():
            i.__del__()

    def init(self, components={}, inputs=[], outputs=[], name=None):
        if not hasattr(self, 'name'):
            if name == None: name = _utils.upper_camel_to_snake_case(self.__class__.__name__)
            self.name = name
            self.components = {}
            self.inputs = []
            self.outputs = []
        for name, spec in components.items():
            self.add_spec(name, spec)
        self.inputs.extend(self.components[i] for i in inputs)
        self.outputs.extend(self.components[i] for i in outputs)

    def post_add_init(self): pass

    def __str__(self):
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
        return component

    def add_spec(self, name, spec):
        args = []
        kwargs = {}
        if type(spec) == str:
            kind = spec
        elif type(spec) == tuple:
            if len(spec) >= 1:
                kind = spec[0]
                assert type(kind) == str
            if len(spec) >= 2:
                args = spec[1]
                assert type(args) == list
            if len(spec) >= 3:
                kwargs = spec[2]
                assert type(kwargs) == dict
        return self.add(name, kind, args, kwargs)

    def add_to(self, driver):
        for i in self.components.values():
            driver.add(i)

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

class Portamento(Subsystem):
    def init(self, slowness=0.999, name=None):
        Subsystem.init(self,
            {
                'rhymel': 'rhymel',
                'lpf': ('lpf', [slowness]),
                'oracle': ('oracle', [], {
                    'mode': 'pitch_wheel',
                    'm': 0x4000,
                    'format': ('midi', [[0xe0, '%l', '%h']]),
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
        self.prepped = False

    def __del__(self):
        super().__del__()
        if not self.prepped:
            print(f'note: {self} was never prepped')

    def prep_output(self, output):
        output.midi(midi.Msg.pitch_bend_range(64))
        self.prepped = True

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
    def init(
        self,
        spec,
        n=3,
        cents=0.1,
        vol=0.25,
        per_voice_init=None,
        effects={},
        name=None,
    ):
        Subsystem.init(
            self,
            dict(
                midi='midi',
                **{f'voice{i}': spec for i in range(n)},
                gain=('gain', [vol/n]),
                **effects,
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
        for effect in effects.keys():
            self.components[effect].connect(self.buf)
        for i in range(n):
            voice = self.components[f'voice{i}']
            if per_voice_init: per_voice_init(voice, i)
            if n > 1:
                bend = 0x2000 + int(0x500 * cents * (2*i/(n-1) - 1))
                l = bend & 0x7f
                h = bend >> 7
                voice.midi([0xe1, l, h])

class Mixer(Subsystem):
    class Channel:
        def __init__(self, gain, pan, pan_spec, lim, buf):
            self.gain = gain
            self.pan = pan
            self.pan_spec = pan_spec
            self.lim = lim
            self.buf = buf
            _connect(
                [self.gain, self.pan, self.lim],
                self.buf,
            )

        def components(self):
            return [
                self.gain,
                self.pan,
                self.lim,
                self.buf,
            ]

    def init(
        self,
        pre_mix_spec,
        *,
        post_mix_extra={},
        reverb=0,
        lim=[1, 0.99, 0.01],
        sample_rate=None,
        name='mixer',
    ):
        self.name = name
        self.components = {}
        self.channels = []
        for i, v in enumerate(pre_mix_spec):
            ch_gain = self.add(f'ch{i}.gain', 'gain', [v.get('gain', 1)])
            ch_pan = self.add(f'ch{i}.pan', 'pan')
            ch_lim = self.add(f'ch{i}.lim', 'lim', v.get('lim', [1, 0.9, 0.1]))
            ch_buf = self.add(f'ch{i}.buf', 'buf')
            channel = Mixer.Channel(
                ch_gain,
                ch_pan,
                (v.get('pan', [0, 1]), {'sample_rate': sample_rate}),
                ch_lim,
                ch_buf,
            )
            self.channels.append(channel)
        self.post_mix = []
        for name, spec in post_mix_extra.items():
            self.post_mix.append(self.add_spec(name, spec))
        self.post_mix.append(self.add('reverb', args=[reverb]))
        self.post_mix.append(self.add('lim', args=lim))
        self.post_mix.append(self.add('buf'))
        for channel in self.channels:
            channel.buf.connect(self.buf)
        _connect(
            [self.reverb, self.lim],
            self.buf,
        )
        self.inputs = tuple(i.buf for i in self.channels)
        self.outputs = [self.buf]

    def post_add_init(self):
        for channel in self.channels:
            channel.pan.set(*channel.pan_spec[0], **channel.pan_spec[1])

    def __getitem__(self, i):
        return self.channels[i].buf

    def print_details(self):
        for i, ch in enumerate(self.channels):
            print(ch.gain, ch.pan, ch.lim)
        for i in self.post_mix[:-1]:
            print(i)
