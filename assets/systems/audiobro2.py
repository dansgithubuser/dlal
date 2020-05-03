import dlal

import midi

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
Voice('arp', 'arp', 'sonic')
Voice('harp', 'sonic')
bins = 512
sample_rate = 44100
sweep = 48 / 12
b = 167 / (sample_rate/2)
m = 440 / (sample_rate/2) / (1-b)
Subsystem('sweep', {
    'midi': ('midi', [], {'port': None}),
    'gate_adsr': ('adsr', [1, 1, 1, 7e-6], {}),
    'gate_oracle': ('oracle', [], {'m': 0.6, 'format': ('gain_y', '%')}),
    'adsr': ('adsr', [1/4/sample_rate, 1, 1, 1e-5], {}),
    'gain': ('gain', [sweep**2], {}),
    'unary2': ('unary', ['sqrt'], {}),
    'unary': ('unary', ['exp2'], {}),
    'oracle': ('oracle', [], {'m': m, 'b': b, 'format': ('bandpass', '%', 1, bins)}),
    'train': ('osc', ['saw'], {}),
    'train2': ('osc', ['saw'], {'bend': 1.0081}),
    'train_adsr': ('adsr', [5e-8, 1, 1, 5e-5], {}),
    'train_oracle': ('oracle', [], {'m': 0.2, 'format': ('set', '%')}),
    'train_gain': ('gain', [], {}),
    'fir': ('fir', [], {}),
    'delay': ('delay', [22050], {'gain_x': 0}),
    'buf': ('buf', [], {}),
})
liner = dlal.Liner()
lpf = dlal.Lpf()
reverb = dlal.Reverb()
buf = dlal.Buf()
tape = dlal.Tape(1 << 17)

voices = [
    drum,
    shaker1,
    shaker2,
    burgers,
    bass,
    arp,
    harp,
]

# add
audio.add(comm)
for voice in voices:
    for i in voice.components.values():
        audio.add(i)
for i in sweep.components.values():
    audio.add(i)
audio.add(liner)
audio.add(lpf)
audio.add(reverb)
audio.add(buf)
audio.add(tape)

# commands
liner.load('assets/midis/audiobro2.mid', immediate=True)
liner.advance(sys_arg(1, float, 0))

# cowbell
drum.buf.load('assets/sounds/drum/cowbell.wav', 56)
# kick
drum.buf.load('assets/sounds/drum/kick.wav', 36)
drum.buf.resample(4, 36)
# ride
drum.buf.load('assets/sounds/drum/ride-bell.wav', 53)
drum.buf.resample(0.465, 53)
drum.buf.amplify(0.3, 53)
# snare
drum.buf.load('assets/sounds/drum/snare.wav', 40)
drum.buf.resample(0.63, 40)
drum.buf.crop(0, 0.1, 40)
drum.buf.amplify(0.7, 40)
# ride
drum.buf.load('assets/sounds/drum/ride.wav', 46)
drum.buf.resample(0.45, 46)
drum.buf.amplify(0.5, 46)
# bongos
drum.buf.load('assets/sounds/drum/bongo-lo.wav', 64)
drum.buf.resample(1.1, 64)
drum.buf.amplify(0.5, 64)
drum.buf.load('assets/sounds/drum/bongo-hi.wav', 63)
drum.buf.resample(0.85, 63)
drum.buf.amplify(0.5, 63)

shaker1.buf.load('assets/sounds/drum/shaker1.wav', 82)

shaker2.buf.load('assets/sounds/drum/shaker2.wav', 82)
shaker2.buf.amplify(0.5, 82)

burgers.buf.load('assets/local/burgers/people.wav', 60)
burgers.buf.amplify(4, 60)
burgers.buf.clip(0.3, 60)

bass.sonic.from_json({
    "0": {
        "a": "5e-4", "d": "1e-4", "s": "0.5", "r": "0.01", "m": "1",
        "i0": "0.2", "i1": "0.15", "i2": "0.03", "i3": "0.03", "o": "0.25",
    },
    "1": {
        "a": "5e-4", "d": "4e-6", "s": "0", "r": "0.01", "m": "3",
        "i0": "0.9", "i1": "0", "i2": "0", "i3": "0", "o": "0",
    },
    "2": {
        "a": "5e-4", "d": "4e-6", "s": "0", "r": "0.01", "m": "4.01",
        "i0": "0.9", "i1": "0", "i2": "0", "i3": "0", "o": "0",
    },
    "3": {
        "a": "5e-4", "d": "4e-6", "s": "0", "r": "0.01", "m": "1.94",
        "i0": "0.9", "i1": "0", "i2": "0", "i3": "0", "o": "0",
    },
})

arp.sonic.from_json({
    "0": {
        "a": "0.01", "d": "2e-4", "s": "0", "r": "2e-4", "m": "1",
        "i0": "0", "i1": "0.1", "i2": "0", "i3": "0", "o": "0.1",
    },
    "1": {
        "a": "0.01", "d": "2e-4", "s": "0", "r": "2e-4", "m": "1",
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

harp.sonic.from_json({
    "0": {
        "a": "0.01", "d": "1e-4", "s": "0", "r": "1e-4", "m": "1",
        "i0": "0", "i1": "0", "i2": "0", "i3": "0", "o": "0.1",
    },
    "1": {
        "a": "0", "d": "0", "s": "0", "r": "0", "m": "0",
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
        '>', sweep.gate_adsr,
        '>', sweep.train,
        '>', sweep.train2,
        '>', sweep.train_adsr,
    ],
    sweep.adsr,
    [sweep.oracle,
        '<', sweep.unary2,
        '<', sweep.unary,
        '<', sweep.gain,
    ],
    sweep.fir,
    [sweep.buf,
        '<', sweep.delay, sweep.gate_oracle, sweep.gate_adsr,
        '<', sweep.train,
        '<', sweep.train2,
        '<', sweep.train_gain, sweep.train_oracle, sweep.train_adsr,
    ],
    buf,
)
lpf.connect(buf)
reverb.connect(buf)
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
                tape.to_file_i16le(1 << 14, file)
else:
    dlal.typical_setup()
