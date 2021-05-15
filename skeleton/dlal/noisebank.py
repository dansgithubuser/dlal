from ._component import Component

class Noisebank(Component):
    def __init__(self, smooth=0, **kwargs):
        Component.__init__(self, 'noisebank', **kwargs)
        from ._skeleton import Immediate
        with Immediate():
            if smooth != None: self.smooth(smooth)
