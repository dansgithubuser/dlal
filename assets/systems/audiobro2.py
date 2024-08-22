import dlal

import midi

import math
import argparse

parser = argparse.ArgumentParser()
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
Voice('burgers1', 'buf')
Voice('burgers2', 'buf')
Voice('ghost', 'sonic')
Voice('bass', 'sonic')
Voice('arp', 'arp', 'sonic')
Voice('harp1', 'sonic')
Voice('harp2', 'sonic')
sample_rate = 44100
m = 220 / (sample_rate/2)
b = -1 * m
Subsystem('sweep', {
    'midi': ('midi', [], {'port': None}),
    'gate_adsr': ('adsr', [1, 1, 1, 7e-6], {}),
    'gate_oracle': ('oracle', [], {'m': 0.6, 'format': ('gain_y', ['%']), 'cv_i': 1}),
    'adsr': ('adsr', [1/4/sample_rate, 1, 1, 1e-5], {}),
    'midman': ('midman', [], {'directives': [([{'nibble': 0x90}], 0, 'set', '%1*0.08')]}),
    'gain': ('gain', [], {}),
    'unary2': ('unary', ['none'], {}),
    'unary': ('unary', ['exp2'], {}),
    'oracle': ('oracle', [], {'m': m, 'b': b, 'format': ('pole_pairs_bandpass', ['%', 0.02, 6]), 'cv_i': 1}),
    'train': ('osc', ['saw'], {}),
    'train2': ('osc', ['saw'], {'bend': 1.0081}),
    'train_adsr': ('adsr', [5e-8, 1, 1, 5e-5], {}),
    'train_oracle': ('oracle', [], {'m': 0.3, 'format': ('set', ['%']), 'cv_i': 1}),
    'train_gain': ('gain', [], {}),
    'iir1': ('iir', [], {}),
    'iir2': ('iir', [], {}),
    'iir3': ('iir', [], {}),
    'iir4': ('iir', [], {}),
    'delay': ('delay', [22050], {'gain_i': 1}),
    'pan_osc': ('osc', ['tri', 1/8], {}),
    'pan_oracle': ('oracle', [], {'m': 90, 'format': ('set', ['%', 10])}),
    'pan': ('pan', [], {}),
    'buf': ('buf', [], {}),
})
mm_delay1 = 0
mm_delay2 = 1
mm_bass = 2
midman = dlal.Midman([
    # E - 120 echo on
    ([{'nibble': 0x90}, 0x40], mm_delay1, 'gain_x', 1),
    # F - 120 echo off
    ([{'nibble': 0x90}, 0x41], mm_delay1, 'gain_x', 0),
    # F# - 120 echo medium
    ([{'nibble': 0x90}, 0x42], mm_delay1, 'gain_x', 0.5),
    # G - loud bass
    ([{'nibble': 0x90}, 0x43], mm_bass, 'o', 0, 0.5),
    # A - quiet bass
    ([{'nibble': 0x90}, 0x45], mm_bass, 'o', 0, 0.4),
    # B - 100 echo off
    ([{'nibble': 0x90}, 0x47], mm_delay2, 'gain_x', 0),
    # C - 100 echo on
    ([{'nibble': 0x90}, 0x48], mm_delay2, 'gain_x', 1),
])
liner = dlal.Liner()
mixer = dlal.subsystem.Mixer(
    [
        {'gain': 1.4, 'pan': [   0, 10]},  # drum
        {'gain': 1.4, 'pan': [   0, 10]},  # shaker1
        {'gain': 1.4, 'pan': [   0, 10]},  # shaker2
        {'gain': 1.4, 'pan': [ -15, 10]},  # burgers1
        {'gain': 1.4, 'pan': [  15, 10]},  # burgers2
        {'gain': 1.4, 'pan': [ -45, 10]},  # ghost
        {'gain': 1.4, 'pan': [   0, 10]},  # bass
        {'gain': 1.4, 'pan': [   0, 10]},  # arp
        {'gain': 1.4, 'pan': [ -30, 10]},  # harp1
        {'gain': 1.4, 'pan': [  30, 10]},  # harp2
    ],
    post_mix_extra={
        'lpf': ('lpf', [0.9]),
        'delay1': ('delay', [11025], {'gain_y': 0.3, 'gain_i': 1, 'smooth': 0.8, 'gain_x': 1}),
        'delay2': ('delay', [13230], {'gain_y': 0.3, 'gain_i': 1, 'smooth': 0.8, 'gain_x': 0}),
    },
    reverb=0.3,
    lim=[1, 0.9, 0.3],
    sample_rate=44100,
)
tape = dlal.Tape(1 << 17)

