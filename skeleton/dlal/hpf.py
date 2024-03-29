from ._component import Component

class Hpf(Component):
    def __init__(self, highness=None, freq=None, sample_rate=44100, **kwargs):
        Component.__init__(self, 'hpf', **kwargs)
        if highness != None: self.command_immediate('set', [highness])
        if freq != None: self.command_immediate('freq', [freq, sample_rate])
