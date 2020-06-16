from ._skeleton import connect as _connect

class Subsystem:
    def __init__(self, name, components, inputs=[], outputs=[]):
        self.name = name
        self.components = {}
        for name, (kind, args, kwargs) in components.items():
            self.add(name, kind, args, kwargs)
        self.inputs = [self.components[i] for i in inputs]
        self.outputs = [self.components[i] for i in outputs]

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

class FrequencyResponseAnalyzer(Subsystem):
    def __init__(self, name='fr', duration=10, sample_rate=44100, smoothness=200):
        self.duration = duration
        self.smoothness = smoothness
        Subsystem.__init__(self, name, {
            'audio': ('audio', [], {}),
            'osc': ('osc', [], {}),
            'buf': ('buf', [], {}),
            'control': ('peak', [], {}),
            'peak': ('peak', [], {}),
        })
        self.audio.sample_rate(sample_rate)
        self.osc.connect(self.buf)
        self.buf.connect(self.control)
        self.audio.add(self.osc)
        self.audio.add(self.buf)
        self.audio.add(self.control)

    def run(self, other):
        # setup
        for i in other.components.values():
            self.audio.add(i)
        self.audio.add(self.peak)
        for i in other.inputs:
            self.buf.connect(i)
        for i in other.outputs:
            i.connect(self.peak)
        # run
        fr = []
        i = 0
        samples = self.duration * self.audio.sample_rate()
        while i < samples:
            self.osc.freq(20000 ** (i / samples))
            self.audio.run()
            fr.append((
                self.osc.freq(),
                self.peak.value() / self.control.value(),
            ))
            i += self.audio.samples_per_evaluation()
        # teardown
        for i in other.components.values():
            self.audio.remove(i)
        self.audio.remove(self.peak)
        for i in other.inputs:
            self.buf.disconnect(i)
        for i in other.outputs:
            i.disconnect(self.peak)
        # smoothing
        smoothed = []
        for i in range(self.smoothness, len(fr)-self.smoothness):
            s = 0.0
            for j in range(-self.smoothness, self.smoothness+1):
                s += fr[i+j][1]
            s /= (2 * self.smoothness + 1)
            smoothed.append((fr[i+self.smoothness][0], s))
        return smoothed

class Bpf(Subsystem):
    def __init__(self, order=1, name='bpf'):
        components = {}
        for i in range(1, order+1):
            components[f'lpf{i}'] = ('lpf', [], {})
            components[f'hpf{i}'] = ('hpf', [], {})
        Subsystem.__init__(self, name,
            components, components.keys(), components.keys())

    def freq(self, freq, sample_rate=None):
        args = [freq]
        if sample_rate: args.append(sample_rate)
        for i in self.components.values():
            i.freq(*args)
