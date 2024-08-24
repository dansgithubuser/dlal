from ._component import Component

class Gate(Component):
    def __init__(self, threshold=None, **kwargs):
        Component.__init__(self, 'gate', **kwargs)
        from ._skeleton import Immediate
        with Immediate():
            if threshold != None:
                self.threshold(threshold)
