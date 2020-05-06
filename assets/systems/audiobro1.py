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
comm = dlal.Comm()
Voice('drum', 'buf')
Voice('piano', 'sonic')
Voice('bass', 'sonic', 'lim', 'buf')
Voice('ghost', 'gain', 'rhymel', 'lpf', 'lfo', 'oracle', 'sonic', input=['rhymel'])
Lforacle('ghost_lfo_i20', 0.40000, 0.3, 0.3, 'i2', 0, '%')
Lforacle('ghost_lfo_i30', 0.31221, 0.1, 0.1, 'i3', 0, '%')
Lforacle('ghost_lfo_i03', 0.12219, 0.1, 0.1, 'i0', 3, '%')
Voice('bell', 'sonic')
Voice('goon', 'sonic')
Voice('hat', 'buf')
hat_osc = dlal.Osc(wave='noise', freq='0.12141')
hat_oracle = dlal.Oracle(m=0.04, b=0.01, format=('offset', 6, '%'))
liner = dlal.Liner()
lpf = dlal.Lpf()
reverb = dlal.Reverb()
buf = dlal.Buf()
tape = dlal.Tape(1 << 17)
gain = dlal.Gain()

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
driver.add(lpf)
driver.add(reverb)
driver.add(buf)
driver.add(tape)
driver.add(gain)

# commands
liner.load('assets/midis/audiobro1.mid', immediate=True)
liner.advance(sys_arg(1, float, 0))

# cricket
drum.buf.load('assets/sounds/animal/cricket.wav', 56)
drum.buf.amplify(1.5, 56)
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
# snare
drum.buf.load('assets/sounds/drum/snare.wav', 38)
drum.buf.resample(0.5, 38)
drum.buf.amplify(0.8, 38)
# ride
drum.buf.load('assets/sounds/drum/ride-bell.wav', 46)
drum.buf.resample(0.465, 53)
drum.buf.amplify(0.3, 53)

bass.sonic.from_json({
    "0": {
        "a": "0.01", "d": "0.01", "s": "1", "r": "0.01", "m": "1",
        "i0": "0", "i1": "0.4", "i2": "0.05", "i3": "0.06", "o": "1",
    },
    "1": {
        "a": "0.01", "d": "1e-06", "s": "1", "r": "0.01", "m": "1",
        "i0": "0", "i1": "0", "i2": "0.09", "i3": "0.07", "o": "0",
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
bass.lim.soft(0.1)
bass.lim.hard(0.25)

piano.sonic.from_json({
    "0": {
        "a": "4e-3", "d": "1e-4", "s": "0", "r": "2e-4", "m": "1",
        "i0": "0", "i1": "0.06", "i2": "0", "i3": "0", "o": "0.25",
    },
    "1": {
        "a": "0.025", "d": "6e-5", "s": "0.2", "r": "3e-5", "m": "1",
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

ghost.gain.set(0)
ghost.lpf.set(0.9992)
ghost.lfo.freq(5)
ghost.lfo.amp(1 / 128)
ghost.oracle.mode('pitch_wheel')
ghost.oracle.m(0x4000)
ghost.oracle.format('midi', [0xe0, '%l', '%h'])
ghost.sonic.from_json({
    "0": {
        "a": "7e-4", "d": "5e-3", "s": "1", "r": "6e-5", "m": "1",
        "i0": "0", "i1": "0", "i2": "1", "i3": "1", "o": "0.05",
    },
    "1": {
        "a": "7e-6", "d": "2e-3", "s": "1", "r": "6e-5", "m": "4",
        "i0": "0", "i1": "0", "i2": "0", "i3": "0", "o": "0.125",
    },
    "2": {
        "a": "1e-5", "d": "3e-5", "s": "1", "r": "6e-5", "m": "1",
        "i0": "0", "i1": "0", "i2": "0", "i3": "0", "o": "0.125",
    },
    "3": {
        "a": "4e-6", "d": "1e-5", "s": "1", "r": "6e-5", "m": "2",
        "i0": "0", "i1": "0", "i2": "0", "i3": "0", "o": "0.125",
    },
})
ghost.sonic.midi(midi.msg.pitch_bend_range(64))

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
        "a": "1e-2", "d": "1e-3", "s": "0.1", "r": "3e-4", "m": "2",
        "i0": "0.1", "i1": "0.1", "i2": "0", "i3": "0", "o": "0.25",
    },
    "1": {
        "a": "3e-4", "d": "1e-3", "s": "0.4", "r": "3e-4", "m": "1",
        "i0": "0.1", "i1": "0.1", "i2": "0", "i3": "0", "o": "0.25",
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

# hat
hat.buf.load('assets/sounds/drum/hat.wav', 42)
hat.buf.resample(0.4, 42)
hat.buf.amplify(0.6, 42)

lpf.set(0.9)
reverb.set(1)
gain.set(0)

# connect
bass.sonic.connect(bass.buf)
bass.lim.connect(bass.buf)
ghost.gain.connect(ghost.oracle)
ghost.rhymel.connect(ghost.sonic)
ghost.rhymel.connect(ghost.oracle)
ghost.lpf.connect(ghost.oracle)
ghost.lfo.connect(ghost.oracle)
ghost.oracle.connect(ghost.sonic)
for voice in voices:
    for i in voice.input:
        liner.connect(i)
    for i in voice.output:
        i.connect(buf)
ghost_lfo_i20.connect(ghost.sonic)
ghost_lfo_i30.connect(ghost.sonic)
ghost_lfo_i03.connect(ghost.sonic)
hat_osc.connect(hat_oracle)
hat_oracle.connect(liner)
lpf.connect(buf)
reverb.connect(buf)
buf.connect(tape)
gain.connect(buf)
buf.connect(driver)

# setup
end = sys_arg(2, float)
if end:
    duration = end - sys_arg(1, float, 0)
    runs = int(duration * 44100 / 64)
    with open('audiobro1.raw', 'wb') as file:
        for i in range(runs):
            driver.run()
            if i % (1 << 8) == 0xff:
                tape.to_file_i16le(1 << 14, file)
else:
    dlal.typical_setup()
