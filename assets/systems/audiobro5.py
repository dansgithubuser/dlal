import dlal
import midi

import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--start', '-s', type=float)
parser.add_argument('--run-size', type=int)
args = parser.parse_args()

class Piano(dlal.subsystem.Voices):
    def init(self, name=None):
        super().init(
            ('digitar', [], {'lowness': 0.1, 'feedback': 0.9999, 'release': 0.2}),
            cents=0.3,
            vol=0.5,
            per_voice_init=lambda voice, i: voice.hammer(offset=1 + (3 + i) / 10),
            effects={
                'lim': ('lim', [0.9, 0.8, 0.2]),
            },
            name=name,
        )

class Drums(dlal.subsystem.Subsystem):
    def init(self, name=None):
        dlal.subsystem.Subsystem.init(
            self,
            {
                'drums': 'buf',
                'lim': ('lim', [1.0, 0.9, 0.1]),
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

class Ghost(dlal.subsystem.Subsystem):
    def init(self, name=None):
        dlal.subsystem.Subsystem.init(
            self,
            {
                'midman': 'midman',
                'rhymel': 'rhymel',
                'lpf': 'lpf',
                'lfo': 'lfo',
                'oracle': 'oracle',
                'sonic': 'sonic',
                'lim': 'lim',
                'buf': 'buf',
            },
            ['rhymel'],
            ['buf'],
            name=name,
        )
        dlal.connect(
            self.midman,
            [self.rhymel, '+>', self.sonic],
            [self.oracle, '<+', self.lpf, '<+', self.lfo],
            self.sonic,
            [self.buf, '<+', self.lim],
        )
        self.midman.directive([{'nibble': 0x90}], 0, 'midi', [0x90, '%1', 0])
        self.lpf.set(0.9992)
        self.lfo.freq(5)
        self.lfo.amp(1 / 128)
        self.oracle.mode('pitch_wheel')
        self.oracle.m(0x4000)
        self.oracle.format('midi', [0xe0, '%l', '%h'])
        self.sonic.from_json({
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
        self.sonic.midi(midi.Msg.pitch_bend_range(64))
        self.lim.hard(0.25/2)
        self.lim.soft(0.15/2)

#===== init =====#
audio = dlal.Audio(driver=True, run_size=args.run_size)
liner = dlal.Liner('assets/midis/audiobro5.mid')

ghost1 = Ghost(name='ghost1')
ghost2 = Ghost(name='ghost2')
piano = Piano()
bass = dlal.Sonic(name='bass')
crow = dlal.Buf(name='crow')
drums = Drums()

reverb = dlal.Reverb(0.3)
lim = dlal.Lim(hard=1, soft=0.95, soft_gain=0.1)
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

#----- drums -----#
drums.drums.load_drums()
drums.drums.load('assets/sounds/drum/kick.wav', dlal.Buf.Drum.bass)
drums.drums.amplify(1.5)
drums.drums.amplify(0.5, dlal.Buf.Drum.mute_cuica)
drums.drums.amplify(0.5, dlal.Buf.Drum.open_cuica)

# burgers ride
drums.drums.resample(0.455, dlal.Buf.Drum.ride_bell)
drums.drums.amplify(0.3, dlal.Buf.Drum.ride_bell)

# math kick
class Kick(dlal.maths.Generator):
    def init(self):
        self.duration = 0.25
        self.phase = self.Phase()
        self.phase2 = self.Phase()

    def amp(self, t):
        if t > self.duration: return
        self.phase += self.ramp(120, 0, t / self.duration)
        self.phase2 += 60
        return 0.5 * self.sqr(self.phase) * self.ramp(1, 0, t / self.duration) * self.sin(self.phase2)

drums.drums.set(
    Kick(audio.sample_rate()).generate(),
    dlal.Buf.Drum.bass_1,
)

#----- crow -----#
crow.load_asset('animal/crow.wav', 78)

#===== connect =====#
dlal.connect(
    liner,
    [
        ghost1,
        ghost2,
        drums,
        crow,
        piano,
        piano,
        bass,
        drums,
        drums,
        drums,
    ],
)
dlal.connect(
    [
        ghost1,
        ghost2,
        drums,
        crow,
        piano,
        bass,
    ],
    [buf,
        '<+', lim,
        '<+', reverb,
    ],
    [audio, tape],
)

#===== start =====#
print(dlal.system_diagram())
for i in audio.addee_order(): print(i)
print()
dlal.typical_setup(duration=180)
