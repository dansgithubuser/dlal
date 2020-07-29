from ._component import Component

import os

class _Default: pass

class Midi(Component):
    def __init__(self, port=_Default, **kwargs):
        Component.__init__(self, 'midi', **kwargs)
        if port == _Default:
            port = os.environ.get('DLAL_MIDI_INPUT')
        if port and any(i.startswith(port) for i in self.ports()):
            self.open(port)
