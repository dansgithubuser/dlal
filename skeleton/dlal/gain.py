from ._component import Component

class Gain(Component):
    def __init__(self, gain=None, **kwargs):
        Component.__init__(self, 'gain', **kwargs)
        from ._skeleton import Immediate
        with Immediate():
            if gain != None: self.set(gain)

    def __str__(self):
        return f'{self.name}({self.get():.2f})'
