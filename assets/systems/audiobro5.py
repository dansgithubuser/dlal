import dlal

import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--start', '-s', type=float)
parser.add_argument('--run-size', type=int)
args = parser.parse_args()

class Piano(dlal.subsystem.Voices):
    def init(self, name=None):
        super().init(
            ('digitar', [], {'lowness': 0.3, 'feedback': 0.9999, 'release': 0.1}),
            vol=0.1,
            per_voice_init=lambda voice, i: voice.hammer(offset=(3 + i) / 10),
            name=name,
        )

#===== init =====#
audio = dlal.Audio(driver=True, run_size=args.run_size)
liner = dlal.Liner('assets/midis/audiobro5.mid')

piano = dlal.Sonic()
bass = dlal.Sonic()
drums = dlal.Buf()

lim = dlal.Lim(hard=1, soft=0.9, soft_gain=0.3)
buf = dlal.Buf()
tape = dlal.Tape()

#===== commands =====#
if args.start:
    liner.advance(args.start)

piano.from_json({
    "0": {
        "a": 4e-3, "d": 5e-5, "s": 0.2, "r": 2e-4, "m": 1,
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

drums.load_drums()

#===== connect =====#
dlal.connect(
    liner,
    [
        piano,
        piano,
        bass,
        drums,
    ],
    [buf, '<+', lim],
    [audio, tape],
)

#===== start =====#
dlal.typical_setup(duration=10)
