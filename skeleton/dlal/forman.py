from ._component import Component

class Forman(Component):
    def __init__(self, freq_per_bin=None, **kwargs):
        Component.__init__(self, 'forman', **kwargs)
        from ._skeleton import Immediate
        with Immediate():
            if freq_per_bin!= None: self.freq_per_bin(freq_per_bin)
