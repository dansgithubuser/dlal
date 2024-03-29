from ._component import Component

class Audio(Component):
    def __init__(self, *, driver=False, run_size=None, mic=False, **kwargs):
        from ._skeleton import driver_set
        Component.__init__(self, 'audio', **kwargs)
        self.components = []
        self.slots = {}
        self.with_components = None
        if driver: driver_set(self)
        if run_size: self.run_size(run_size)
        if mic: self.add(self)

    def __enter__(self):
        from ._skeleton import driver_set
        assert self.with_components == None
        self.old_driver = driver_set(self)
        self.with_components = []

    def __exit__(self, *args):
        from ._skeleton import driver_set
        driver_set(self.old_driver)
        for i in self.with_components:
            self.remove(i)
        self.with_components = None

    def run_size(self, run_size=None):
        args = ['run_size']
        if run_size != None:
            args.append([run_size])
        return int(self.command_immediate(*args))

    def sample_rate(self, sample_rate=None):
        args = ['sample_rate']
        if sample_rate != None:
            args.append([sample_rate])
        return float(self.command_immediate(*args))

    def add(self, component, slot=0):
        from ._subsystem import Subsystem
        if isinstance(component, Subsystem):
            return component.add_to(self)
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
