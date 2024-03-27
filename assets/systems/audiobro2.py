import dlal

import midi

import math
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--live', '-l', action='store_true')
parser.add_argument('--start', '-s')
parser.add_argument('--run-size', type=int)
args = parser.parse_args()

class Voice:
    def __init__(self, name, *kinds, input=None, output=None):
        globals()[name] = self
        self.components = {}
        for kind in kinds:
            component = dlal.component_class(kind)(name=f'{name}.{kind}')
            self.components[kind] = component
            setattr(self, kind, component)
        self.input = self.pick(input or [kinds[0]])
        self.output = self.pick(output or [kinds[-1]])

    def pick(self, ks):
        return [
            v
            for k, v in self.components.items()
            if k in ks
        ]

class Subsystem:
    def __init__(self, name, components):
        globals()[name] = self
        self.name = name
        self.components = {}
        for name, (kind, args, kwargs) in components.items():
            self.components[name] = dlal.component_class(kind)(*args, **kwargs, name=f'{self.name}.{name}')
            setattr(self, name, self.components[name])

# init
audio = dlal.Audio()
if args.run_size: audio.run_size(args.run_size)
comm = dlal.Comm()
Voice('drum', 'buf')
Voice('shaker1', 'buf')
Voice('shaker2', 'buf')
Voice('burgers', 'buf')
Voice('bass', 'sonic')
Voice('arp', 'arp', 'sonic')
Voice('harp1', 'sonic', input=['sonic'])
Voice('harp2', 'sonic', input=['sonic'])
sample_rate = 44100
sweep = 48 / 12
m = 220 / (sample_rate/2) * 2 * math.pi
b = -1 * m
Subsystem('sweep', {
    'midi': ('midi', [], {'port': None}),
    'gate_adsr': ('adsr', [1, 1, 1, 7e-6], {}),
    'gate_oracle': ('oracle', [], {'m': 0.6, 'format': ('gain_y', '%'), 'cv_i': 1}),
    'adsr': ('adsr', [1/4/sample_rate, 1, 1, 1e-5], {}),
    'midman': ('midman', [], {'directives': [([{'nibble': 0x90}], 0, 'set', '%1*0.08')]}),
    'gain': ('gain', [], {}),
    'unary2': ('unary', ['none'], {}),
    'unary': ('unary', ['exp2'], {}),
    'oracle': ('oracle', [], {'m': m, 'b': b, 'format': ('pole_pairs_bandpass', '%', 0.02, 6), 'cv_i': 1}),
    'train': ('osc', ['saw'], {}),
    'train2': ('osc', ['saw'], {'bend': 1.0081}),
    'train_adsr': ('adsr', [5e-8, 1, 1, 5e-5], {}),
    'train_oracle': ('oracle', [], {'m': 0.2, 'format': ('set', '%'), 'cv_i': 1}),
    'train_gain': ('gain', [], {}),
    'iir1': ('iir', [], {}),
    'iir2': ('iir', [], {}),
    'iir3': ('iir', [], {}),
    'iir4': ('iir', [], {}),
    'delay': ('delay', [22050], {'gain_i': 1}),
    'buf': ('buf', [], {}),
})
mm_delay = 0
midman = dlal.Midman([
    # E - echo on
    ([{'nibble': 0x90}, 0x40], mm_delay, 'gain_x', 1),
    # F - echo off
    ([{'nibble': 0x90}, 0x41], mm_delay, 'gain_x', 0),
])
liner = dlal.Liner()
lpf = dlal.Lpf()
reverb = dlal.Reverb()
delay = dlal.Delay(11025, gain_y=0.3, gain_i=1)
lim = dlal.Lim(hard=1, soft=0.9, soft_gain=0.3)
buf = dlal.Buf()
tape = dlal.Tape(1 << 17)

voices = [
    drum,
    shaker1,
    shaker2,
    burgers,
    bass,
    arp,
    harp1,
    harp2,
]

# add
audio.add(comm)
for voice in voices:
    for i in voice.components.values():
        audio.add(i)
