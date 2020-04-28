from ._component import Component

class Hpf(Component):
    def __init__(self, highness=None, name=None):
        Component.__init__(self, 'hpf', name)
        if highness != None: self.command_immediate('set', [highness])
