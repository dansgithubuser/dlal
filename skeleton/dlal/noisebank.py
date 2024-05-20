from ._component import Component

class Noisebank(Component):
    def __init__(self, *, mode='linear', n_bins=64, bin_centers=None, smooth=None, **kwargs):
        def preadd():
            self.configure_bins(mode=mode, n_bins=n_bins, bin_centers=bin_centers)
        Component.__init__(self, 'noisebank', preadd=preadd, **kwargs)
        from ._skeleton import Immediate
        with Immediate():
            if smooth != None: self.smooth(smooth)
