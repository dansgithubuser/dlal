from ._component import Component

class Delay(Component):
    def __init__(
        self,
        size=None,
        gain_x=None,
        gain_y=None,
        gain_o=None,
        **kwargs,
    ):
        Component.__init__(self, 'delay', **kwargs)
        from ._skeleton import Immediate
        with Immediate():
            if size != None: self.resize(size)
            if gain_x != None: self.gain_x(gain_x)
            if gain_y != None: self.gain_y(gain_y)
            if gain_o != None: self.gain_o(gain_o)
