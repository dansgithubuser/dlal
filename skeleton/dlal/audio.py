from ._component import Component

class Audio(Component):
    def __init__(self, name=None):
        Component.__init__(self, 'audio', name)
        self.components = []

    def add(self, component):
        result = self.command('add', *component._view())
        self.components.append(component.name)
        return result

    def start(self):
        return self.command_immediate('start')

    def stop(self):
        return self.command_immediate('stop')

    def get_cross_state(self):
        return self.components

    def set_cross_state(self, state):
        from ._skeleton import component
        for name in state: self.add(component(name))
