from ._component import Component

class Lpf(Component):
    def __init__(self, lowness=None, freq=None, sample_rate=44100, name=None):
        Component.__init__(self, 'lpf', name)
        if lowness != None: self.command_immediate('set', [lowness])
        if freq != None: self.command_immediate('freq', [freq, sample_rate])
