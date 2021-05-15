from ._component import Component

class Sinbank(Component):
    def __init__(self, bin_size=None, smooth=0, **kwargs):
        Component.__init__(self, 'sinbank', **kwargs)
        from ._skeleton import Immediate
        with Immediate():
            if bin_size != None: self.bin_size(bin_size)
            if smooth != None: self.smooth(smooth)
