from ._component import Component

class Peak(Component):
    def __init__(self, decay=None, **kwargs):
        Component.__init__(self, 'peak', **kwargs)
        from ._skeleton import Immediate
        with Immediate():
            if decay != None: self.decay(decay)
