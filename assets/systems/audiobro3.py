import dlal

import midi

import sys

def sys_arg(i):
    if len(sys.argv) > i:
        return sys.argv[i]

#===== init =====#
audio = dlal.Audio(driver=True)
comm = dlal.Comm()

bassoon1 = dlal.Sonic('bassoon', name='bassoon1')
bassoon2 = dlal.Sonic('bassoon', name='bassoon2')
accordion1 = dlal.Sonic('magic_bread', name='accordion1')
accordion2 = dlal.Sonic('magic_bread', name='accordion2')
drum = dlal.Buf(name='drum')
voice = dlal.Sonic('cello', name='voice')
guitar = dlal.Sonic('harp', name='guitar')
shaker1 = dlal.Buf(name='shaker1')
shaker2 = dlal.Buf(name='shaker2')

liner = dlal.Liner()
buf = dlal.Buf()
tape = dlal.Tape(1 << 17)

#===== commands =====#
#----- drum -----#
# bass
drum.load('assets/sounds/drum/bass.wav', 35)
drum.crop(0, 0.2, 35)
drum.load('assets/sounds/drum/bass.wav', 36)
drum.crop(0, 0.2, 36)
# snare
drum.load('assets/sounds/drum/snare.wav', 38)
# hat
drum.load('assets/sounds/drum/hat.wav', 42)
# snare
drum.load('assets/sounds/drum/crash.wav', 57)
# side stick
drum.load('assets/sounds/drum/side-stick.wav', 37)
drum.resample(1.5, 37)
drum.amplify(2, 37)
drum.crop(0, 0.07, 37)
# ride bell
drum.load('assets/sounds/drum/ride-bell.wav', 55)

#----- shaker1 -----#
shaker1.load('assets/sounds/drum/shaker1.wav', 82)

#----- shaker2 -----#
shaker2.load('assets/sounds/drum/shaker2.wav', 82)
shaker2.amplify(0.5, 82)

#----- liner -----#
liner.load('assets/midis/audiobro3.mid', immediate=True)
liner.advance(float(sys_arg(1) or 0))

#===== connect =====#
dlal.connect(
    liner,
    [
        bassoon1,
        bassoon2,
        accordion1,
        accordion2,
        drum,
        voice,
        guitar,
        shaker1,
        shaker2,
    ],
    buf,
    [audio, tape],
)

#===== start =====#
dlal.typical_setup()
