from ._component import Component

class Noisebank(Component):
    def __init__(self, smooth=None, **kwargs):
        Component.__init__(self, 'noisebank', **kwargs)
        from ._skeleton import Immediate
        with Immediate():
            if smooth != None: self.smooth(smooth)
