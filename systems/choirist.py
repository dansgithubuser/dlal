import dlal
import midi

class Choirist(dlal.subsystem.Subsystem):
    def init(self, name=None):
        dlal.subsystem.Subsystem.init(
            self,
            {
                'midman': 'midman',
                'rhymel': 'rhymel',
                'lpf': ('lpf', [0.9992]),
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
            [self.oracle, '<+', self.lpf],
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
        self.vocoder.freeze_with(dlal.sound.read('assets/phonetics/a.flac').samples[44100:44100+64*1024])

audio = dlal.Audio(driver=True)
midi_ = dlal.Midi()
choirist = Choirist()

dlal.connect(
    midi_,
    choirist,
    audio,
)

dlal.typical_setup()
