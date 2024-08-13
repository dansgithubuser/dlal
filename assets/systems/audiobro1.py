import dlal

import midi

import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--start', '-s')
parser.add_argument('--run-size', type=int)
args = parser.parse_args()

class Voice:
    def __init__(self, name, *component_names, input=None, output=None):
        globals()[name] = self
        self.components = {}
        for component_name in component_names:
            kind = component_name.split('_')[0]
            component = dlal.component_class(kind)(name=f'{name}.{component_name}')
            self.components[component_name] = component
            setattr(self, component_name, component)
        self.input = self.pick(input or [component_names[0]])
        self.output = self.pick(output or [component_names[-1]])

    def pick(self, ks):
        return [
            v
            for k, v in self.components.items()
            if k in ks
        ]

class Lforacle:
    def __init__(self, name, freq, amp, b, fmt_name, *fmt_args, **fmt_kwargs):
        globals()[name] = self
        self.lfo = dlal.Lfo(name=f'{name}.lfo')
        self.oracle = dlal.Oracle(name=f'{name}.oracle')
        self.lfo.freq(freq)
        self.lfo.amp(amp)
        self.oracle.b(b)
        self.oracle.format(fmt_name, *fmt_args, **fmt_kwargs)
        self.lfo.connect(self.oracle)

    def add_to(self, driver):
        driver.add(self.lfo)
        driver.add(self.oracle)

    def connect(self, other):
        self.oracle.connect(other)

# init
driver = dlal.Audio()
if args.run_size: driver.run_size(int(args.run_size))
comm = dlal.Comm()
Voice('drum', 'buf')
Voice('piano', 'sonic', 'lfo', 'mul', 'buf_1', 'buf_2')
Voice('bass', 'sonic', 'lim', 'buf')
Voice('ghost', 'gain', 'midman', 'rhymel', 'lpf', 'lfo', 'oracle', 'sonic', 'lim', 'buf', input=['rhymel'])
Lforacle('ghost_lfo_i20', 0.40000, 0.3, 0.3, 'i2', 0, '%')
Lforacle('ghost_lfo_i30', 0.31221, 0.1, 0.1, 'i3', 0, '%')
Lforacle('ghost_lfo_i03', 0.12219, 0.1, 0.1, 'i0', 3, '%')
Voice('bell', 'sonic')
Voice('goon', 'sonic')
Voice('hat', 'buf')
hat_osc = dlal.Osc(wave='noise', freq='0.12141')
hat_oracle = dlal.Oracle(m=0.04, b=0.01, format=('offset', [6, '%']))
liner = dlal.Liner()
mixer = dlal.subsystem.Mixer(
    [
        {'pan': [0, 1]},
        {'pan': [0, 1]},
        {'pan': [0, 1]},
        {'pan': [0, 1]},
        {'pan': [0, 1]},
        {'pan': [0, 1]},
        {'pan': [0, 1]},
    ],
    post_mix_extra={
        'lpf': ('lpf', [0.9]),
    },
    reverb=1,
)
tape = dlal.Tape(1 << 17)

voices = [
    drum,
    piano,
    bass,
    ghost,
    bell,
    goon,
    hat,
]

# add
driver.add(comm)
for voice in voices:
    for i in voice.components.values():
        driver.add(i)
ghost_lfo_i20.add_to(driver)
ghost_lfo_i30.add_to(driver)
ghost_lfo_i03.add_to(driver)
driver.add(hat_osc)
driver.add(hat_oracle)
driver.add(liner)
for i in mixer.components.values():
    driver.add(i)
driver.add(tape)

# commands
liner.load('assets/midis/audiobro1.mid', immediate=True)
if args.start:
    liner.advance(float(args.start))

# 80 Hz sin
drum.buf.sin(0.5, 80, 0.5, 1, 1)
# cricket
drum.buf.load('assets/sounds/animal/cricket.wav', 56)
drum.buf.amplify(1.5, 56)
drum.buf.sin(0.25, 80, 0.75, 1, 2)
drum.buf.mul(56, 2)
# shunk
drum.buf.load('assets/sounds/drum/snare.wav', 36)
drum.buf.resample(0.3, 36)
drum.buf.crop(0, 0.06, 36)
drum.buf.amplify(0.4, 36)
drum.buf.load('assets/sounds/drum/low-tom.wav', 0)
drum.buf.resample(1.2, 0)
drum.buf.amplify(1.4, 0)
drum.buf.clip(1.0, 0)
drum.buf.add(36, 0)
drum.buf.mul(36, 1)
# snare
drum.buf.load('assets/sounds/drum/snare.wav', 38)
drum.buf.resample(0.5, 38)
drum.buf.amplify(0.8, 38)
drum.buf.mul(38, 1)
# ride
drum.buf.load('assets/sounds/drum/ride-bell.wav', 46)
drum.buf.resample(0.455, 46)
drum.buf.amplify(0.3, 46)

