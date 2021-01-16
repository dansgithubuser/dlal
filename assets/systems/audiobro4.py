import dlal

import random
import sys

def sys_arg(i):
    if len(sys.argv) > i:
        return sys.argv[i]

def violin(name, n=7):
    return dlal.subsystem.Voices(
        name,
        ('osc', ['saw']),
        n=n,
        vol=0.2,
        randomize_phase=lambda osc: osc.phase(random.random()),
    )

#===== init =====#
audio = dlal.Audio(driver=True)
comm = dlal.Comm()

violin1 = violin('violin1', n=3)
violin2 = violin('violin2', n=3)
violin3 = violin('violin3', n=3)
cello = violin('cello', n=3)
bass = violin('bass', n=3)
harp1 = dlal.Sonic('harp', name='harp1')
harp2 = dlal.Sonic('harp', name='harp2')

liner = dlal.Liner()
lpf1 = dlal.Lpf(freq=200)
lpf2 = dlal.Lpf(freq=800)
reverb = dlal.Reverb(0.1)
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
        harp1,
        harp2,
    ],
    [buf,
        '<+', lpf1,
        '<+', lpf2,
        '<+', reverb,
        '<+', lim,
    ],
    [audio, tape],
)

#===== start =====#
dlal.typical_setup()
