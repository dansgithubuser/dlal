from ._component import Component

class Stft(Component):
    def __init__(self, window_size=None, **kwargs):
        Component.__init__(self, 'stft', **kwargs)
        from ._skeleton import Immediate
        with Immediate():
            if window_size != None: self.window_size(window_size)
