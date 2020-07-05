from ._component import Component

class Comm(Component):
    def __init__(self, name=None):
        Component.__init__(self, 'comm', name)

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
                str(timeout_ms),
                detach,
            ],
            do_json_prep=False,
        )
