from ._component import Component

class Lfo(Component):
    def __init__(self, freq=None, amp=None, **kwargs):
        Component.__init__(self, 'lfo', **kwargs)
        if freq != None: self.freq(freq)
        if amp != None: self.amp(amp)
