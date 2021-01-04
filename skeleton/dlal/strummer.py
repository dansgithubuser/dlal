from ._component import Component

class Strummer(Component):
    def __init__(self, name=None):
        Component.__init__(self, 'strummer', name)

    def pattern(self, pattern):
        self.command('pattern', [list(pattern.replace(' ', ''))])
