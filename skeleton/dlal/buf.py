from ._component import Component
from ._utils import ASSETS_DIR

import glob
import os

class Buf(Component):
    def __init__(self, instrument=None, **kwargs):
        Component.__init__(self, 'buf', **kwargs)
        if instrument:
            self.load_pitched(instrument)

    def load(self, file_path, note):
        return self.command_immediate('load', [file_path, note])

    def load_all(self):
        pattern = os.path.join(ASSETS_DIR, 'sounds', '*', '*.wav')
        for i, file_path in enumerate(glob.glob(pattern)):
            self.load(file_path, i)

    def load_pitched(self, instrument='?'):
        pitched_path = os.path.join(ASSETS_DIR, 'sounds', 'pitched')
        if instrument == '?':
            return os.listdir(pitched_path)
        path = os.path.join(pitched_path, instrument)
        for i in os.listdir(path):
            self.load(os.path.join(path, i), int(i.split('.')[0]))

    def plot(self, note):
        samples = self.to_json()['_extra']['sounds'][str(note)]['samples']
        import dansplotcore as dpc
        dpc.plot(samples)
