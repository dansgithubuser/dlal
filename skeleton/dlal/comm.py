from ._component import Component

class Comm(Component):
    def __init__(self, size=None, **kwargs):
        Component.__init__(self, 'comm', **kwargs)
        from ._skeleton import Immediate
        with Immediate():
            if size != None: self.resize(size)

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
