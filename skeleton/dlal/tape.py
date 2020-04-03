from ._component import Component

class Tape(Component):
    def __init__(self, size=None, name=None):
        Component.__init__(self, 'tape', name)
        if size: self.command_immediate('resize', [size])

    def size(self):
        return int(self.command_immediate('size'))

    def clear(self):
        return self.command_immediate('clear')

    def read(self, size):
        return [float(i) for i in self.command_immediate('read', [size])]
