from ._component import Component

import struct

class Tape(Component):
    def __init__(self, size=None, name=None):
        Component.__init__(self, 'tape', name)
        if size: self.command_immediate('resize', [size])

    def size(self):
        return int(self.command_immediate('size'))

    def clear(self):
        return self.command_immediate('clear')

    def read(self, size):
        return [float(i) for i in self.command_immediate('read', [size])]

    def to_file_i16le(self, size, file):
        samples = self.read(size)
        for sample in samples:
            i = int(sample * 0x7fff)
            if i > 0x7fff: i = 0x7fff
            elif i < -0x8000: i = -0x8000
            file.write(struct.pack('<h', i))
