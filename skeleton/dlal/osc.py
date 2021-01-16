from ._component import Component

class Osc(Component):
    def __init__(self, wave=None, freq=None, bend=None, stay_on=None, **kwargs):
        Component.__init__(self, 'osc', **kwargs)
        from ._skeleton import Immediate
        with Immediate():
            if wave != None: self.wave(wave)
            if freq != None: self.freq(freq)
            if bend != None: self.bend(bend)
            if stay_on != None: self.stay_on(stay_on)
