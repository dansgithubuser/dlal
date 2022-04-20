from ._component import Component

class _Pauser():
    def __init__(self, comm):
        self.comm = comm

    def __enter__(self):
        if not self.comm.paused:
            x = self.comm.pause(True)
        self.comm.paused += 1

    def __exit__(self, *args):
        self.comm.paused -= 1
        if not self.comm.paused:
            x = self.comm.pause(False)

class Comm(Component):
    def __init__(self, size=None, **kwargs):
        Component.__init__(self, 'comm', **kwargs)
        from ._skeleton import Immediate
        with Immediate():
            if size != None: self.resize(size)
        self.paused = 0

    def __enter__(self):
        self.component_comm = Component._comm
        Component._comm = self

    def __exit__(self, *args):
        Component._comm = self.component_comm

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

    def pauser(self):
        return _Pauser(self)
