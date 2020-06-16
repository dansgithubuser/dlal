from ._component import Component

import struct
import threading
import weakref

class Tape(Component):
    def __init__(self, size=None, name=None):
        Component.__init__(self, 'tape', name)
        if size: self.command_immediate('resize', [size])

    def size(self):
        return int(self.command_immediate('size'))

    def clear(self):
        return self.command_immediate('clear')

    def read(self, size=None):
        args = []
        if size: args.append(size)
        return [float(i) for i in self.command_immediate('read', args)]

    def to_file_i16le(self, size, file):
        samples = self.read(size)
        for sample in samples:
            i = int(sample * 0x7fff)
            if i > 0x7fff: i = 0x7fff
            elif i < -0x8000: i = -0x8000
            file.write(struct.pack('<h', i))

    def to_file_i16le_start(self, size, file_path):
        tape = weakref.proxy(self)
        class File:
            def __init__(self, file_path):
                self.file = open(file_path, 'wb')
                self.quit = False
                weak_self = weakref.proxy(self)
                def main():
                    while not weak_self.quit:
                        tape.to_file_i16le(size, weak_self.file)
                self.thread = threading.Thread(target=main)
                self.thread.start()
            def stop(self):
                self.quit = True
                self.thread.join()
        self._file = File(file_path)

    def to_file_i16le_stop(self):
        self._file.stop()
