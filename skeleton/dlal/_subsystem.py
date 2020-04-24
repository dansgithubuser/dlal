from ._skeleton import connect as _connect

class Subsystem:
    def __init__(self, name, components, inputs=[], outputs=[]):
        from ._skeleton import component_class
        self.name = name
        self.components = {}
        for name, (kind, args, kwargs) in components.items():
            kwargs['name'] = self.name + kwargs.get('name', name)
            component = component_class(kind)(*args, **kwargs)
            self.components[name] = component
            setattr(self, name, component)
        self.inputs = [self.components[i] for i in inputs]
        self.outputs = [self.components[i] for i in outputs]

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
