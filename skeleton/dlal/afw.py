from ._component import Component

class Afw(Component):
    def __init__(self, *, context_duration=None, **kwargs):
        def preadd():
            if context_duration: self.context_duration(context_duration)
        Component.__init__(self, 'afw', preadd=preadd, **kwargs)
