from ._component import Component

class Mul(Component):
    def __init__(self, c=None, **kwargs):
        Component.__init__(self, 'mul', **kwargs)
        from ._skeleton import Immediate
        with Immediate():
            if c != None: self.c(c)
