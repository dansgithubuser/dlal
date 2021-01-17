from ._component import Component

class Mgain(Component):
    def __init__(self, gain=None, **kwargs):
        Component.__init__(self, 'mgain', **kwargs)
        if gain != None: self.gain(gain)
