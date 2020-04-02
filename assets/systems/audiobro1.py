import dlal

import sys

def sys_arg(i, f=str, default=None):
    if len(sys.argv) > i:
        return f(sys.argv[i])
    return default

class Voice:
    def __init__(self, **kwargs):
        self.components = {}
        for k, v in kwargs.items():
            if k in 'io': continue
            self.components[k] = v
            setattr(self, k, v)
        items = list(self.components.items())
        self.i = self.pick(kwargs.get('i', items[ 0][0]))
        self.o = self.pick(kwargs.get('o', items[-1][0]))

    def pick(self, ks):
        return [
            v
            for k, v in self.components.items()
            if k in ks
        ]

# init
driver = dlal.Audio()
comm = dlal.Comm()
drum = Voice(buf=dlal.Buf(), gain=dlal.Gain(), o=['buf'])
piano = Voice(sonic=dlal.Sonic())
bass = Voice(sonic=dlal.Sonic())
ghost = Voice(sonic=dlal.Sonic())
bell = Voice(sonic=dlal.Sonic())
goon = Voice(sonic=dlal.Sonic())
liner = dlal.Liner()

voices = [
    drum,
    piano,
    bass,
    ghost,
    bell,
    goon,
]

# add
driver.add(comm)
for voice in voices:
    for c in voice.components.values():
        driver.add(c)
driver.add(liner)

# commands
liner.load('assets/midis/audiobro1.mid')
liner.advance(sys_arg(1, float, 0))

drum.buf.load('assets/sounds/animal/cricket.wav', 56)
drum.buf.load('assets/sounds/drum/kick.wav', 36)
drum.buf.load('assets/sounds/drum/snare.wav', 38)
drum.buf.load('assets/sounds/drum/hat.wav', 42)
drum.buf.load('assets/sounds/drum/ride.wav', 46)
drum.gain.set(0)

bass.sonic.from_json({
    "0": {
        "a": "0.01", "d": "0.01", "s": "1", "r": "0.01", "m": "1",
        "i0": "0", "i1": "1", "i2": "0", "i3": "0", "o": "0.25",
    },
    "1": {
        "a": "0.01", "d": "1e-06", "s": "1", "r": "0.01", "m": "1",
        "i0": "0", "i1": "0", "i2": "0", "i3": "0", "o": "0",
    },
    "2": {
        "a": "0", "d": "0", "s": "0", "r": "0", "m": "0",
        "i0": "0", "i1": "0", "i2": "0", "i3": "0", "o": "0",
    },
    "3": {
        "a": "0", "d": "0", "s": "0", "r": "0", "m": "0",
        "i0": "0", "i1": "0", "i2": "0", "i3": "0", "o": "0",
    },
})
piano.sonic.from_json({
    "0": {
        "a": "4e-3", "d": "3e-5", "s": "0", "r": "3e-4", "m": "1",
        "i0": "0.06", "i1": "0.2", "i2": "0", "i3": "0", "o": "0.01",
    },
    "1": {
        "a": "6e-3", "d": "2e-3", "s": "0", "r": "2e-3", "m": "4",
        "i0": "0", "i1": "0", "i2": "0", "i3": "0", "o": "0",
    },
    "2": {
        "a": "4e-3", "d": "1e-4", "s": "0", "r": "2e-4", "m": "1",
        "i0": "0", "i1": "0", "i2": "0", "i3": "0.06", "o": "0.2",
    },
    "3": {
        "a": "0.025", "d": "6e-5", "s": "0.2", "r": "3e-5", "m": "1",
        "i0": "0", "i1": "0", "i2": "0", "i3": "0", "o": "0",
    },
})
ghost.sonic.from_json({
    "0": {
        "a": "7e-4", "d": "5e-3", "s": "1", "r": "6e-5", "m": "1",
        "i0": "0", "i1": "0", "i2": "1", "i3": "1", "o": "0.05",
    },
    "1": {
        "a": "1e-6", "d": "2e-3", "s": "1", "r": "6e-5", "m": "4",
        "i0": "0", "i1": "0", "i2": "0", "i3": "0", "o": "0.125",
    },
    "2": {
        "a": "1e-5", "d": "3e-5", "s": "0.25", "r": "6e-5", "m": "1",
        "i0": "0", "i1": "0", "i2": "0", "i3": "0", "o": "0.125",
    },
    "3": {
        "a": "4e-6", "d": "1e-5", "s": "0.25", "r": "6e-5", "m": "2",
        "i0": "0", "i1": "0", "i2": "0", "i3": "0", "o": "0.125",
    },
})
bell.sonic.from_json({
    "0": {
        "a": "0.01", "d": "3e-5", "s": "0", "r": "3e-5", "m": "1",
        "i0": "0", "i1": "0.1", "i2": "0", "i3": "0", "o": "0.1",
    },
    "1": {
        "a": "0.01", "d": "3e-5", "s": "0", "r": "3e-5", "m": "2",
        "i0": "0", "i1": "0", "i2": "0", "i3": "0", "o": "0",
    },
    "2": {
        "a": "0.01", "d": "3e-5", "s": "0", "r": "3e-5", "m": "1",
        "i0": "0", "i1": "0", "i2": "0", "i3": "0.3", "o": "0.01",
    },
    "3": {
        "a": "0.01", "d": "3e-5", "s": "0", "r": "3e-5", "m": "4",
        "i0": "0", "i1": "0", "i2": "0", "i3": "0", "o": "0",
    },
})
goon.sonic.from_json({
    "0": {
        "a": "1e-3", "d": "1e-3", "s": "0.5", "r": "3e-4", "m": "1",
        "i0": "0", "i1": "1", "i2": "0", "i3": "0", "o": "0.15",
    },
    "1": {
        "a": "1e-3", "d": "1e-3", "s": "0.5", "r": "3e-4", "m": "2",
        "i0": "0", "i1": "0", "i2": "0", "i3": "0", "o": "0",
    },
    "2": {
        "a": "0", "d": "0", "s": "0", "r": "0", "m": "0",
        "i0": "0", "i1": "0", "i2": "0", "i3": "0", "o": "0",
    },
    "3": {
        "a": "0", "d": "0", "s": "0", "r": "0", "m": "0",
        "i0": "0", "i1": "0", "i2": "0", "i3": "0", "o": "0",
    },
})

# connect
drum.gain.connect(drum.buf)
for voice in voices:
    for i in voice.i:
        liner.connect(i)
    for o in voice.o:
        o.connect(driver)

# setup
dlal.typical_setup()
