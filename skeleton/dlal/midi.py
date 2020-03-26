from ._component import Component

import os

class Midi(Component):
    def __init__(self, name=None):
        Component.__init__(self, 'midi', name)
        port = os.environ.get('DLAL_MIDI_INPUT')
        if port and any(i.startswith(port) for i in self.ports()):
            self.open(port)