for i in sweep.components.values():
    audio.add(i)
audio.add(midman)
audio.add(liner)
audio.add(lpf)
audio.add(reverb)
audio.add(delay)
audio.add(lim)
audio.add(buf)
audio.add(tape)

# commands
liner.load('assets/midis/audiobro2.mid', immediate=True)

# cowbell
drum.buf.load('assets/sounds/drum/cowbell.wav', 56)
drum.buf.amplify(2, 56)
# kick
drum.buf.load('assets/sounds/drum/kick.wav', 36)
drum.buf.resample(1.5, 36)
# ride
drum.buf.load('assets/sounds/drum/ride-bell.wav', 53)
drum.buf.resample(0.455, 53)
drum.buf.amplify(0.3, 53)
# tom
drum.buf.load('assets/sounds/drum/floor-tom.wav', 50)
drum.buf.crop(0, 0.05, 50)
drum.buf.resample(3, 50)
# clap
drum.buf.load('assets/sounds/drum/clap.wav', 52)
drum.buf.resample(1.48, 52)
# snare
drum.buf.load('assets/sounds/drum/snare.wav', 40)
drum.buf.crop(0, 0.1, 40)
drum.buf.amplify(2, 40)
drum.buf.clip(1.0, 40)
# ride
drum.buf.load('assets/sounds/drum/ride.wav', 46)
drum.buf.resample(0.45, 46)
drum.buf.amplify(0.5, 46)
# bongos
drum.buf.load('assets/sounds/drum/bongo-lo.wav', 64)
drum.buf.resample(1.1, 64)
drum.buf.amplify(0.75, 64)
drum.buf.load('assets/sounds/drum/bongo-hi.wav', 63)
drum.buf.resample(0.85, 63)
drum.buf.amplify(0.75, 63)
# guiro
drum.buf.load('assets/sounds/drum/guiro.wav', 47)
# megabass
drum.buf.load('assets/sounds/drum/low-tom.wav', 41)
drum.buf.resample(0.45, 41)
drum.buf.amplify(5, 41)
drum.buf.clip(0.4, 41)

shaker1.buf.load('assets/sounds/drum/shaker1.wav', 82)

shaker2.buf.load('assets/sounds/drum/shaker2.wav', 82)
shaker2.buf.amplify(0.5, 82)

burgers.buf.load('assets/local/burgers/people.wav', 60)
burgers.buf.load('assets/local/burgers/pickle.wav', 62)
burgers.buf.load('assets/local/burgers/plate.wav', 64)
burgers.buf.load('assets/local/burgers/plate2.wav', 63)
burgers.buf.load('assets/local/burgers/mm.wav', 65)
burgers.buf.load('assets/local/burgers/think.wav', 67)
burgers.buf.load('assets/local/burgers/legs.wav', 69)
for i in range(60, 72):
    burgers.buf.amplify(5, i)
    burgers.buf.clip(0.25, i)

bass.sonic.from_json({
    "0": {
        "a": 5e-3, "d": 3e-4, "s": 0.5, "r": 0.01, "m": 1,
        "i0": 0.3, "i1": 0.5, "i2": 0.4, "i3": 0.3, "o": 0.5,
    },
    "1": {
        "a": 5e-3, "d": 1e-4, "s": 0.5, "r": 0.01, "m": 1.99,
        "i0": 0.04, "i1": 0, "i2": 0, "i3": 0, "o": 0,
    },
    "2": {
        "a": 4e-3, "d": 3e-4, "s": 0.5, "r": 0.01, "m": 3.00013,
        "i0": 0.03, "i1": 0, "i2": 0, "i3": 0, "o": 0,
    },
    "3": {
        "a": 3e-3, "d": 1e-4, "s": 0.5, "r": 0.01, "m": 4.0001,
        "i0": 0.02, "i1": 0, "i2": 0, "i3": 0, "o": 0,
    },
})

