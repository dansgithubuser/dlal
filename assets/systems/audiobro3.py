import dlal

import midi

import argparse
import datetime
import os
import subprocess
import sys

parser = argparse.ArgumentParser()
parser.add_argument('--live', '-l', action='store_true')
parser.add_argument('--start', '-s')
parser.add_argument('--run-size', type=int)
args = parser.parse_args()

#===== init =====#
if os.path.exists('assets/local/audiobro3_voice.flac'):
    created_at = datetime.datetime.fromtimestamp(os.stat('assets/local/audiobro3_voice.flac').st_ctime)
    print(f'using voice from {created_at.isoformat()}')
else:
    print('no voice, rendering')
    import audiobro3_voice
    print('voice rendered, exiting (run me again)')
    sys.exit()

audio = dlal.Audio(driver=True)
if args.run_size: audio.run_size(args.run_size)
comm = dlal.Comm()

# bassoons
bassoon1 = dlal.Buf('bassoon', name='bassoon1')
bassoon2 = dlal.Buf('bassoon', name='bassoon2')
# accordion
accordion1 = dlal.Buf('melodica', name='accordion1')
accordion2 = dlal.Buf('melodica', name='accordion2')
# drum
drum = dlal.Buf(name='drum')
# voice
voice = dlal.Afr('assets/local/audiobro3_voice.flac')
voice_gain = dlal.Gain(1.5)
voice_buf = dlal.Buf()
# guitar
guitar_strummer = dlal.Strummer(name='guitar_strummer')
guitar = dlal.Buf('guitar', name='guitar')
# shaker
shaker1 = dlal.Buf(name='shaker1')
shaker2 = dlal.Buf(name='shaker2')

liner = dlal.Liner()
reverb = dlal.Reverb(0.2)
master_gain = dlal.Gain(2.0)
lim = dlal.Lim(1, 0.9, 0.3)
buf = dlal.Buf()
tape = dlal.Tape(1 << 17)

#===== commands =====#
#----- bassoons -----#
bassoon1.repeat()
bassoon2.repeat()
bassoon1.normalize(0.15)
bassoon2.normalize(0.15)

#----- accordion -----#
accordion1.repeat()
accordion2.repeat()
accordion1.normalize(0.05)
accordion2.normalize(0.05)

#----- drum -----#
# bass
drum.load('assets/sounds/drum/bass.wav', 35)
drum.crop(0, 0.2, 35)
drum.amplify(0.5, 35)
drum.load('assets/sounds/drum/bass.wav', 36)
drum.crop(0, 0.2, 36)
drum.amplify(0.5, 36)
# snare
drum.load('assets/sounds/drum/snare.wav', 38)
drum.clip(0.5, 38)
drum.amplify(0.5, 38)
# hat
drum.load('assets/sounds/drum/hat.wav', 42)
drum.amplify(0.25, 42)
# crash
drum.load('assets/sounds/drum/crash.wav', 57)
drum.amplify(0.5, 57)
# side stick
drum.load('assets/sounds/drum/side-stick.wav', 37)
drum.resample(1.5, 37)
drum.amplify(2, 37)
drum.crop(0, 0.07, 37)
drum.amplify(0.5, 37)
# ride bell
drum.load('assets/sounds/drum/ride-bell.wav', 55)
drum.amplify(0.5, 55)

#----- guitar -----#
guitar_strummer.pattern(
    'd u udu u ududu'
    'd u udu u ududu'
    'd u udu u ududu'
    'd u udu u udd'
)
guitar.normalize(0.15)

#----- shakers -----#
shaker1.load('assets/sounds/drum/shaker1.wav', 82)
shaker1.amplify(0.5, 82)

shaker2.load('assets/sounds/drum/shaker2.wav', 82)
shaker2.amplify(0.25, 82)

#----- liner -----#
liner.load('assets/midis/audiobro3.mid', immediate=True)
if args.start:
    liner.advance(float(args.start))

#===== connect =====#
voice_gain.connect(voice_buf)
master_gain.connect(buf)
dlal.connect(
    liner,
    [
        bassoon1,
        bassoon2,
        accordion1,
        accordion2,
        drum,
        [voice, '>', voice_buf],
        [guitar_strummer, '>', guitar],
        shaker1,
        shaker2,
    ],
    [buf,
        '<+', guitar,
        '<+', reverb,
        '<+', lim,
        '<+', voice_buf,
    ],
    [audio, tape],
)

#===== start =====#
dlal.typical_setup(duration=240)
