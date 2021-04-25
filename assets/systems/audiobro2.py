import dlal

import midi

import math
import sys

def sys_arg(i, f=str, default=None):
    if len(sys.argv) > i:
        return f(sys.argv[i])
    return default

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
comm = dlal.Comm()
Voice('drum', 'buf')
Voice('shaker1', 'buf')
Voice('shaker2', 'buf')
Voice('burgers', 'buf')
Voice('bass', 'sonic')
Voice('arp', 'arp', 'sonic', 'osc', 'unary', 'oracle', output=['sonic'])
Voice('harp1', 'osc', 'oracle', 'sonic', input=['sonic'])
Voice('harp2', 'osc', 'oracle', 'sonic', input=['sonic'])
sample_rate = 44100
sweep = 48 / 12
b = 0 / (sample_rate/2)
m = 440 / (sample_rate/2) / (1-b) * 2 * math.pi
Subsystem('sweep', {
    'midi': ('midi', [], {'port': None}),
    'gate_adsr': ('adsr', [1, 1, 1, 7e-6], {}),
    'gate_oracle': ('oracle', [], {'m': 0.6, 'format': ('gain_y', '%')}),
    'adsr': ('adsr', [1/4/sample_rate, 1, 1, 1e-5], {}),
    'midman': ('midman', [], {'directives': [([{'nibble': 0x90}], 0, 'set', '%1*0.08')]}),
    'gain': ('gain', [], {}),
    'unary2': ('unary', ['none'], {}),
    'unary': ('unary', ['exp2'], {}),
    'oracle': ('oracle', [], {'m': m, 'b': b, 'format': ('pole_pairs_bandpass', '%', 0.02, 6)}),
    'train': ('osc', ['saw'], {}),
    'train2': ('osc', ['saw'], {'bend': 1.0081}),
    'train_adsr': ('adsr', [5e-8, 1, 1, 5e-5], {}),
    'train_oracle': ('oracle', [], {'m': 0.2, 'format': ('set', '%')}),
    'train_gain': ('gain', [], {}),
    'iir1': ('iir', [], {}),
    'iir2': ('iir', [], {}),
    'iir3': ('iir', [], {}),
    'iir4': ('iir', [], {}),
    'delay': ('delay', [22050], {'gain_i': 1}),
    'buf': ('buf', [], {}),
})
midman = dlal.Midman([
    ([{'nibble': 0x90}, 0x3c], 0, 'freq', 0),  # harp1.osc
    ([{'nibble': 0x90}, 0x3c], 1, 'freq', 0),  # harp2.osc
    ([{'nibble': 0x90}, 0x3c], 0, 'phase', 0),
    ([{'nibble': 0x90}, 0x3c], 1, 'phase', 0),
    ([{'nibble': 0x90}, 0x3e], 0, 'freq', 1/16),
    ([{'nibble': 0x90}, 0x3e], 1, 'freq', 1/16),
    ([{'nibble': 0x90}, 0x40], 2, 'gain_x', 1),  # delay
    ([{'nibble': 0x90}, 0x41], 2, 'gain_x', 0),
    ([{'nibble': 0x90}, 0x43], 3, 'phase', 0.75),  # arp.osc
    ([{'nibble': 0x90}, 0x45], 4, 'm', -28*m),  # sweep.oracle
    ([{'nibble': 0x90}, 0x45], 4, 'b', 16000 / (sample_rate/2)),
    ([{'nibble': 0x90}, 0x45], 5, 'gain_x', 0),  # sweep.delay
    ([{'nibble': 0x90}, 0x45], 6, 'a', 1e-3),  # sweep.train_adsr
    ([{'nibble': 0x90}, 0x45], 6, 'r', 1e-3),
    ([{'nibble': 0x90}, 0x45], 7, 'm', 0.0005),  # sweep.train_oracle
    ([{'nibble': 0x90}, 0x45], 8, 'r', 1),  # sweep.adsr
    ([{'nibble': 0x90}, 0x47], 4, 'm', m),  # sweep.oracle
    ([{'nibble': 0x90}, 0x47], 4, 'b', b),
    ([{'nibble': 0x90}, 0x47], 5, 'gain_x', 1),  # sweep.delay
    ([{'nibble': 0x90}, 0x47], 6, 'a', 5e-8),  # sweep.train_adsr
    ([{'nibble': 0x90}, 0x47], 6, 'r', 5e-5),
    ([{'nibble': 0x90}, 0x47], 7, 'm', 0.2),  # sweep.train_oracle
    ([{'nibble': 0x90}, 0x47], 8, 'r', 1e-5),  # sweep.adsr
])
harp1.oracle.m(1/12)
harp2.oracle.m(0/4)
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
liner.advance(sys_arg(1, float, 0))

