from ._component import Component

class Reverb(Component):
    def __init__(self, amount=None, name=None):
        Component.__init__(self, 'reverb', name)
        if amount!= None: self.command_immediate('set', [amount])
