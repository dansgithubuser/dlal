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
