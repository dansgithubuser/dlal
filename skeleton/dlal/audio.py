from ._component import Component

class Audio(Component):
    def __init__(self, name=None):
        Component.__init__(self, 'audio', name)
        self.components = []

    def samples_per_evaluation(self, samples_per_evaluation=None):
        args = ['samples_per_evaluation']
        if samples_per_evaluation != None:
            args.append([samples_per_evaluation])
        return int(self.command_immediate(*args))

    def sample_rate(self, sample_rate=None):
        args = ['sample_rate']
        if sample_rate != None:
            args.append([sample_rate])
        return float(self.command_immediate(*args))

    def add(self, component):
        result = self.command('add', component._view())
        self.components.append(component.name)
        return result

    def remove(self, component):
        result = self.command('remove', component._view())
        self.components.remove(component.name)
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
