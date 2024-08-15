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
            per_voice_init=lambda osc, i: osc.phase(random.random()),
            name=name,
        )
        dlal.subsystem.Subsystem.init(
            self,
            {
                'adsr': ('adsr', [3e-5, 1e-5, 0.5, 5e-5]),
                'lim': ('lim', [0.5, 0.4]),
                'lpf': ('lpf', [], {'freq': 200}),
            },
            name=None,
        )
        dlal.connect(
            self.midi,
            self.adsr,
            [self.buf,
                '<+', self.lim,
                '<+', self.lpf],
        )
        components = self.components
        self.components = {
            k: v for
            k, v in components.items()
            if k not in ['adsr', 'lim', 'lpf', 'buf']
        }
        self.components['adsr'] = components['adsr']
        self.components['lim'] = components['lim']
        self.components['lpf'] = components['lpf']
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

mixer = dlal.subsystem.Mixer(
    [
        {'gain': 1.4, 'pan': [   0, 10]},  # violin1
        {'gain': 1.4, 'pan': [ -10, 10]},  # violin2
        {'gain': 1.4, 'pan': [ -20, 10]},  # violin3
        {'gain': 1.4, 'pan': [  15, 10]},  # cello
        {'gain': 1.4, 'pan': [   0, 10]},  # bass
        {'gain': 1.4, 'pan': [  30, 10]},  # harp1
        {'gain': 1.4, 'pan': [ -30, 10]},  # harp2
    ],
    post_mix_extra={
        'lpf': ('lpf', [], {'freq': 800}),
        'hpf': ('hpf', [], {'freq': 40}),
        'delay1': ('delay', [15000], {'gain_y': 0.2}),
        'delay2': ('delay', [21000], {'gain_y': 0.1}),
    },
    reverb=0.6,
    lim=[1, 0.9, 0.3],
)
tape = dlal.Tape(1 << 17)

#===== commands =====#
#----- liner -----#
liner.load('assets/midis/audiobro4.mid', immediate=True)
if args.start:
    liner.advance(args.start)

#===== connect =====#
dlal.connect(
    liner,
    (
        violin1,
        violin2,
        violin3,
        cello,
        bass,
        harp1,
        harp2,
    ),
    mixer,
    [audio, tape],
)
dlal.connect(
    [mixer.lpf, mixer.hpf, mixer.delay1, mixer.delay2],
    mixer.buf,
)

#===== start =====#
dlal.typical_setup(duration=296)
