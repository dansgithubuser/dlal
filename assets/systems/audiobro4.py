import dlal

import random
import sys

def sys_arg(i):
    if len(sys.argv) > i:
        return sys.argv[i]

class Violin(dlal.subsystem.Voices):
    def init(self, name):
        dlal.subsystem.Voices.init(
            self,
            name,
            ('osc', ['saw'], {'stay_on': True}),
            vol=0.5,
            randomize_phase=lambda osc: osc.phase(random.random()),
        )
        dlal.subsystem.Subsystem.init(
            self,
            None,
            {'adsr': ('adsr', [3e-5, 6e-6, 0.5, 3e-5])},
        )
        dlal.connect(
            self.midi,
            self.adsr,
            self.buf,
        )
        components = self.components
        self.components = {
            k: v for
            k, v in components.items()
            if k not in ['adsr', 'buf']
        }
        self.components['adsr'] = components['adsr']
        self.components['buf'] = components['buf']

#===== init =====#
audio = dlal.Audio(driver=True)
comm = dlal.Comm()

violin1 = Violin('violin1')
violin2 = Violin('violin2')
violin3 = Violin('violin3')
cello = Violin('cello')
bass = Violin('bass')
harp1 = dlal.Digitar(lowness=0.2, name='harp1'); harp1_mgain = dlal.Mgain(0.5)
harp2 = dlal.Digitar(lowness=0.2, name='harp2'); harp2_mgain = dlal.Mgain(0.5)

liner = dlal.Liner()
lpf1 = dlal.Lpf(freq=200)
lpf2 = dlal.Lpf(freq=800)
delay = dlal.Delay(10000, gain_y=0.2)
reverb = dlal.Reverb(0.4)
lim = dlal.Lim(1, 0.5, 0.3)
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
        [harp1_mgain, '>', harp1],
        [harp2_mgain, '>', harp2],
    ],
    [buf,
        '<+', harp1,
        '<+', harp2,
        '<+', lpf1,
        '<+', lpf2,
        '<+', delay,
        '<+', reverb,
        '<+', lim,
    ],
    [audio, tape],
)

#===== start =====#
dlal.typical_setup()