# cowbell
drum.buf.load('assets/sounds/drum/cowbell.wav', 56)
drum.buf.amplify(2, 56)
# kick
drum.buf.load('assets/sounds/drum/kick.wav', 36)
drum.buf.resample(4, 36)
# ride
drum.buf.load('assets/sounds/drum/ride-bell.wav', 53)
drum.buf.resample(0.465, 53)
drum.buf.amplify(0.3, 53)
# tom
drum.buf.load('assets/sounds/drum/floor-tom.wav', 50)
drum.buf.crop(0, 0.05, 50)
drum.buf.resample(3, 50)
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
        "i0": 0.3, "i1": 0.5, "i2": 0.4, "i3": 0.3, "o": 0.25,
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
        "a": 0.01, "d": 2e-4, "s": 0, "r": 2e-4, "m": 1,
        "i0": 0, "i1": 0.1, "i2": 0.5, "i3": 0, "o": 0.1,
    },
    "1": {
        "a": 1e-3, "d": 4e-4, "s": 0, "r": 4e-4, "m": 1.99,
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
arp.osc.freq(1/8)
arp.oracle.m(0.1)
arp.oracle.format('i0', 0, '%')
arp.unary.mode('exp2')

harp1.sonic.from_json({
    "0": {
        "a": 0.01, "d": 2e-5, "s": 0, "r": 2e-5, "m": 1,
        "i0": 0, "i1": 0.1, "i2": 0, "i3": 0, "o": 0.1,
    },
    "1": {
        "a": 0.01, "d": 4e-5, "s": 0.5, "r": 2e-5, "m": 3,
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
harp1.oracle.format('offset', 6, '%')

harp2.sonic.from_json({
    "0": {
        "a": 0.01, "d": 2e-5, "s": 0, "r": 2e-5, "m": 1,
        "i0": 0, "i1": 0.1, "i2": 0, "i3": 0, "o": 0.1,
    },
    "1": {
        "a": 0.01, "d": 4e-5, "s": 0.5, "r": 2e-5, "m": 3,
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
harp2.oracle.format('offset', 7, '%')

lpf.set(0.9)
reverb.set(0.3)

# connect
arp.arp.connect(arp.sonic)
arp.osc.connect(arp.oracle)
arp.unary.connect(arp.oracle)
arp.oracle.connect(arp.sonic)
for voice in voices:
    for i in voice.input:
        liner.connect(i)
    for i in voice.output:
        i.connect(buf)
harp1.osc.connect(harp1.oracle)
harp2.osc.connect(harp2.oracle)
harp1.oracle.connect(liner)
harp2.oracle.connect(liner)
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
        '<+', sweep.unary2,
        '<+', sweep.unary,
        '<+', sweep.gain,
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
midman.connect(harp1.osc)
midman.connect(harp2.osc)
midman.connect(delay)
midman.connect(arp.osc)
midman.connect(sweep.oracle)
midman.connect(sweep.delay)
midman.connect(sweep.train_adsr)
midman.connect(sweep.train_oracle)
midman.connect(sweep.adsr)
lpf.connect(buf)
reverb.connect(buf)
delay.connect(buf)
lim.connect(buf)
buf.connect(tape)
buf.connect(audio)

# setup
end = sys_arg(2, float)
if end:
    duration = end - sys_arg(1, float, 0)
    runs = int(duration * 44100 / 64)
    with open('audiobro2.raw', 'wb') as file:
        for i in range(runs):
            audio.run()
            if i % (1 << 8) == 0xff:
                tape.to_file_i16le(file, 1 << 14)
else:
    dlal.typical_setup()
