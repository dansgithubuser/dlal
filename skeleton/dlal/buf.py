from ._component import Component
from ._utils import ASSETS_DIR

import glob
import os

midi_drums = {
    #27: 'high-q.wav',
    #28: 'slap.wav',
    #29: 'scratch-push.wav',
    #30: 'scratch-pull.wav',
    #31: 'sticks.wav',
    #32: 'square-click.wav',
    #33: 'metronome-click.wav',
    #34: 'metronome-bell.wav',
    35: 'bass.wav',
    36: 'bass.wav',
    37: 'side-stick.wav',
    38: 'snare.wav',
    39: 'clap.wav',
    40: 'snare.wav',
    41: 'floor-tom.wav',
    42: 'hat.wav',
    43: 'floor-tom.wav',
    #44: 'pedal-hat.wav',
    45: 'low-tom.wav',
    #46: 'open-hat.wav',
    47: 'mid-tom.wav',
    48: 'mid-tom.wav',
    49: 'crash.wav',
    50: 'high-tom.wav',
    51: 'ride.wav',
    #52: 'chinese-cymbal.wav',
    53: 'ride-bell.wav',
    #54: 'tambourine.wav',
    #55: 'splash-cymbal.wav',
    56: 'cowbell.wav',
    57: 'crash.wav',
    #58: 'Vibra Slap',
    59: 'ride.wav',
    60: 'bongo-hi.wav',
    61: 'bongo-lo.wav',
    #62: 'Mute High Conga',
    #63: 'Open High Conga',
    #64: 'Low Conga',
    #65: 'High Timbale',
    #66: 'Low Timbale',
    #67: 'High Agogo',
    #68: 'Low Agogo',
    #69: 'Cabasa',
    #70: 'Maracas',
    #71: 'Short Whistle',
    #72: 'Long Whistle',
    #73: 'Short Guiro',
    74: 'guiro.wav',
    #75: 'Claves',
    #76: 'High Wood Block',
    #77: 'Low Wood Block',
    78: 'cuica.wav',
    79: 'cuica-open.wav',
    #80: 'Mute Triangle',
    #81: 'Open Triangle',
    82: 'shaker1.wav',
    #83: 'Jingle Bell',
    #84: 'Belltree',
    #85: 'Castanets',
    #86: 'Mute Surdo',
    #87: 'Open Surdo',
}

class Buf(Component):
    class Drum:
        bass = 35
        bass_1 = 36
        side_stick = 37
        snare = 38
        clap = 39
        electric_snare = 40
        low_floor_tom = 41
        closed_hat = 42
        high_floor_tom = 43
        low_tom = 45
        low_mid_tom = 47
        high_mid_tom = 48
        crash = 49
        high_tom = 50
        ride = 51
        ride_bell = 53
        cowbell = 56
        crash_2 = 57
        ride_2 = 59
        high_bongo = 60
        low_bongo = 61
        long_guiro = 74
        mute_cuica = 78
        open_cuica = 79
        shaker = 82

    def __init__(self, instrument=None, **kwargs):
        Component.__init__(self, 'buf', **kwargs)
        if instrument:
            self.load_pitched(instrument)

    def load(self, file_path, note):
        return self.command_immediate('load', [file_path, note])

    def load_asset(self, asset_path, note):
        return self.load(os.path.join(ASSETS_DIR, 'sounds', asset_path), note)

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

    def load_drums(self):
        for note, file_path in midi_drums.items():
            self.load(os.path.join(ASSETS_DIR, 'sounds', 'drum', file_path), note)

    def plot(self, note):
        samples = self.to_json()['_extra']['sounds'][str(note)]['samples']
        import dansplotcore as dpc
        dpc.plot(samples)
