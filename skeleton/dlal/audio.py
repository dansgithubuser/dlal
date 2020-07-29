from ._component import Component
from ._skeleton import driver_set

class Audio(Component):
    def __init__(self, **kwargs):
        Component.__init__(self, 'audio', **kwargs)
        self.components = []
        self.slots = {}
        self.with_components = None

    def __enter__(self):
        assert self.with_components == None
        self.old_driver = driver_set(self)
        self.with_components = []

    def __exit__(self, *args):
        driver_set(self.old_driver)
        for i in self.with_components:
            self.remove(i)
        self.with_components = None

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

    def add(self, component, slot=0):
        result = self.command('add', component._view()+[slot])
        self.components.append(component.name)
        self.slots[component.name] = slot
        if self.with_components != None:
            self.with_components.append(component)
        return result

    def remove(self, component):
        result = self.command('remove', component._view())
        self.components.remove(component.name)
        del self.slots[component.name]
        return result

    def start(self):
        return self.command_immediate('start')

    def stop(self):
        return self.command_immediate('stop')

    def get_cross_state(self):
        return {
            'components': self.components,
            'slots': self.slots,
        }

    def set_cross_state(self, state):
        from ._skeleton import component
        for name in state['components']:
            self.add(component(name), state['slots'][name])
