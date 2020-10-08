from ._component import Component

class Comm(Component):
    def __init__(self, **kwargs):
        Component.__init__(self, 'comm', **kwargs)

    def queue(self, component, name, args, kwargs, timeout_ms=20, detach=False):
        return self.command_immediate(
            'queue',
            [
                *component._view(),
                {
                    'name': name,
                    'args': args,
                    'kwargs': kwargs,
                },
                timeout_ms,
                detach,
            ],
        )

    def wait(self, samples):
        return self.command_immediate('wait', [samples])