bass.sonic.from_json({
    "0": {
        "a": 0.01, "d": 0.01, "s": 1, "r": 0.01, "m": 1,
        "i0": 0, "i1": 0.4, "i2": 0.05, "i3": 0.06, "o": 1,
    },
    "1": {
        "a": 0.01, "d": 1e-06, "s": 1, "r": 0.01, "m": 1,
        "i0": 0, "i1": 0, "i2": 0.09, "i3": 0.07, "o": 0,
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
bass.lim.soft(0.1)
bass.lim.hard(0.25)

piano.sonic.from_json({
    "0": {
        "a": 4e-3, "d": 5e-5, "s": 0.2, "r": 2e-4, "m": 1,
        "i0": 0, "i1": 0.06, "i2": 0.02, "i3": 0, "o": 0.25,
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
piano.lfo.freq(12)
piano.lfo.amp(0.5)
piano.lfo.offset(1)

ghost.gain.set(0)
ghost.midman.directive([{'nibble': 0x90}], 0, 'midi', [0x90, '%1', 0])
ghost.lpf.set(0.9992)
ghost.lfo.freq(5)
ghost.lfo.amp(1 / 128)
ghost.oracle.mode('pitch_wheel')
ghost.oracle.m(0x4000)
ghost.oracle.format('midi', [0xe0, '%l', '%h'])
ghost.sonic.from_json({
    "0": {
        "a": 1e-3, "d": 5e-3, "s": 1, "r": 6e-5, "m": 1,
        "i0": 0, "i1": 0.15, "i2": 0, "i3": 0, "o": 0.95/2,
    },
    "1": {
        "a": 1, "d": 2e-5, "s": 0, "r": 1, "m": 1,
        "i0": 0, "i1": 0, "i2": 0, "i3": 0, "o": 0,
    },
    "2": {
        "a": 1e-5, "d": 3e-5, "s": 1, "r": 6e-5, "m": 1,
        "i0": 0, "i1": 0, "i2": 0, "i3": 0, "o": 0,
    },
    "3": {
        "a": 4e-6, "d": 1e-5, "s": 1, "r": 6e-5, "m": 2,
        "i0": 0, "i1": 0, "i2": 0, "i3": 0, "o": 0,
    },
})
ghost.sonic.midi(midi.Msg.pitch_bend_range(64))
ghost.lim.hard(0.25/2)
ghost.lim.soft(0.15/2)

bell.sonic.from_json({
    "0": {
        "a": 0.01, "d": 3e-5, "s": 0, "r": 3e-5, "m": 1,
        "i0": 0, "i1": 0.1, "i2": 0, "i3": 0, "o": 0.1,
    },
    "1": {
        "a": 0.01, "d": 3e-5, "s": 0, "r": 3e-5, "m": 2,
        "i0": 0, "i1": 0, "i2": 0, "i3": 0, "o": 0,
    },
    "2": {
        "a": 0.01, "d": 3e-5, "s": 0, "r": 3e-5, "m": 1,
        "i0": 0, "i1": 0, "i2": 0, "i3": 0.3, "o": 0.01,
    },
    "3": {
        "a": 0.01, "d": 3e-5, "s": 0, "r": 3e-5, "m": 4,
        "i0": 0, "i1": 0, "i2": 0, "i3": 0, "o": 0,
    },
})

goon.sonic.from_json({
    "0": {
        "a": 1e-3, "d": 5e-3, "s": 1, "r": 6e-5, "m": 1,
        "i0": 0, "i1": 0.15, "i2": 0, "i3": 0, "o": 0.3,
    },
    "1": {
        "a": 1, "d": 2e-5, "s": 0, "r": 1, "m": 1,
        "i0": 0, "i1": 0, "i2": 0, "i3": 0, "o": 0,
    },
    "2": {
        "a": 1e-5, "d": 3e-5, "s": 1, "r": 6e-5, "m": 1,
        "i0": 0, "i1": 0, "i2": 0, "i3": 0, "o": 0,
    },
    "3": {
        "a": 4e-6, "d": 1e-5, "s": 1, "r": 6e-5, "m": 2,
        "i0": 0, "i1": 0, "i2": 0, "i3": 0, "o": 0,
    },
})

# hat
hat.buf.load('assets/sounds/drum/hat.wav', 54)
hat.buf.resample(0.33, 54)
hat.buf.clip(0.24, 54)
hat.buf.amplify(0.6, 54)

# connect
piano.sonic.connect(piano.buf_2)
piano.lfo.connect(piano.buf_1)
piano.mul.connect(piano.buf_1)
piano.mul.connect(piano.buf_2)
bass.sonic.connect(bass.buf)
bass.lim.connect(bass.buf)
ghost.gain.connect(ghost.oracle)
ghost.rhymel.connect(ghost.sonic)
ghost.rhymel.connect(ghost.oracle)
ghost.lpf.connect(ghost.oracle)
ghost.lfo.connect(ghost.oracle)
ghost.oracle.connect(ghost.sonic)
ghost.sonic.connect(ghost.buf)
ghost.lim.connect(ghost.buf)
for i_voice, voice in enumerate(voices):
    for i in voice.input:
        liner.connect(i)
    for i in voice.output:
        i.connect(mixer[i_voice])
liner.connect(ghost.midman)
ghost.midman.connect(ghost.rhymel)
#ghost_lfo_i20.connect(ghost.sonic)
#ghost_lfo_i30.connect(ghost.sonic)
#ghost_lfo_i03.connect(ghost.sonic)
hat_osc.connect(hat_oracle)
hat_oracle.connect(liner)
mixer.lpf.connect(mixer.buf)
mixer.buf.connect(tape)
mixer.buf.connect(driver)

# setup
dlal.typical_setup(duration=216)
