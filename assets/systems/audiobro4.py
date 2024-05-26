import dlal

import argparse
import random
import sys

parser = argparse.ArgumentParser()
parser.add_argument('--start', '-s', type=float)
parser.add_argument('--run-size', type=int)
args = parser.parse_args()

class Violin(dlal.subsystem.Voices):
    def init(self, name, vol=0):
        dlal.subsystem.Voices.init(
            self,
            ('osc', ['saw'], {'stay_on': True}),
            vol=1.0,
            randomize_phase=lambda osc: osc.phase(random.random()),
            name=name,
        )
        dlal.subsystem.Subsystem.init(
            self,
            {
                'adsr': ('adsr', [3e-5, 1e-5, 0.5, 5e-5]),
                'lim': ('lim', [0.5, 0.4]),
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
                'mgain': ('mgain', [0.2]),
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
audio = dlal.Audio(driver=True, run_size=args.run_size)
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
hpf = dlal.Hpf(freq=40)
delay1 = dlal.Delay(15000, gain_y=0.2)
delay2 = dlal.Delay(21000, gain_y=0.1)
reverb = dlal.Reverb(0.6)
lim = dlal.Lim(1, 0.9, 0.3)
buf = dlal.Buf()
tape = dlal.Tape(1 << 17)

#===== commands =====#
#----- liner -----#
liner.load('assets/midis/audiobro4.mid', immediate=True)
if args.start:
    liner.advance(args.start)

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
        '<+', hpf,
        '<+', delay1,
        '<+', delay2,
        '<+', reverb,
        '<+', lim,
    ],
    [audio, tape],
)

#===== start =====#
dlal.typical_setup(duration=296)
