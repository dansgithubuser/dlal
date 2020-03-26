from ._component import Component

class Comm(Component):
    def __init__(self, name=None):
        Component.__init__(self, 'comm', name)

    def queue(self, component, name, *args, **kwargs):
        self.command('queue', *component._view(), {
            'name': name,
            'args': args,
            'kwargs': kwargs,
        }, '20')
