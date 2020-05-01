from ._component import Component

class Osc(Component):
    def __init__(self, wave=None, name=None):
        Component.__init__(self, 'osc', name)
        from ._skeleton import Immediate
        with Immediate():
            if wave != None: self.wave(wave)
