from ._skeleton import connect as _connect

import glob
import json
import math
import os

class Subsystem:
    def __init__(self, name, components={}, inputs=[], outputs=[]):
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
    def __init__(self, name, order):
        components = {}
        for i in range(order):
            components[f'iirs[{i}]'] = 'iir'
            components[f'bufs[{i}]'] = 'buf'
        bufs = [f'bufs[{i}]' for i in range(order)]
        Subsystem.__init__(self, name, components, bufs, bufs)
        self.iirs = []
        self.bufs = []
        for i in range(order):
            self.iirs.append(self.components[f'iirs[{i}]'])
            self.bufs.append(self.components[f'bufs[{i}]'])
            self.iirs[-1].connect(self.bufs[-1])

class Phonetizer(IirBank):
    def __init__(self, name, phonetics_path='assets/phonetics', sample_rate=44100):
        Subsystem.__init__(self, name, {
            'tone_gain': ('gain', [0]),
            'tone_buf': 'buf',
            'noise_gain': ('gain', [0]),
            'noise_buf': 'buf',
        })
        IirBank.__init__(self, None, 5)
        _connect(
            (self.tone_gain, self.noise_gain),
            (self.tone_buf, self.noise_buf),
            self,
        )
        # inputs must be explicit
        self.inputs = None
        # phonetics
        self.phonetics = {}
        for path in glob.glob(os.path.join(phonetics_path, '*.phonetic.json')):
            phonetic = os.path.basename(path).split('.')[0]
            with open(path) as file:
                self.phonetics[phonetic] = json.loads(file.read())
        # sample rate
        self.sample_rate = sample_rate

    def say(self, phonetics, smooth=0):
        for iir, (freq, peak) in zip(self.iirs, self.phonetics[phonetic]['formants'].items()):
            w = freq / self.sample_rate * 2 * math.pi
            iir.single_pole_bandpass(w, 0.01, peak, smooth)
