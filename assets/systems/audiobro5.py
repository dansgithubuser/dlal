import dlal

import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--start', '-s', type=float)
parser.add_argument('--run-size', type=int)
args = parser.parse_args()

class Piano(dlal.subsystem.Subsystem):
    def init(self, name=None):
        dlal.subsystem.Subsystem.init(
            self,
            {
                'sonic': 'sonic',
                'lim': ('lim', [0.5, 0.25, 0.3]),
                'buf': 'buf',
            },
            ['sonic'],
            ['buf'],
            name=name,
        )
        dlal.connect(
            self.sonic,
            [self.buf, '<+', self.lim],
        )
        self.sonic.from_json({
            "0": {
                "a": 4e-3, "d": 2e-4, "s": 0.5, "r": 2e-4, "m": 1,
                "i0": 0, "i1": 0.06, "i2": 0.02, "i3": 0, "o": 0.5,
            },
            "1": {
                "a": 0.025, "d": 6e-5, "s": 0.2, "r": 3e-5, "m": 1,
                "i0": 0, "i1": 0, "i2": 0, "i3": 0, "o": 0,
            },
            "2": {
                "a": 0.025, "d": 0.01, "s": 1.0, "r": 0.01, "m": 4,
                "i0": 0, "i1": 0, "i2": 0, "i3": 0, "o": 0,
            },
            "3": {
                "a": 0, "d": 0, "s": 0, "r": 0, "m": 0,
                "i0": 0, "i1": 0, "i2": 0, "i3": 0, "o": 0,
            },
        })

class Drums(dlal.subsystem.Subsystem):
    def init(self, name=None):
        dlal.subsystem.Subsystem.init(
            self,
            {
                'drums': 'buf',
                'lim': ('lim', [1.0, 0.8, 0.2]),
                'buf': 'buf',
            },
            ['drums'],
            ['buf'],
            name=name,
        )
        dlal.connect(
            self.drums,
            [self.buf, '<+', self.lim],
        )

#===== init =====#
audio = dlal.Audio(driver=True, run_size=args.run_size)
liner = dlal.Liner('assets/midis/audiobro5.mid')

piano = Piano()
bass = dlal.Sonic()
drums = Drums()

reverb = dlal.Reverb(0.3)
lim = dlal.Lim(hard=1, soft=0.9, soft_gain=0.3)
buf = dlal.Buf()
tape = dlal.Tape()

#===== commands =====#
if args.start:
    liner.advance(args.start)

bass.from_json({
    "0": {
        "a": 5e-3, "d": 3e-4, "s": 0.5, "r": 0.01, "m": 1,
        "i0": 0.3, "i1": 0.5, "i2": 0.4, "i3": 0.3, "o": 0.5,
    },
    "1": {
        "a": 5e-3, "d": 1e-4, "s": 0.5, "r": 0.01, "m": 1.99,
        "i0": 0.01, "i1": 0, "i2": 0, "i3": 0, "o": 0,
    },
    "2": {
        "a": 4e-3, "d": 3e-4, "s": 0.5, "r": 0.01, "m": 3.00013,
        "i0": 0.01, "i1": 0, "i2": 0, "i3": 0, "o": 0,
    },
    "3": {
        "a": 3e-3, "d": 1e-4, "s": 0.5, "r": 0.01, "m": 4.0001,
        "i0": 0.01, "i1": 0, "i2": 0, "i3": 0, "o": 0,
    },
})

drums.drums.load_drums()
drums.drums.amplify(0.5, dlal.Buf.Drum.bass)
drums.drums.amplify(0.5, dlal.Buf.Drum.snare)
drums.drums.amplify(0.5, dlal.Buf.Drum.low_floor_tom)
drums.drums.amplify(0.5, dlal.Buf.Drum.high_floor_tom)
drums.drums.amplify(0.5, dlal.Buf.Drum.low_tom)
drums.drums.amplify(0.5, dlal.Buf.Drum.low_mid_tom)
drums.drums.amplify(0.5, dlal.Buf.Drum.high_mid_tom)
drums.drums.amplify(0.5, dlal.Buf.Drum.high_tom)
drums.drums.amplify(0.5, dlal.Buf.Drum.mute_cuica)
drums.drums.amplify(0.5, dlal.Buf.Drum.open_cuica)

#===== connect =====#
dlal.connect(
    liner,
    [
        drums,
        drums,
        piano,
        piano,
        bass,
        drums,
    ],
    [buf,
        '<+', lim,
        '<+', reverb,
    ],
    [audio, tape],
)

#===== start =====#
dlal.typical_setup(duration=20)
