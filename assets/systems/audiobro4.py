import dlal

import random
import sys

def sys_arg(i):
    if len(sys.argv) > i:
        return sys.argv[i]

class Violin(dlal.subsystem.Voices):
    def init(self, name, vol=0):
        dlal.subsystem.Voices.init(
            self,
            ('osc', ['saw'], {'stay_on': True}),
            vol=0.5,
            randomize_phase=lambda osc: osc.phase(random.random()),
            name=name,
        )
        dlal.subsystem.Subsystem.init(
            self,
            {
                'adsr': ('adsr', [3e-5, 1e-5, 0.5, 5e-5]),
                'lim': ('lim', [0.25, 0.2]),
            },
            name=None,
        )
        dlal.connect(
            self.midi,
            self.adsr,
            [self.buf, '<+', self.lim],
        )
        components = self.components
        self.components = {
            k: v for
            k, v in components.items()
            if k not in ['adsr', 'lim', 'buf']
        }
        self.components['adsr'] = components['adsr']
        self.components['lim'] = components['lim']
        self.components['buf'] = components['buf']

class Harp(dlal.subsystem.Subsystem):
    def init(self, name):
        dlal.subsystem.Subsystem.init(
            self,
            {
                'mgain': ('mgain', [0.05]),
                'digitar': ('digitar', [0.3, 0.998]),
                'lim': ('lim', [0.25, 0.2]),
                'buf': 'buf',
            },
            ['mgain'],
            ['buf'],
            name=name,
        )
        dlal.connect(
            self.mgain,
            self.digitar,
            [self.buf, '<+', self.lim],
        )
        self.digitar.stay_on(True)

#===== init =====#
audio = dlal.Audio(driver=True)
comm = dlal.Comm()
liner = dlal.Liner()

violin1 = Violin('violin1')
violin2 = Violin('violin2')
violin3 = Violin('violin3')
cello = Violin('cello')
bass = Violin('bass')
harp1 = Harp('harp1')
harp2 = Harp('harp2')

lpf1 = dlal.Lpf(freq=200)
bow_buf = dlal.Buf(name='bow_buf')

lpf2 = dlal.Lpf(freq=800)
delay1 = dlal.Delay(15000, gain_y=0.4)
delay2 = dlal.Delay(21000, gain_y=0.2)
reverb = dlal.Reverb(0.8)
lim = dlal.Lim(1, 0.9, 0.3)
buf = dlal.Buf()
tape = dlal.Tape(1 << 17)

#===== commands =====#
#----- liner -----#
liner.load('assets/midis/audiobro4.mid', immediate=True)
liner.advance(float(sys_arg(1) or 0))

#===== connect =====#
dlal.connect(
    liner,
    [
        violin1,
        violin2,
        violin3,
        cello,
        bass,
        [harp1, '>', buf],
        [harp2, '>', buf],
    ],
    [bow_buf,
        '<+', lpf1,
    ],
    [buf,
        '<+', lpf2,
        '<+', delay1,
        '<+', delay2,
        '<+', reverb,
        '<+', lim,
    ],
    [audio, tape],
)

#===== start =====#
dlal.typical_setup()
