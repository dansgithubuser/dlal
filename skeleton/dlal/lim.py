from ._component import Component

class Lim(Component):
    def __init__(self, hard=None, soft=None, soft_gain=None, name=None):
        Component.__init__(self, 'lim', name)
        if hard != None: self.command_immediate('hard', [hard])
        if soft != None: self.command_immediate('soft', [soft])
        if soft_gain != None: self.command_immediate('soft_gain', [soft_gain])
