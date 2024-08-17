import dlal
import midi

import argparse
import hashlib

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
        x = hashlib.sha256(name.encode()).digest()
        r1 = int.from_bytes(x[0:4], byteorder='big') / (1 << 32)
        r2 = int.from_bytes(x[4:8], byteorder='big') / (1 << 32)
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
                'pan_osc': ('osc', ['tri', 1/8]),
                'pan_oracle': ('oracle', [], {'m': 90, 'format': ('set', ['%', 10])})
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
            [],
            self.pan_osc,
            self.pan_oracle,
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
                "a": 1e-3, "d": 5e-3, "s": 1, "r": 6e-5, "m": 1 + (r1 - 0.5)/20,
                "i0": 0, "i1": 0.15 + r1/20, "i2": 0, "i3": 0, "o": 0.95/2,
            },
            "1": {
                "a": 1, "d": 2e-5, "s": 0, "r": 1, "m": 1 + (r2 - 0.5)/20,
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

class TalkingBassoon(dlal.subsystem.Subsystem):
    def init(self, name=None):
        dlal.subsystem.Subsystem.init(
            self,
            {
                'bassoon': ('buf', ['bassoon']),
                'talk': 'buf',
                'vocoder': 'vocoder',
                'gain': ('gain', [8]),
                'lim': ('lim', [1.0, 0.8, 0.1]),
                'buf': 'buf',
            },
            ['bassoon'],
            ['buf'],
            name=name,
        )
        dlal.connect(
            [self.bassoon, self.gain, self.lim],
            self.buf,
        )
        dlal.connect(
            self.talk,
            self.vocoder,
            self.buf,
        )
        self.talk.load('assets/local/bassindaface1.flac', 46)
        self.talk.load('assets/local/bassindaface2.flac', 49)
        self.talk.load('assets/local/funkyfunkybass.flac', 43)

class Choirist(dlal.subsystem.Subsystem):
    def init(self, phonetic_samples, name=None):
        self.phonetic_samples = phonetic_samples
        x = hashlib.sha256(name.encode()).digest()
        r1 = int.from_bytes(x[0:4], byteorder='big') / (1 << 32)
        r2 = int.from_bytes(x[4:8], byteorder='big') / (1 << 32)
        dlal.subsystem.Subsystem.init(
            self,
            {
                'midman': 'midman',
                'rhymel': 'rhymel',
                'lpf': ('lpf', [0.9992]),
                'lfo': ('lfo', [2 + 2 * r1, (1+r2)/128/16]),
                'oracle': 'oracle',
                'sonic': 'sonic',
                'vocoder': 'vocoder',
                'lim': ('lim', [0.25, 0.15]),
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
        dlal.connect(self.vocoder, self.buf)
        self.midman.directive([{'nibble': 0x90}], 0, 'midi', [0x90, '%1', 0])
        self.oracle.mode('pitch_wheel')
        self.oracle.m(0x4000)
        self.oracle.format('midi', [0xe0, '%l', '%h'])
        self.sonic.from_json({
            "0": {
                "a": 1e-4, "d": 0, "s": 1, "r": 1e-4, "m": 1,
                "i0": 0, "i1": 0.3, "i2": 0.2, "i3": 0.1, "o": 0.125,
            },
            "1": {
                "a": 1, "d": 0, "s": 1, "r": 1e-5, "m": 1,
                "i0": 0, "i1": 0, "i2": 0, "i3": 0, "o": 0,
            },
            "2": {
                "a": 1, "d": 0, "s": 1, "r": 1e-5, "m": 3,
                "i0": 0, "i1": 0, "i2": 0, "i3": 0, "o": 0,
            },
            "3": {
                "a": 1, "d": 0, "s": 1, "r": 1e-5, "m": 5,
                "i0": 0, "i1": 0, "i2": 0, "i3": 0, "o": 0,
            },
        })
        self.sonic.midi(midi.Msg.pitch_bend_range(64))

    def post_add_init(self):
        self.vocoder.freeze_with(self.phonetic_samples)

#===== init =====#
a_m = dlal.sound.read('assets/phonetics/a.flac').samples[44100:44100+64*1024]
a_f = dlal.sound.read('assets/phonetics/a.flac').samples[44100:44100+64*1024]

audio = dlal.Audio(driver=True, run_size=args.run_size)
liner = dlal.Liner('assets/midis/audiobro5.mid')

ghost1 = Ghost(name='ghost1')
ghost2 = Ghost(name='ghost2')
piano = Piano()
bass = dlal.Sonic(name='bass')
crow = dlal.Buf(name='crow')
drums = Drums()
talking_bassoon = TalkingBassoon()
bell = dlal.Addsyn().tubular_bells()
choir_s = Choirist(a_f, name='choir_s')
choir_a = Choirist(a_f, name='choir_a')
choir_t = Choirist(a_m, name='choir_t')
choir_b = Choirist(a_m, name='choir_b')

mixer = dlal.subsystem.Mixer(
    [
        {'gain':  1.4, 'pan': [   0, 10]},  # ghost1
        {'gain':  1.4, 'pan': [   0, 10]},  # ghost2
        {'gain':  1.4, 'pan': [   0, 10]},  # drums
        {'gain':  1.4, 'pan': [  45, 10]},  # crow
        {'gain':  1.4, 'pan': [   0, 10]},  # piano
        {'gain':  1.4, 'pan': [   0, 10]},  # bass
        {'gain': 11.2, 'pan': [   0, 10]},  # talking bassoon
        {'gain':  1.4, 'pan': [  45, 10]},  # bell
        {'gain':  1.4, 'pan': [   0, 10]},  # s
        {'gain':  1.4, 'pan': [  10, 10]},  # a
        {'gain':  1.4, 'pan': [ -20, 10]},  # t
        {'gain':  1.4, 'pan': [ -10, 10]},  # b
    ],
    reverb=0.3,
    lim=[1, 0.95, 0.1],
)
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
        self.duration = 0.2
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
        talking_bassoon,
        talking_bassoon.talk,
        bell,
        choir_s,
        choir_a,
        choir_t,
        choir_b,
    ],
)
dlal.connect(
    (
        ghost1,
        ghost2,
        drums,
        crow,
        piano,
        bass,
        talking_bassoon,
        bell,
        choir_s,
        choir_a,
        choir_t,
        choir_b,
    ),
    mixer,
    [audio, tape],
)
ghost1.pan_oracle.connect(mixer.channels[0].pan)
ghost2.pan_oracle.connect(mixer.channels[1].pan)

#===== start =====#
dlal.typical_setup(duration=240)
