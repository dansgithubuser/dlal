from ._component import Component

class Gain(Component):
    def __init__(self, gain=None, name=None):
        Component.__init__(self, 'gain', name)
        from ._skeleton import Immediate
        with Immediate():
            if gain != None: self.set(gain)