voices = [
    drum,
    shaker1,
    shaker2,
    burgers1,
    burgers2,
    ghost,
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
for i in mixer.components.values():
    audio.add(i)
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
drum.buf.amplify(2, 52)
# snare
drum.buf.load('assets/sounds/drum/snare.wav', 40)
drum.buf.crop(0, 0.1, 40)
drum.buf.amplify(4, 40)
drum.buf.clip(2.0, 40)
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
# crash
drum.buf.load('assets/sounds/drum/crash.wav', 49)

shaker1.buf.load('assets/sounds/drum/shaker1.wav', 82)

shaker2.buf.load('assets/sounds/drum/shaker2.wav', 82)
shaker2.buf.amplify(0.5, 82)

for burgers in [burgers1, burgers2]:
    burgers.buf.load('assets/local/burgers/people.wav', 60)
    burgers.buf.amplify(8, 60)
    burgers.buf.load('assets/local/burgers/pickle.wav', 62)
    burgers.buf.amplify(8, 62)
    burgers.buf.load('assets/local/burgers/plate.wav', 64)
    burgers.buf.amplify(8, 64)
    burgers.buf.load('assets/local/burgers/plate2.wav', 63)
    burgers.buf.amplify(8, 63)
    burgers.buf.load('assets/local/burgers/mm.wav', 65)
    burgers.buf.amplify(8, 65)
    burgers.buf.load('assets/local/burgers/think.wav', 67)
    burgers.buf.amplify(4, 67)
    burgers.buf.load('assets/local/burgers/legs.wav', 69)
    burgers.buf.amplify(8, 69)

    burgers.buf.load('assets/local/burgers/people.wav', 72)  # people
    burgers.buf.crop(0.4540, 0.7968, 72)
    burgers.buf.amplify(8, 72)
    burgers.buf.sound_params(72, repeat=True, accel=1.2, cresc=0.8)
    burgers.buf.load('assets/local/burgers/people.wav', 74)  # think
    burgers.buf.crop(0.9103, 1.2137, 74)
    burgers.buf.amplify(8, 74)
    burgers.buf.sound_params(74, repeat=True, accel=0.99, cresc=0.8)
    burgers.buf.load('assets/local/burgers/people.wav', 76)  # burgers
    burgers.buf.crop(1.581, 1.997, 76)
    burgers.buf.amplify(8, 76)
    burgers.buf.sound_params(76, repeat=True, accel=0.5, cresc=0.9)
    burgers.buf.load('assets/local/burgers/pickle.wav', 77)  # pickle
    burgers.buf.crop(0.3377, 0.5736, 77)
    burgers.buf.amplify(8, 77)
    burgers.buf.sound_params(77, repeat=True, accel=9.0, cresc=0.9)
    burgers.buf.load('assets/local/burgers/people.wav', 79)  # people
    burgers.buf.crop(0.4540, 0.7968, 79)
    burgers.buf.amplify(8, 79)
    burgers.buf.sound_params(79, repeat=True, accel=0.6, cresc=0.9)
    burgers.buf.load('assets/local/burgers/people.wav', 81)  # think
    burgers.buf.crop(0.9103, 1.2137, 81)
    burgers.buf.amplify(8, 81)
    burgers.buf.sound_params(81, repeat=True, accel=4.0, cresc=0.9)
    burgers.buf.load('assets/local/burgers/people.wav', 83)  # burgers
    burgers.buf.crop(1.581, 1.997, 83)
    burgers.buf.amplify(8, 83)
    burgers.buf.sound_params(83, repeat=True, accel=0.9, cresc=0.9)
    burgers.buf.load('assets/local/burgers/people.wav', 84)  # they haven't been here
    burgers.buf.crop(2.3, 3.2, 84)
    burgers.buf.amplify(8, 84)

ghost.sonic.from_json({
    "0": {
        "a": 1e-2, "d": 2e-6, "s": 0, "r": 1e-3, "m": 0.99,
        "i0": 0.05, "i1": 0.4, "i2": 0.05, "i3": 0, "o": 0.2,
    },
    "1": {
        "a": 1e-2, "d": 1e-4, "s": 0, "r": 1e-3, "m": 1.99,
        "i0": 0, "i1": 0, "i2": 0, "i3": 0, "o": 0,
    },
    "2": {
        "a": 1e-2, "d": 2e-6, "s": 0, "r": 1e-3, "m": 1.007,
        "i0": 0.05, "i1": 0, "i2": 0, "i3": 0.8, "o": 0.2,
    },
    "3": {
        "a": 1e-2, "d": 8e-6, "s": 0, "r": 1e-3, "m": 0.992,
        "i0": 0, "i1": 0, "i2": 0, "i3": 0, "o": 0,
    },
})

bass.sonic.from_json({
    "0": {
        "a": 5e-3, "d": 3e-4, "s": 0.5, "r": 0.01, "m": 1,
        "i0": 0.3, "i1": 0.5, "i2": 0.4, "i3": 0.3, "o": 0,  # set by midman
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
        "a": 4e-3, "d": 5e-5, "s": 0.2, "r": 2e-4, "m": 1.006,
        "i0": 0, "i1": 0.06, "i2": 0, "i3": 0, "o": 0.25,
    },
    "1": {
        "a": 0.025, "d": 6e-5, "s": 0.2, "r": 3e-5, "m": 1,
        "i0": 0, "i1": 0, "i2": 0, "i3": 0, "o": 0,
    },
    "2": {
        "a": 4e-3, "d": 5e-5, "s": 0.2, "r": 2e-4, "m": 0.994,
        "i0": 0, "i1": 0.06, "i2": 0, "i3": 0, "o": 0.25,
    },
    "3": {
        "a": 0, "d": 0, "s": 0, "r": 0, "m": 0,
        "i0": 0, "i1": 0, "i2": 0, "i3": 0, "o": 0,
    },
})

harp2.sonic.from_json({
    "0": {
        "a": 4e-3, "d": 5e-5, "s": 0.2, "r": 2e-4, "m": 1.007,
        "i0": 0, "i1": 0.06, "i2": 0, "i3": 0, "o": 0.25,
    },
    "1": {
        "a": 0.025, "d": 6e-5, "s": 0.2, "r": 3e-5, "m": 1,
        "i0": 0, "i1": 0, "i2": 0, "i3": 0, "o": 0,
    },
    "2": {
        "a": 4e-3, "d": 5e-5, "s": 0.2, "r": 2e-4, "m": 0.993,
        "i0": 0, "i1": 0.06, "i2": 0, "i3": 0, "o": 0.25,
    },
    "3": {
        "a": 0, "d": 0, "s": 0, "r": 0, "m": 0,
        "i0": 0, "i1": 0, "i2": 0, "i3": 0, "o": 0,
    },
})

# connect
arp.arp.connect(arp.sonic)
for i_voice, voice in enumerate(voices):
    for i in voice.input:
        liner.connect(i)
    for i in voice.output:
        i.connect(mixer[i_voice])
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
        '<+', sweep.pan, sweep.pan_oracle, sweep.pan_osc,
    ],
    mixer.buf,
)
liner.connect(midman)
midman.connect(mixer.delay1)
midman.connect(mixer.delay2)
midman.connect(bass.sonic)
mixer.lpf.connect(mixer.buf)
mixer.delay1.connect(mixer.buf)
mixer.delay2.connect(mixer.buf)
mixer.buf.connect(tape)
mixer.buf.connect(audio)

# setup
if args.start:
    liner.advance(float(args.start))
dlal.typical_setup(duration=177)
