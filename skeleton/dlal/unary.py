from ._component import Component

class Unary(Component):
    def __init__(self, mode=None, name=None):
        Component.__init__(self, 'unary', name)
        from ._skeleton import Immediate
        with Immediate():
            if mode != None: self.mode(mode)
