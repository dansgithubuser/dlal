from ._component import Component

class Hpf(Component):
    def __init__(self, highness=None, freq=None, sample_rate=44100, name=None):
        Component.__init__(self, 'hpf', name)
        if highness != None: self.command_immediate('set', [highness])
        if freq != None: self.command_immediate('freq', [freq, sample_rate])
