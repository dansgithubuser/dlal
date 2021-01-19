from ._component import Component

class Digitar(Component):
    def __init__(self, lowness=None, feedback=None, **kwargs):
        Component.__init__(self, 'digitar', **kwargs)
        if lowness != None: self.lowness(lowness)
        if feedback != None: self.feedback(feedback)
