from .component import Component

import ctypes

class Audio(Component):
    def __init__(self, name=None):
        Component.__init__(self, 'audio', name)

    def add(self, component):
        self.command('add', str(component._raw),
            str(ctypes.cast(component._lib.command , ctypes.c_void_p).value),
            str(ctypes.cast(component._lib.evaluate, ctypes.c_void_p).value),
        )
