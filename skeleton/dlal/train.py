from ._component import Component

class Train(Component):
    def __init__(self, impulse=None, **kwargs):
        Component.__init__(self, 'train', **kwargs)
        from ._skeleton import Immediate
        with Immediate():
            if impulse != None: self.impulse(impulse)
