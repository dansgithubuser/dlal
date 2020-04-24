from ._component import Component

import os

class _Default: pass

class Midi(Component):
    def __init__(self, port=_Default, name=None):
        Component.__init__(self, 'midi', name)
        if port == _Default:
            port = os.environ.get('DLAL_MIDI_INPUT')
        if port and any(i.startswith(port) for i in self.ports()):
            self.open(port)
