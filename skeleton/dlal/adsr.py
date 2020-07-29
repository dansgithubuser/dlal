from ._component import Component

class Adsr(Component):
    def __init__(self, a=None, d=None, s=None, r=None, **kwargs):
        Component.__init__(self, 'adsr', **kwargs)
        if a != None: self.command_immediate('a', [a])
        if d != None: self.command_immediate('d', [d])
        if s != None: self.command_immediate('s', [s])
        if r != None: self.command_immediate('r', [r])
