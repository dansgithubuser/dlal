from ._component import Component

class Compressor(Component):
    def __init__(
        self,
        *,
        volume=None,
        gain_min=None,
        gain_max=None,
        gain_smooth_rise=None,
        gain_smooth_fall=None,
        peak_smooth_rise=None,
        peak_smooth_fall=None,
        **kwargs,
    ):
        Component.__init__(self, 'compressor', **kwargs)
        from ._skeleton import Immediate
        with Immediate():
            if volume: self.volume(volume)
            if gain_min: self.gain_min(gain_min)
            if gain_max: self.gain_max(gain_max)
            if gain_smooth_rise: self.gain_smooth_rise(gain_smooth_rise)
            if gain_smooth_fall: self.gain_smooth_fall(gain_smooth_fall)
            if peak_smooth_rise: self.peak_smooth_rise(peak_smooth_rise)
            if peak_smooth_fall: self.peak_smooth_fall(peak_smooth_fall)
