from ._component import Component

class Audio(Component):
    def __init__(self, name=None):
        Component.__init__(self, 'audio', name)

    def add(self, component):
        return self.command('add', *component._view())
