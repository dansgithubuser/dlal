from ._component import Component

class Lpf(Component):
    def __init__(self, lowness=None, name=None):
        Component.__init__(self, 'lpf', name)
        if lowness != None: self.command_immediate('set', [lowness])
