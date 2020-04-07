from ._component import Component
from ._utils import ASSETS_DIR

import glob
import os

class Buf(Component):
    def __init__(self, name=None):
        Component.__init__(self, 'buf', name)

    def load(self, file_path, note):
        return self.command_immediate('load', [file_path, note])

    def load_all(self):
        pattern = os.path.join(ASSETS_DIR, 'sounds', '*', '*.wav')
        for i, file_path in enumerate(glob.glob(pattern)):
            self.load(file_path, i)