arp.sonic.from_json({
    "0": {
        "a": 4e-3, "d": 5e-5, "s": 0, "r": 2e-3, "m": 1,
        "i0": 0, "i1": 0.06, "i2": 0, "i3": 0, "o": 0.25,
    },
    "1": {
        "a": 0.025, "d": 6e-5, "s": 0, "r": 3e-4, "m": 1,
        "i0": 0, "i1": 0, "i2": 0, "i3": 0, "o": 0,
    },
    "2": {
        "a": 0, "d": 0, "s": 0, "r": 0, "m": 0,
        "i0": 0, "i1": 0, "i2": 0, "i3": 0, "o": 0,
    },
    "3": {
        "a": 0, "d": 0, "s": 0, "r": 0, "m": 0,
        "i0": 0, "i1": 0, "i2": 0, "i3": 0, "o": 0,
    },
})

harp1.sonic.from_json({
    "0": {
        "a": 4e-3, "d": 5e-5, "s": 0.2, "r": 2e-4, "m": 1,
        "i0": 0, "i1": 0.06, "i2": 0, "i3": 0, "o": 0.25,
    },
    "1": {
        "a": 0.025, "d": 6e-5, "s": 0.2, "r": 3e-5, "m": 1,
        "i0": 0, "i1": 0, "i2": 0, "i3": 0, "o": 0,
    },
    "2": {
        "a": 0, "d": 0, "s": 0, "r": 0, "m": 0,
        "i0": 0, "i1": 0, "i2": 0, "i3": 0, "o": 0,
    },
    "3": {
        "a": 0, "d": 0, "s": 0, "r": 0, "m": 0,
        "i0": 0, "i1": 0, "i2": 0, "i3": 0, "o": 0,
    },
})

harp2.sonic.from_json({
    "0": {
        "a": 4e-3, "d": 5e-5, "s": 0.2, "r": 2e-4, "m": 1,
        "i0": 0, "i1": 0.06, "i2": 0, "i3": 0, "o": 0.25,
    },
    "1": {
        "a": 0.025, "d": 6e-5, "s": 0.2, "r": 3e-5, "m": 1,
        "i0": 0, "i1": 0, "i2": 0, "i3": 0, "o": 0,
    },
    "2": {
        "a": 0, "d": 0, "s": 0, "r": 0, "m": 0,
        "i0": 0, "i1": 0, "i2": 0, "i3": 0, "o": 0,
    },
    "3": {
        "a": 0, "d": 0, "s": 0, "r": 0, "m": 0,
        "i0": 0, "i1": 0, "i2": 0, "i3": 0, "o": 0,
    },
})

lpf.set(0.9)
reverb.set(0.3)

# connect
arp.arp.connect(arp.sonic)
for voice in voices:
    for i in voice.input:
        liner.connect(i)
    for i in voice.output:
        i.connect(buf)
dlal.connect(
    liner,
    [sweep.midi,
        '+>', sweep.midman, sweep.gain,
        '+>', sweep.gate_adsr,
        '+>', sweep.train,
        '+>', sweep.train2,
        '+>', sweep.train_adsr,
    ],
    sweep.adsr,
    [sweep.oracle,
        '<+', sweep.gain,
        '<+', sweep.unary2,
        '<+', sweep.unary,
    ],
    [sweep.iir1, sweep.iir2, sweep.iir3, sweep.iir4],
    [sweep.buf,
        '<+', sweep.delay, sweep.gate_oracle, sweep.gate_adsr,
        '<+', sweep.train,
        '<+', sweep.train2,
        '<+', sweep.train_gain, sweep.train_oracle, sweep.train_adsr,
    ],
    buf,
)
liner.connect(midman)
midman.connect(delay)
lpf.connect(buf)
reverb.connect(buf)
delay.connect(buf)
lim.connect(buf)
buf.connect(tape)
buf.connect(audio)

# setup
if args.start:
    liner.advance(float(args.start))
if args.live:
    dlal.typical_setup()
else:
    dlal.typical_setup(live=False, duration=92)
